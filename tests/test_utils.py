# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2018 Mike Bonnet <mikeb@redhat.com>

from unittest.mock import patch
from repotracker import utils
import json

def test_load_config(tmpdir):
    """
    Test that the config can be loaded.
    """
    conf = tmpdir.join('conf')
    conf.write("""[broker]
    urls = amqps://broker01.example.com
    cert = /cert
    key = /key
    cacerts = /cacerts
    topic_prefix = container

    [example]
    type = container
    repo = example.com/repos/testrepo
    """)
    result = utils.load_config(str(conf))
    assert result.has_section('broker')
    assert result['broker']['urls'] == 'amqps://broker01.example.com'
    assert result['broker']['cert'] == '/cert'
    assert result['broker']['key'] == '/key'
    assert result['broker']['cacerts'] == '/cacerts'
    assert result['broker']['topic_prefix'] == 'container'
    assert result.has_section('example')
    assert result['example']['type'] == 'container'
    assert result['example']['repo'] == 'example.com/repos/testrepo'


def test_load_data_missing(tmpdir):
    """
    Test that a missing or empty data file does not cause an error.
    """
    data = tmpdir.join('data')
    assert data.check() == False
    result = utils.load_data(str(data))
    assert result == {}
    data.ensure()
    assert data.check()
    assert data.size() == 0
    result = utils.load_data(str(data))
    assert result == {}
    

def test_load_data(tmpdir):
    """
    Test that historical data can be loaded.
    """
    data = tmpdir.join('data')
    expected = {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': 'abc123',
                'old_digest': None,
                'created': '2018-10-28T00:07:23.904635308Z',
                'labels': {
                    'foo': 'bar',
                },
                'os': 'linux',
                'arch': 'x86_64',
            },
        }
    }
    data.write(json.dumps(expected))
    result = utils.load_data(str(data))
    assert expected == result


def test_save_data(tmpdir):
    """
    Test that historical data can be saved.
    """
    data = tmpdir.join('data')
    expected = {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': 'abc123',
                'old_digest': None,
                'created': '2018-10-28T00:07:23.904635308Z',
                'labels': {
                    'foo': 'bar',
                },
                'os': 'linux',
                'arch': 'x86_64',
            },
        }
    }
    utils.save_data(str(data), expected)
    assert json.dumps(expected) == data.read()
