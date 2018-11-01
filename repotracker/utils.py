# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2018 Mike Bonnet <mikeb@redhat.com>
# Utility functions for repotacker

import configparser
import json
import tempfile
import os
import stat


def load_config(path):
    parser = configparser.ConfigParser()
    with open(path) as fobj:
        parser.read_file(fobj)
    return parser


def load_data(path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path) as fobj:
            return json.load(fobj)
    return {}


def save_data(path, data):
    with tempfile.NamedTemporaryFile(dir=os.path.dirname(path), delete=False) as fobj:
        fobj.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    os.chmod(fobj.name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    os.replace(fobj.name, path)
