# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2018 Mike Bonnet <mikeb@redhat.com>


from repotracker import container
from unittest.mock import patch, call
import json
import pytest

CONF = {
    'broker': {
        'urls': 'amqps://broker01.example.com',
    },
    'notest': {
        'type': 'other',
        'repo': 'example.com/some/other/repo',
    },
    'test': {
        'type': 'container',
        'repo': 'example.com/repos/testrepo',
    }
}
RAW_DATA_1 = """
{
    "Name": "example.com/repos/testrepo",
    "Tag": "latest",
    "Digest": "sha256:ad2c57edd37de7c7e51baea3dbfb97e469034e098a15b3c91fa3dd3da63bf66e",
    "RepoTags": [
        "latest"
    ],
    "Created": "2018-10-26T00:07:54.904635308Z",
    "DockerVersion": "17.09.0-ce",
    "Labels": {
        "license": "GPLv3",
        "name": "testrepo"
    },
    "Architecture": "amd64",
    "Os": "linux",
    "Layers": [
        "sha256:a3ed95caeb02ffe68cdd9fd84406680ae93d633cb16422d00e8a7c22955b46d4",
        "sha256:565884f490d9ec697e519c57d55d09e268542ef2c1340fd63262751fa308f047"
    ]
}
"""
INSPECT_DATA_1 = json.loads(RAW_DATA_1)
INSPECT_DATA_2 = {
    "Name": "example.com/repos/testrepo",
    "Tag": "latest",
    "Digest": "sha256:8e69c47663d1f8d8f25322170a5211df912b409b0e8c92ffe1b365ee99d672ed",
    "RepoTags": [
        "latest",
    ],
    "Created": "2018-10-27T00:08:23.904635308Z",
    "DockerVersion": "17.09.0-ce",
    "Labels": {
        "license": "GPLv2",
        "name": "testrepo",
    },
    "Architecture": "aarch64",
    "Os": "debian",
    "Layers": [
        "sha256:2f5e62cf5f1c6d35613e4c848f59901195991fefb8774fcf4e585c6842026f21",
        "sha256:aecae378e09ee01f6976750bc840ee596b204bb35d7d121037021cbc927fcd7b",
    ]
}


@patch.object(container.subprocess, 'run', autospec=True)
def test_inspect_repo(run):
    """
    Test that inspect_repo() returns the correct output.
    """
    run.return_value.returncode = 0
    run.return_value.stdout = RAW_DATA_1
    result = container.inspect_repo('example.com/repos/testrepo', 'latest')
    assert result == INSPECT_DATA_1


@patch.object(container.subprocess, 'run', autospec=True)
def test_inspect_repo_raises(run):
    """
    Test that inspect_repo() raises an exception on an error.
    """
    run.return_value.returncode = 1
    with pytest.raises(RuntimeError):
        container.inspect_repo('example.com/repos/testrepo', 'latest')


def test_gen_result_null():
    """
    Test gen_result() when passed an empty dict.
    """
    result = container.gen_result('example.com/repos/testrepo', 'testtag', {})
    assert result == {
        'repo': 'example.com/repos/testrepo',
        'reponame': 'testrepo',
        'tag': 'testtag',
        'digest': None,
        'created': None,
        'labels': {},
        'os': None,
        'arch': None
    }


@patch.object(container, 'inspect_repo', autospec=True, side_effect=RuntimeError('could not inspect repo'))
def test_check_repos_raises(inspect_repo):
    """
    Test that an error inspecting the repo results in the correct output.
    """
    result = container.check_repos(CONF, {})
    inspect_repo.assert_called_once_with('example.com/repos/testrepo', 'latest')
    assert result == {}


@patch.object(container, 'inspect_repo', autospec=True, return_value=INSPECT_DATA_1)
def test_check_repos_added(inspect_repo):
    """
    Test that a new repo results in the correct output.
    """
    result = container.check_repos(CONF, {})
    inspect_repo.assert_called_once_with('example.com/repos/testrepo', 'latest')
    assert result == {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            }
        }
    }


@patch.object(container, 'inspect_repo', autospec=True, return_value=INSPECT_DATA_1)
def test_check_repos_unchanged(inspect_repo):
    """
    Test that an unchanged repo results in the correct output.
    """
    old_data = {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            }
        }
    }
    result = container.check_repos(CONF, old_data)
    inspect_repo.assert_called_once_with('example.com/repos/testrepo', 'latest')
    assert result == {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'unchanged',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            }
        }
    }


@patch.object(container, 'inspect_repo', autospec=True, return_value=INSPECT_DATA_2)
def test_check_repos_updated(inspect_repo):
    """
    Test that an updated repo results in the correct output.
    """
    old_data = {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            }
        }
    }
    result = container.check_repos(CONF, old_data)
    inspect_repo.assert_called_once_with('example.com/repos/testrepo', 'latest')
    assert result == {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'updated',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_2['Digest'],
                'old_digest': INSPECT_DATA_1['Digest'],
                'created': INSPECT_DATA_2['Created'],
                'labels': INSPECT_DATA_2['Labels'],
                'os': INSPECT_DATA_2['Os'],
                'arch': INSPECT_DATA_2['Architecture'],
            }
        }
    }


