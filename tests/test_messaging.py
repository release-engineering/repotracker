# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2018 Mike Bonnet <mikeb@redhat.com>

from unittest.mock import MagicMock, patch, call
producer_mock = MagicMock()
patch.dict('sys.modules', values={'rhmsg.activemq.producer': producer_mock}).start()
from repotracker import messaging
import json


DATA = {
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
CONF = {
    'broker': {
        'urls': 'amqps://broker01.example.com',
        'cert': '/cert',
        'key': '/key',
        'cacerts': '/cacerts',
        'topic_prefix': 'container',
    },
}


def test_gen_msg():
    """
    Test that gen_msg() produces the correct output.
    """
    data = DATA['example.com/repos/testrepo']['latest'].copy()
    result = messaging.gen_msg(data)
    expected_body = json.dumps(data)
    del data['labels']
    assert result == (data, expected_body)


@patch.dict(DATA['example.com/repos/testrepo'], ignore=True)
@patch.object(messaging, 'AMQProducer')
def test_send_container_updates_ignore(prod):
    """
    Test that no messages are sent when a repo is marked as ignored.
    """
    messaging.send_container_updates(CONF, DATA)
    prod.return_value.__enter__.return_value.send_msgs.assert_not_called()


@patch.dict(DATA['example.com/repos/testrepo']['latest'], action='unchanged')
@patch.object(messaging, 'AMQProducer')
def test_send_container_updates_unchanged(prod):
    """
    Test that no messages are sent when a tag is unchanged.
    """
    messaging.send_container_updates(CONF, DATA)
    prod.return_value.__enter__.return_value.send_msgs.assert_not_called()


@patch.object(messaging, 'AMQProducer')
def test_send_container_updates_added(prod):
    """
    Test that a message is sent when a tag is added.
    """
    messaging.send_container_updates(CONF, DATA)
    prod.return_value.__enter__.return_value.send_msgs.\
        assert_called_once_with([messaging.gen_msg(DATA['example.com/repos/testrepo']['latest'])])


@patch.dict(DATA['example.com/repos/testrepo']['latest'], action='updated', old_digest='def456')
@patch.object(messaging, 'AMQProducer')
def test_send_container_updates_updated(prod):
    """
    Test that a message is sent when a tag is updated.
    """
    messaging.send_container_updates(CONF, DATA)
    prod.return_value.__enter__.return_value.send_msgs.\
        assert_called_once_with([messaging.gen_msg(DATA['example.com/repos/testrepo']['latest'])])


@patch.object(messaging, 'AMQProducer')
def test_send_container_updates_removed(prod):
    """
    Test that a message is sent when a tag is removed.
    """
    data = {
        'action': 'removed',
        'repo': 'example.com/repos/testrepo',
        'reponame': 'testrepo',
        'tag': 'latest',
        'digest': None,
        'old_digest': 'abc123',
        'created': None,
        'labels': {},
        'os': None,
        'arch': None,
    }
    messaging.send_container_updates(CONF, {'e': {'latest': data}})
    prod.return_value.__enter__.return_value.send_msgs.\
        assert_called_once_with([messaging.gen_msg(data)])


@patch.object(messaging, 'AMQProducer')
def test_send_container_updates_all(prod):
    """
    Test that a sequence of messages is sent successfully.
    """
    added_msg = {
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
    }
    unchanged_msg = added_msg.copy()
    unchanged_msg['action'] = 'unchanged'
    updated_msg = added_msg.copy()
    updated_msg['action'] = 'updated'
    updated_msg['old_digest'] = updated_msg['digest']
    updated_msg['digest'] = 'def456'
    removed_msg = added_msg.copy()
    removed_msg['action'] = 'removed'
    removed_msg['old_digest'] = removed_msg['digest']
    removed_msg['digest'] = None
    removed_msg['labels'] = {}
    removed_msg['os'] = None
    removed_msg['arch'] = None
    data = {
        'repo1': {
            'tag1': added_msg,
            'tag2': unchanged_msg,
            'tag3': updated_msg,
            'tag4': removed_msg,
        },
        'repo2': {
            'tag1': removed_msg,
            'tag2': updated_msg,
            'tag3': unchanged_msg,
            'tag4': added_msg,
        },
    }
    messaging.send_container_updates(CONF, data)
    send_msgs = prod.return_value.__enter__.return_value.send_msgs
    assert send_msgs.call_count == 3
    calls = [
        call([messaging.gen_msg(added_msg), messaging.gen_msg(added_msg)]),
        call([messaging.gen_msg(updated_msg), messaging.gen_msg(updated_msg)]),
        call([messaging.gen_msg(removed_msg), messaging.gen_msg(removed_msg)]),
    ]
    send_msgs.assert_has_calls(calls)
