### action plugin: `set_ssh_keys`
Uses the `api` lookup plugin to list SSH keys registered to the user with the API key, delete keys not desired, and upload desired keys not already present.
```yml
required arguments:
  api_key: takes the form "consumer_key:consumer_token:secret"
  region_controller_url: 'example: "http://maas-region-controller:5240/MAAS/"'
  pubkeys: list of strings of the form "algorithm pubkey-base64 commments". no newlines.
```

### lookup plugin: `api`
Uses python `requests` library to query the MAAS REST API. See documentation: https://maas.io/docs/api
```yml
required arguments:
  api_key: takes the form "consumer_key:consumer_token:secret"
  region_controller_url: 'example: "http://maas-region-controller:5240/MAAS/"'
  http_method: get, post, delete, put
optional_arguments:
  data: dictionary with string keys and string values. in the docs, these parameters are titled "Request body (multipart/form-data)".
```

### examples

```yml
- name: print ssh keys
  ansible.builtin.debug:
    msg: "{{ lookup('unity.maas.api', http_method='get', url=maas_region_controller_url + '/api/2.0/account/prefs/sshkeys/', api_key=maas_api_key) | to_nice_yaml }}"
- name: overwrite list of keys
  unity.maas.set_ssh_keys:
    region_controller_url: "{{ maas_region_controller_url }}"
    api_key: "{{ maas_api_key }}"
    pubkeys: "{{ root_authorized_keys }}"
```
