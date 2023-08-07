# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2018 Mike Bonnet <mikeb@redhat.com>

from repotracker import utils
import json


def test_load_config(tmpdir):
    """
    Test that the config can be loaded.
    """
    conf = tmpdir.join("conf")
    conf.write(
        """[broker]
    urls = amqps://broker01.example.com
    cert = /cert
    key = /key
    cacerts = /cacerts
    topic_prefix = container

    [example]
    type = container
    repo = example.com/repos/testrepo
    """
    )
    result = utils.load_config(str(conf))
    assert result.has_section("broker")
    assert result["broker"]["urls"] == "amqps://broker01.example.com"
    assert result["broker"]["cert"] == "/cert"
    assert result["broker"]["key"] == "/key"
    assert result["broker"]["cacerts"] == "/cacerts"
    assert result["broker"]["topic_prefix"] == "container"
    assert result.has_section("example")
    assert result["example"]["type"] == "container"
    assert result["example"]["repo"] == "example.com/repos/testrepo"


def test_load_data_missing(tmpdir):
    """
    Test that a missing or empty data file does not cause an error.
    """
    data = tmpdir.join("data")
    assert data.check() is False
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
    data = tmpdir.join("data")
    expected = {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": "abc123",
                "old_digest": None,
                "created": "2018-10-28T00:07:23.904635308Z",
                "labels": {
                    "foo": "bar",
                },
                "os": "linux",
                "arch": "x86_64",
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
    data = tmpdir.join("data")
    expected = {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": "abc123",
                "old_digest": None,
                "created": "2018-10-28T00:07:23.904635308Z",
                "labels": {
                    "foo": "bar",
                },
                "os": "linux",
                "arch": "x86_64",
            },
        }
    }
    utils.save_data(str(data), expected)
    assert json.dumps(expected) == data.read()


def test_format_ts_int():
    """
    Test that format_ts() formats integer timestamps correctly.
    """
    assert utils.format_ts(1556038408) == "2019-04-23T16:53:28Z"


def test_format_ts_float():
    """
    Test that format_ts() formats float timestamps correctly.
    """
    assert utils.format_ts(1556038408.123) == "2019-04-23T16:53:28Z"


def test_format_time():
    """
    Test that format_time() formats datetime strings correctly.
    """
    assert utils.format_time("2019-04-23T16:41:13.304737955Z") == "2019-04-23T16:41:13Z"
    assert utils.format_time("2019-04-23T16:41:13.0Z") == "2019-04-23T16:41:13Z"
    assert utils.format_time("2019-04-23T16:41:13Z") == "2019-04-23T16:41:13Z"
    assert (
        utils.format_time("2019-04-23T16:41:13.304737955UTC")
        == "2019-04-23T16:41:13UTC"
    )
    assert utils.format_time("2019-04-23T16:41:13.0UTC") == "2019-04-23T16:41:13UTC"
    assert utils.format_time("2019-04-23T16:41:13UTC") == "2019-04-23T16:41:13UTC"
    assert utils.format_time("2019-04-23T16:41:13") == "2019-04-23T16:41:13"


def test_format_time_empty():
    """
    Test that format_time() handles empty values correctly.
    """
    assert utils.format_time(None) is None
    assert utils.format_time("") is None
