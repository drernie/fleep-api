#! /usr/bin/env python3

"""Dump Fleep chat history into JSON file.

Input - YAML file ~/.fleep.yml

fleep-client:
  version: 1.0
  login:
    username: user@fleep.io
    password: xxxx

Output: history.json

"""

import sys
import os.path
import subprocess
import time
import logging
import re
import hashlib
import hmac
import stat
import json
import socket
import yaml

from fleepclient.api import FleepApi
from fleepclient.cache import FleepCache

SERVER = 'https://fleep.io'
CONFIG_FILE = "~/.fleep.yml"

def load_config():
    global USERNAME, PASSWORD
    cf_path = os.path.expanduser(CONFIG_FILE)
    print(cf_path)
    with open(cf_path, 'r') as file:
        cf = yaml.safe_load(file)
        print(cf)
    if not cf["login"]:
        print(f'Please create {CONFIG_FILE} with username and password.')
        sys.exit(1)
    return cf["login"]

def json_encode_stable(data = None, **kwargs):
    """JSON with sorted keys, needed for tests.
    """
    data = data or kwargs
    e = json.JSONEncoder(sort_keys=True, indent=2)
    return e.encode(data)

def main():
    c = load_config()

    print('Login')
    fc = FleepCache(SERVER, c["username"], c["password"])
    print('Loading contacts')
    fc.contacts.sync_all()
    print('Loading conversations')
    for conv_id in fc.conversations:
        conv = fc.conversations[conv_id]
        print('  %s - %s' % (conv_id, conv.topic))
        conv.sync_to_first()
    data = {
        'account': {
            'account_id': fc.account['account_id'],
            'display_name': fc.account['display_name'],
        },
        'contacts': fc.contacts.contacts,
        'conversations': {},
    }
    for conv_id in fc.conversations:
        conv = fc.conversations[conv_id]
        cdata = {
            'topic': conv.topic,
            'members': conv.members,
            'messages': [],
        }
        mlist = conv.messages.keys()
        mlist.sort()
        for mnr in mlist:
            m = conv.messages[mnr]
            cdata['messages'].append(m.as_dict())
        data['conversations'][conv_id] = cdata

    fn = 'history.json'
    jsdata = json_encode_stable(data)
    with open(fn, 'w') as f:
        f.write(jsdata)
    print('Wrote', fn)

if __name__ == '__main__':
    main()
