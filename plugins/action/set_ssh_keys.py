import json
from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase


def _fmt_response(x):
    try:
        return json.dumps(x)
    except TypeError:
        return x.text


class ActionModule(ActionBase):

    def api_call(self, args: dict, task_vars=None):
        api_task = self._task.copy()
        api_task.args = args
        api_action = self._shared_loader_obj.action_loader.get(
            "unity.maas.api",
            task=api_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=self._templar,
            shared_loader_obj=self._shared_loader_obj,
        )
        api_action_result = api_action.run(task_vars=task_vars)
        if api_action_result["failed"]:
            raise AnsibleError(api_action_result)
        return api_action_result["response"]

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        required_args = ["api_key", "region_controller_url", "pubkeys"]
        for argname in required_args:
            if argname not in self._task.args:
                raise AnsibleError(f'required argument: "{argname}"')
        region_controller_url = self._task.args["region_controller_url"].rstrip("/")
        before_sshkeys_response = self.api_call(
            args={
                "http_method": "get",
                "url": f"{region_controller_url}/api/2.0/account/prefs/sshkeys/",
                "api_key": self._task.args["api_key"],
            },
        )
        before_pubkeys = sorted([x["key"] for x in before_sshkeys_response.json()])
        expected_pubkeys = sorted(self._task.args["pubkeys"])
        if before_pubkeys == expected_pubkeys:
            result["msg"] = "all keys already set"
            return result
        result["changed"] = True
        if self._play_context.check_mode:
            result["diff"] = {"before": before_pubkeys, "after": expected_pubkeys}
            return result
        diff = {"before": before_pubkeys}
        responses = []
        for before_pubkey_info in before_sshkeys_response.json():
            if before_pubkey_info["key"] not in expected_pubkeys:
                delete_response = self.api_call(
                    args={
                        "http_method": "delete",
                        "url": f"{region_controller_url}/api/2.0/account/prefs/sshkeys/{before_pubkey_info['id']}/",
                        "api_key": self._task.args["api_key"],
                    },
                    task_vars=task_vars,
                )
                responses.append(
                    {
                        "name": f"delete key {before_pubkey_info['id']}",
                        "response": _fmt_response(delete_response),
                    }
                )
        for expected_pubkey in expected_pubkeys:
            if expected_pubkey in before_pubkeys:
                continue
            add_key_response = self.api_call(
                args={
                    "http_method": "post",
                    "url": f"{region_controller_url}/api/2.0/account/prefs/sshkeys/",
                    "data": {"key": expected_pubkey},
                    "api_key": self._task.args["api_key"],
                },
                task_vars=task_vars,
            )
            responses.append(
                {
                    "name": f"add key {expected_pubkey}",
                    "response": _fmt_response(add_key_response),
                }
            )
        after_sshkeys_response = self.api_call(
            args={
                "http_method": "get",
                "url": f"{region_controller_url}/api/2.0/account/prefs/sshkeys/",
                "api_key": self._task.args["api_key"],
            },
        )
        diff["after"] = sorted([x["key"] for x in after_sshkeys_response.json()])
        # return a list of HTTP responses as a prepared diff along with the before/after comparison
        result["diff"] = [diff, {"prepared": json.dumps(responses, indent=4)}]
        return result
