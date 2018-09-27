# Utility functions for repotacker
# Mike Bonnet, 2018-09-27

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
    if os.path.exists(path):
        with open(path) as fobj:
            return json.load(fobj)
    else:
        return {}


def save_data(path, data):
    with tempfile.NamedTemporaryFile(dir=os.path.dirname(path), delete=False) as fobj:
        fobj.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    os.chmod(fobj.name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    os.replace(fobj.name, path)
