import json
from oauthlib.oauth1 import SIGNATURE_PLAINTEXT
from requests_oauthlib import OAuth1Session
from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        required_args = ["api_key", "url", "http_method"]
        for argname in required_args:
            if argname not in kwargs:
                raise AnsibleError(f'required argument: "{argname}"')

        try:
            consumer_key, consumer_token, secret = kwargs["api_key"].split(":")
        except ValueError as e:
            raise AnsibleError(
                'Invalid format for "api_key". Expected "consumer_key:consumer_token:secret".'
            ) from e

        session = OAuth1Session(
            consumer_key,
            resource_owner_key=consumer_token,
            resource_owner_secret=secret,
            signature_method=SIGNATURE_PLAINTEXT,
        )

        http_method = kwargs["http_method"].lower()
        url = kwargs["url"]
        data = kwargs.get("data", {})

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

        response.raise_for_status()

        if response.text == "":
            return [None]
        try:
            return [response.json()]
        except json.JSONDecodeError as e:
            raise AnsibleError(
                f"API response was not empty string or JSON:\n{response.text}"
            ) from e
