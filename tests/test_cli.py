# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2018 Mike Bonnet <mikeb@redhat.com>

from unittest.mock import patch, MagicMock
producer_mock = MagicMock()
patch.dict('sys.modules', values={'rhmsg.activemq.producer': producer_mock}).start()
from repotracker import cli
import pytest


@patch('sys.argv', new=['foo'])
def test_get_args_default():
    """
    Test that get_args() returns the expected default values.
    """
    args = cli.get_args()
    assert args.quiet == False
    assert args.verbose == False
    assert args.config == '/etc/repotracker/repotracker.ini'
    assert args.data == '/var/lib/repotracker/containers/repotracker-containers.json'


@patch('sys.argv', new=['foo', '-q', '-v', '-c', '/repotracker.ini', '-d', '/data.json'])
def test_get_args_all():
    """
    Test that get_args() respects all command-line options.
    """
    args = cli.get_args()
    assert args.quiet == True
    assert args.verbose == True
    assert args.config == '/repotracker.ini'
    assert args.data == '/data.json'


def test_main_default(tmpdir):
    """
    Test that the main() method works as expected with default args.
    """
    conf = tmpdir.join('conf')
    conf.write("""[broker]
    urls = amqps://broker01.example.com
    cert = /cert
    key = /key
    cacerts = /cacerts
    topic_prefix = container
    """)
    data = tmpdir.join('data')
    with patch('sys.argv', new=['foo', '-c', str(conf), '-d', str(data)]):
        cli.main()


def test_main_quiet_verbose(tmpdir):
    """
    Test that the main() method works as expected with quiet and verbose options.
    """
    conf = tmpdir.join('conf')
    conf.write("""[broker]
    urls = amqps://broker01.example.com
    cert = /cert
    key = /key
    cacerts = /cacerts
    topic_prefix = container
    """)
    data = tmpdir.join('data')
    with patch('sys.argv', new=['foo', '-c', str(conf), '-d', str(data), '-q', '-v']):
        cli.main()


@patch.object(cli.messaging, 'send_container_updates', side_effect=RuntimeError('could not send messages'))
def test_main_error(send_container_updates, tmpdir):
    """
    Test that the main() method works as expected when handling an error.
    """
    conf = tmpdir.join('conf')
    conf.write("""[broker]
    urls = amqps://broker01.example.com
    cert = /cert
    key = /key
    cacerts = /cacerts
    topic_prefix = container
    """)
    data = tmpdir.join('data')
    with patch('sys.argv', new=['foo', '-c', str(conf), '-d', str(data), '-q', '-v']):
        with pytest.raises(RuntimeError):
            cli.main()