@patch.object(container, 'inspect_repo', autospec=True, return_value=INSPECT_DATA_1)
def test_check_repos_removed(inspect_repo):
    """
    Test that a removed tag results in the correct output.
    """
    old_data = {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            },
            'stage': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'stage',
                'digest': INSPECT_DATA_2['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_2['Created'],
                'labels': INSPECT_DATA_2['Labels'],
                'os': INSPECT_DATA_2['Os'],
                'arch': INSPECT_DATA_2['Architecture'],
            }
        }
    }
    result = container.check_repos(CONF, old_data)
    inspect_repo.assert_called_once_with('example.com/repos/testrepo', 'latest')
    assert result == {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'unchanged',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            },
            'stage': {
                'action': 'removed',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'stage',
                'digest': None,
                'old_digest': INSPECT_DATA_2['Digest'],
                'created': None,
                'labels': {},
                'os': None,
                'arch': None,
            }
        }
    }


@patch.object(container, 'inspect_repo', autospec=True, return_value=INSPECT_DATA_1)
def test_check_repos_removed_previously(inspect_repo):
    """
    Test that a previously removed tag doesn't stay in the results.
    """
    old_data = {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            },
            'stage': {
                'action': 'removed',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'stage',
                'digest': None,
                'old_digest': INSPECT_DATA_2['Digest'],
                'created': None,
                'labels': {},
                'os': None,
                'arch': None,
            }
        }
    }
    result = container.check_repos(CONF, old_data)
    inspect_repo.assert_called_once_with('example.com/repos/testrepo', 'latest')
    assert result == {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'unchanged',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            },
        }
    }


@patch.dict(INSPECT_DATA_1, RepoTags=['latest', 'stage'])
@patch.object(container, 'inspect_repo', autospec=True, side_effect=[INSPECT_DATA_1, RuntimeError('no such tag')])
def test_check_repos_removed_race(inspect_repo):
    """
    Test that a tag that was removed after initial inspection results in the correct output.
    """
    old_data = {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            },
            'stage': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'stage',
                'digest': INSPECT_DATA_2['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_2['Created'],
                'labels': INSPECT_DATA_2['Labels'],
                'os': INSPECT_DATA_2['Os'],
                'arch': INSPECT_DATA_2['Architecture'],
            }
        }
    }
    result = container.check_repos(CONF, old_data)
    assert inspect_repo.call_count == 2
    calls = [
        call('example.com/repos/testrepo', 'latest'),
        call('example.com/repos/testrepo', 'stage'),
    ]
    inspect_repo.assert_has_calls(calls)
    assert result == {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'unchanged',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            },
            'stage': {
                'action': 'removed',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'stage',
                'digest': None,
                'old_digest': INSPECT_DATA_2['Digest'],
                'created': None,
                'labels': {},
                'os': None,
                'arch': None,
            }
        }
    }


@patch.dict(INSPECT_DATA_1, RepoTags=['latest', 'stage'])
@patch.object(container, 'inspect_repo', autospec=True, side_effect=[INSPECT_DATA_1, RuntimeError('no such tag')])
def test_check_repos_ghost(inspect_repo):
    """
    Test that a tag that appeared in the RepoTags list, but no longer exists, and isn't present
    in the data from the previous run, results in the correct output.
    """
    old_data = {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            },
        }
    }
    result = container.check_repos(CONF, old_data)
    assert inspect_repo.call_count == 2
    calls = [
        call('example.com/repos/testrepo', 'latest'),
        call('example.com/repos/testrepo', 'stage'),
    ]
    inspect_repo.assert_has_calls(calls)
    assert result == {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'unchanged',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            },
        }
    }


@patch.object(container, 'inspect_repo', autospec=True, return_value=INSPECT_DATA_1)
def test_check_repos_readded(inspect_repo):
    """
    Test that a repo that is readded immediately after it was removed results in
    a "added" message, and not an "updated" message.
    """
    old_data = {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'removed',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': None,
                'old_digest': 'a1b2c3',
                'created': None,
                'labels': {},
                'os': None,
                'arch': None,
            }
        }
    }
    result = container.check_repos(CONF, old_data)
    inspect_repo.assert_called_once_with('example.com/repos/testrepo', 'latest')
    assert result == {
        'example.com/repos/testrepo': {
            'latest': {
                'action': 'added',
                'repo': 'example.com/repos/testrepo',
                'reponame': 'testrepo',
                'tag': 'latest',
                'digest': INSPECT_DATA_1['Digest'],
                'old_digest': None,
                'created': INSPECT_DATA_1['Created'],
                'labels': INSPECT_DATA_1['Labels'],
                'os': INSPECT_DATA_1['Os'],
                'arch': INSPECT_DATA_1['Architecture'],
            }
        }
    }
