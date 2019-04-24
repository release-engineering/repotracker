# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2018 Mike Bonnet <mikeb@redhat.com>
# Utility functions for repotacker

import configparser
import json
import tempfile
import os
import stat
import datetime
import re


FRACTIONAL_SECONDS_RE = re.compile(r'\.\d+(\w*)$')


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


def format_ts(ts):
    """
    Format in integer timestamp into ISO format.
    Example: 2019-04-23T16:12:07Z
    """
    dobj = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
    return dobj.strftime('%Y-%m-%dT%H:%M:%SZ')


def format_time(timestr):
    """
    Format a datetime string in ISO format into a consistent and more parseable value.
    Example: 2019-04-23T16:12:07.762980555Z -> 2019-04-23T16:12:07Z
    """
    if not timestr:
        return None
    # Just trim off any fractional seconds.
    return FRACTIONAL_SECONDS_RE.sub(r'\1', timestr)
