import traceback
from oauthlib.oauth1 import SIGNATURE_PLAINTEXT
from requests_oauthlib import OAuth1Session
from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError
from requests.exceptions import HTTPError


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        result["failed"] = False

        required_args = ["api_key", "url", "http_method"]
        for argname in required_args:
            if argname not in self._task.args:
                raise AnsibleError(f'required argument: "{argname}"')

        try:
            consumer_key, consumer_token, secret = self._task.args["api_key"].split(":")
        except ValueError as e:
            raise AnsibleError(
                'Invalid format for "api_key". Expected "consumer_key:consumer_token:secret".'
            ) from e

        http_method = self._task.args["http_method"].lower()
        url = self._task.args["url"]
        data = self._task.args.get("data", {})

        if self._play_context.check_mode and http_method != "get":
            result["skipped"] = True
            return result

        session = OAuth1Session(
            consumer_key,
            resource_owner_key=consumer_token,
            resource_owner_secret=secret,
            signature_method=SIGNATURE_PLAINTEXT,
        )

        if http_method == "get":
            response = session.get(url, data=data)
        elif http_method == "post":
            response = session.post(url, data=data)
        elif http_method == "put":
            response = session.put(url, data=data)
        elif http_method == "delete":
            response = session.delete(url, data=data)
        else:
            raise AnsibleError(f'Unsupported HTTP method: "{http_method.upper()}"')

        try:
            response.raise_for_status()
        except HTTPError:
            result["failed"] = True
            result["msg"] = traceback.format_exc()
            return result

        result["response"] = response
        return result
