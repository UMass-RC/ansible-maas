import json
from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        required_args = ["api_key", "region_controller_url", "pubkeys"]
        for argname in required_args:
            if argname not in self._task.args:
                raise AnsibleError(f'required argument: "{argname}"')
        region_controller_url = self._task.args["region_controller_url"].rstrip("/")
        before_lookup = self._templar._lookup(
            "unity.maas.api",
            http_method="get",
            url=f"{region_controller_url}/api/2.0/account/prefs/sshkeys/",
            api_key=self._task.args["api_key"],
        )
        before_pubkeys = sorted([x["key"] for x in before_lookup])
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
        for before_pubkey_info in before_lookup:
            if before_pubkey_info["key"] not in expected_pubkeys:
                delete_response = self._templar._lookup(
                    "unity.maas.api",
                    http_method="delete",
                    url=f"{region_controller_url}/api/2.0/account/prefs/sshkeys/{before_pubkey_info['id']}/",
                    api_key=self._task.args["api_key"],
                )
                responses.append(
                    {"name": f"delete key {before_pubkey_info['id']}", "response": delete_response}
                )
        for expected_pubkey in expected_pubkeys:
            if expected_pubkey in before_pubkeys:
                continue
            add_key_response = self._templar._lookup(
                "unity.maas.api",
                http_method="post",
                url=f"{region_controller_url}/api/2.0/account/prefs/sshkeys/",
                data={"key": expected_pubkey},
                api_key=self._task.args["api_key"],
            )
            responses.append({"name": f"add key {expected_pubkey}", "response": add_key_response})
        after_lookup = self._templar._lookup(
            "unity.maas.api",
            http_method="get",
            url=f"{region_controller_url}/api/2.0/account/prefs/sshkeys/",
            api_key=self._task.args["api_key"],
        )
        diff["after"] = sorted([x["key"] for x in after_lookup])
        # return a list of HTTP responses as a prepared diff along with the before/after comparison
        result["diff"] = [diff, {"prepared": json.dumps(responses, indent=4)}]
        return result
