# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2018 Mike Bonnet <mikeb@redhat.com>


from repotracker import container
from repotracker.utils import format_ts, format_time
from unittest.mock import patch, call, Mock
import json
import pytest


CONF = {
    "broker": {
        "urls": "amqps://broker01.example.com",
    },
    "notest": {
        "type": "other",
        "repo": "example.com/some/other/repo",
    },
    "test": {
        "type": "container",
        "repo": "example.com/repos/testrepo",
    },
}
RAW_DATA_1 = """
{
    "Name": "example.com/repos/testrepo",
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
    ],
}


@patch.object(container.subprocess, "run", autospec=True)
def test_inspect_tag(run):
    """
    Test that inspect_tag() returns the correct output.
    """
    run.return_value.returncode = 0
    run.return_value.stdout = RAW_DATA_1
    result = container.inspect_tag("example.com/repos/testrepo", "latest")
    assert result == INSPECT_DATA_1


@patch.object(container.subprocess, "run", autospec=True)
def test_inspect_tag_no_tag(run):
    """
    Test that inspect_tag() with no tag name returns the correct output.
    """
    run.return_value.returncode = 0
    run.return_value.stdout = RAW_DATA_1
    result = container.inspect_tag("example.com/repos/testrepo")
    assert result == INSPECT_DATA_1


@patch.object(container.subprocess, "run", autospec=True)
def test_inspect_tag_raises(run):
    """
    Test that inspect_tag() raises an exception on an error.
    """
    run.return_value.returncode = 1
    with pytest.raises(RuntimeError):
        container.inspect_tag("example.com/repos/testrepo", "latest")


@patch.object(container.subprocess, "run", autospec=True)
def test_inspect_repo_raises(run):
    """
    Test that inspect_repo() raises an exception on an error when first querying the repo.
    """
    run.return_value.returncode = 1
    with pytest.raises(RuntimeError):
        container.inspect_repo("example.com/repos/testrepo")


@patch.dict(INSPECT_DATA_1, RepoTags=["some-tag"])
@patch.object(container.subprocess, "run", autospec=True)
def test_inspect_repo_no_latest(run):
    """
    Test that inspect_repo() against a repo with no :latest tag returns the correct results.
    """
    run.return_value.returncode = 0
    run.return_value.stdout = json.dumps(INSPECT_DATA_1)
    result = container.inspect_repo("example.com/repos/testrepo")
    assert result == {"some-tag": INSPECT_DATA_1}


def test_gen_result_null():
    """
    Test gen_result() when passed an empty dict.
    """
    result = container.gen_result("example.com/repos/testrepo", "testtag", {})
    assert result == {
        "repo": "example.com/repos/testrepo",
        "reponame": "testrepo",
        "tag": "testtag",
        "digest": None,
        "created": None,
        "labels": {},
        "os": None,
        "arch": None,
    }


@patch.object(
    container,
    "inspect_tag",
    autospec=True,
    side_effect=RuntimeError("could not inspect repo"),
)
def test_check_repos_raises(inspect_tag):
    """
    Test that an error inspecting the repo results in the correct output.
    """
    result = container.check_repos(CONF, {})
    inspect_tag.assert_called_once_with("example.com/repos/testrepo")
    assert result == {}


@patch.object(container, "inspect_tag", autospec=True, return_value=INSPECT_DATA_1)
def test_check_repos_added(inspect_tag):
    """
    Test that a new repo results in the correct output.
    """
    result = container.check_repos(CONF, {})
    assert inspect_tag.call_count == 2
    inspect_tag.assert_has_calls(
        [
            call("example.com/repos/testrepo"),
            call("example.com/repos/testrepo", tag="latest"),
        ]
    )
    assert result == {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            }
        }
    }


@patch.object(container, "inspect_tag", autospec=True, return_value=INSPECT_DATA_1)
def test_check_repos_unchanged(inspect_tag):
    """
    Test that an unchanged repo results in the correct output.
    """
    old_data = {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            }
        }
    }
    result = container.check_repos(CONF, old_data)
    assert inspect_tag.call_count == 2
    inspect_tag.assert_has_calls(
        [
            call("example.com/repos/testrepo"),
            call("example.com/repos/testrepo", tag="latest"),
        ]
    )
    assert result == {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "unchanged",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            }
        }
    }


@patch.object(container, "inspect_tag", autospec=True, return_value=INSPECT_DATA_1)
def test_check_repos_unchanged_ignore(inspect_tag):
    """
    Test that the 'ignore' flag is correctly ignored.
    """
    old_data = {
        "example.com/repos/testrepo": {
            "ignore": True,
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            },
        }
    }
    result = container.check_repos(CONF, old_data)
    assert inspect_tag.call_count == 2
    inspect_tag.assert_has_calls(
        [
            call("example.com/repos/testrepo"),
            call("example.com/repos/testrepo", tag="latest"),
        ]
    )
    assert result == {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "unchanged",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            }
        }
    }


@patch.object(container, "inspect_tag", autospec=True, return_value=INSPECT_DATA_2)
def test_check_repos_updated(inspect_tag):
    """
    Test that an updated repo results in the correct output.
    """
    old_data = {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            }
        }
    }
    result = container.check_repos(CONF, old_data)
    assert inspect_tag.call_count == 2
    inspect_tag.assert_has_calls(
        [
            call("example.com/repos/testrepo"),
            call("example.com/repos/testrepo", tag="latest"),
        ]
    )
    assert result == {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "updated",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_2["Digest"],
                "old_digest": INSPECT_DATA_1["Digest"],
                "created": format_time(INSPECT_DATA_2["Created"]),
                "labels": INSPECT_DATA_2["Labels"],
                "os": INSPECT_DATA_2["Os"],
                "arch": INSPECT_DATA_2["Architecture"],
            }
        }
    }


@patch.object(container, "inspect_tag", autospec=True, return_value=INSPECT_DATA_1)
def test_check_repos_removed(inspect_tag):
    """
    Test that a removed tag results in the correct output.
    """
    old_data = {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            },
            "stage": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "stage",
                "digest": INSPECT_DATA_2["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_2["Created"]),
                "labels": INSPECT_DATA_2["Labels"],
                "os": INSPECT_DATA_2["Os"],
                "arch": INSPECT_DATA_2["Architecture"],
            },
        }
    }
    result = container.check_repos(CONF, old_data)
    assert inspect_tag.call_count == 2
    inspect_tag.assert_has_calls(
        [
            call("example.com/repos/testrepo"),
            call("example.com/repos/testrepo", tag="latest"),
        ]
    )
    assert result == {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "unchanged",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            },
            "stage": {
                "action": "removed",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "stage",
                "digest": None,
                "old_digest": INSPECT_DATA_2["Digest"],
                "created": None,
                "labels": {},
                "os": None,
                "arch": None,
            },
        }
    }


@patch.object(container, "inspect_tag", autospec=True, return_value=INSPECT_DATA_1)
def test_check_repos_removed_previously(inspect_tag):
    """
    Test that a previously removed tag doesn't stay in the results.
    """
    old_data = {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            },
            "stage": {
                "action": "removed",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "stage",
                "digest": None,
                "old_digest": INSPECT_DATA_2["Digest"],
                "created": None,
                "labels": {},
                "os": None,
                "arch": None,
            },
        }
    }
    result = container.check_repos(CONF, old_data)
    assert inspect_tag.call_count == 2
    inspect_tag.assert_has_calls(
        [
            call("example.com/repos/testrepo"),
            call("example.com/repos/testrepo", tag="latest"),
        ]
    )
    assert result == {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "unchanged",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            },
        }
    }


@patch.dict(INSPECT_DATA_1, RepoTags=["latest", "stage"])
@patch.object(container.subprocess, "run", autospec=True)
def test_check_repos_removed_race(run):
    """
    Test that a tag that was removed after initial inspection results in the correct output.
    """
    run.side_effect = [
        Mock(returncode=0, stdout=json.dumps(INSPECT_DATA_1)),
        Mock(returncode=0, stdout=json.dumps(INSPECT_DATA_1)),
        Mock(
            returncode=1,
            stderr="FATA[0001] Error reading manifest stage in example.com/repos/testrepo:"
            "manifest unknown: manifest unknown\n",
        ),
    ]
    old_data = {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            },
            "stage": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "stage",
                "digest": INSPECT_DATA_2["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_2["Created"]),
                "labels": INSPECT_DATA_2["Labels"],
                "os": INSPECT_DATA_2["Os"],
                "arch": INSPECT_DATA_2["Architecture"],
            },
        }
    }
    result = container.check_repos(CONF, old_data)
    assert run.call_count == 3
    assert result == {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "unchanged",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            },
            "stage": {
                "action": "removed",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "stage",
                "digest": None,
                "old_digest": INSPECT_DATA_2["Digest"],
                "created": None,
                "labels": {},
                "os": None,
                "arch": None,
            },
        }
    }


@patch.dict(INSPECT_DATA_1, RepoTags=["latest", "stage"])
@patch.object(container.subprocess, "run", autospec=True)
def test_check_repos_removed_error(run):
    """
    Test that a tag that throws an error after initial inspection results in the correct output.
    """
    run.side_effect = [
        Mock(returncode=0, stdout=json.dumps(INSPECT_DATA_1)),
        Mock(returncode=0, stdout=json.dumps(INSPECT_DATA_1)),
        Mock(
            returncode=1,
            stderr="FATA[0001] Error reading manifest stage in example.com/repos/testrepo:"
            "some other error\n",
        ),
    ]
    old_data = {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            },
            "stage": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "stage",
                "digest": INSPECT_DATA_2["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_2["Created"]),
                "labels": INSPECT_DATA_2["Labels"],
                "os": INSPECT_DATA_2["Os"],
                "arch": INSPECT_DATA_2["Architecture"],
            },
        }
    }
    result = container.check_repos(CONF, old_data)
    assert run.call_count == 3
    assert result == {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "unchanged",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            },
            "stage": {
                "action": "removed",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "stage",
                "digest": None,
                "old_digest": INSPECT_DATA_2["Digest"],
                "created": None,
                "labels": {},
                "os": None,
                "arch": None,
            },
        }
    }


@patch.dict(INSPECT_DATA_1, RepoTags=["latest", "stage"])
@patch.object(container.subprocess, "run", autospec=True)
def test_check_repos_ghost(run):
    """
    Test that a tag that appeared in the RepoTags list, but no longer exists, and isn't present
    in the data from the previous run, results in the correct output.
    """
    run.side_effect = [
        Mock(returncode=0, stdout=json.dumps(INSPECT_DATA_1)),
        Mock(returncode=0, stdout=json.dumps(INSPECT_DATA_1)),
        Mock(
            returncode=1,
            stderr="FATA[0001] Error reading manifest stage in example.com/repos/testrepo:"
            "manifest unknown: manifest unknown\n",
        ),
    ]
    old_data = {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            },
        }
    }
    result = container.check_repos(CONF, old_data)
    assert run.call_count == 3
    assert result == {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "unchanged",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            },
        }
    }


@patch.object(container, "inspect_tag", autospec=True, return_value=INSPECT_DATA_1)
def test_check_repos_readded(inspect_tag):
    """
    Test that a repo that is readded immediately after it was removed results in
    a "added" message, and not an "updated" message.
    """
    old_data = {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "removed",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": None,
                "old_digest": "a1b2c3",
                "created": None,
                "labels": {},
                "os": None,
                "arch": None,
            }
        }
    }
    result = container.check_repos(CONF, old_data)
    assert inspect_tag.call_count == 2
    inspect_tag.assert_has_calls(
        [
            call("example.com/repos/testrepo"),
            call("example.com/repos/testrepo", tag="latest"),
        ]
    )
    assert result == {
        "example.com/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "example.com/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": INSPECT_DATA_1["Digest"],
                "old_digest": None,
                "created": format_time(INSPECT_DATA_1["Created"]),
                "labels": INSPECT_DATA_1["Labels"],
                "os": INSPECT_DATA_1["Os"],
                "arch": INSPECT_DATA_1["Architecture"],
            }
        }
    }


# Test use of the quay.io API
QUAY_API_DATA = {
    "has_additional": False,
    "page": 1,
    "tags": [
        {
            "name": "latest",
            "reversion": False,
            "start_ts": 1556038408,
            "image_id": "a81c3fba775bdcaa910fad989c6b790403eb916d37787c37783bd31d311af4ea",
            "last_modified": "Tue, 23 Apr 2019 16:53:28 -0000",
            "manifest_digest": "sha256:f205e8d3efc7105be8768ac5b0660b48fa2a57a8d854ba24317ab6fb6eba9bec",
            "docker_image_id": "a81c3fba775bdcaa910fad989c6b790403eb916d37787c37783bd31d311af4ea",
            "is_manifest_list": False,
            "size": 189669700,
        }
    ],
}
QUAY_API_DATA_MULTITAG = {
    "has_additional": False,
    "page": 1,
    "tags": [
        {
            "name": "stage",
            "reversion": False,
            "start_ts": 1555926025,
            "image_id": "cca7b8e074d5724e574c2929b3bffc4895629fd11e61199239f3aeadf1b4e45f",
            "last_modified": "Mon, 22 Apr 2019 09:40:25 -0000",
            "manifest_digest": "sha256:ac99b7fb73a6a412e4242936feab8aa0218bd19f3170c5471a49c303ae257408",
            "docker_image_id": "cca7b8e074d5724e574c2929b3bffc4895629fd11e61199239f3aeadf1b4e45f",
            "is_manifest_list": False,
            "size": 185937992,
        },
        {
            "name": "prod",
            "reversion": False,
            "start_ts": 1555837967,
            "image_id": "65e8ae7e46fcc8b6dd8211b77ad983d1277b5ad13f1833f1c86fc50dac95b7ff",
            "last_modified": "Sun, 21 Apr 2019 09:12:47 -0000",
            "manifest_digest": "sha256:4e689ce3d5968a4b17110cc8311de3ee948271614ee3576deea46115a24a58ac",
            "docker_image_id": "65e8ae7e46fcc8b6dd8211b77ad983d1277b5ad13f1833f1c86fc50dac95b7ff",
            "is_manifest_list": False,
            "size": 184283673,
        },
    ],
}
QUAY_API_DATA_MULTIPAGE = []
for i in range(3):
    QUAY_API_DATA_MULTIPAGE.append(
        {
            "has_additional": (i != 2),
            "page": i + 1,
            "tags": [
                {
                    "name": "tag" + str(i + 1),
                    "reversion": False,
                    "start_ts": QUAY_API_DATA["tags"][0]["start_ts"],
                    "image_id": QUAY_API_DATA["tags"][0]["image_id"],
                    "last_modified": QUAY_API_DATA["tags"][0]["last_modified"],
                    "manifest_digest": QUAY_API_DATA["tags"][0]["manifest_digest"],
                    "docker_image_id": QUAY_API_DATA["tags"][0]["docker_image_id"],
                    "is_manifest_list": False,
                    "size": QUAY_API_DATA["tags"][0]["size"],
                }
            ],
        }
    )


@patch.dict(CONF["test"], repo="quay.io/repos/testrepo")
@patch.object(container.requests, "get", autospec=True)
def test_quay_latest(get):
    """
    Test that data for a single tag from the quay.io API is handled correctly.
    """
    get.return_value.json.return_value = QUAY_API_DATA
    result = container.check_repos(CONF, {})
    get.assert_called_once_with(
        "https://quay.io/api/v1/repository/repos/testrepo/tag/?onlyActiveTags=true&limit=100&page=1",
        headers={},
    )
    assert result == {
        "quay.io/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": QUAY_API_DATA["tags"][0]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA["tags"][0]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            }
        }
    }


@patch.dict(CONF["test"], repo="quay.io/repos/testrepo", token_env="ENV_TOKEN")
@patch.dict(container.os.environ, {"ENV_TOKEN": "TOKEN"})
@patch.object(container.requests, "get", autospec=True)
def test_quay_token(get):
    """
    Test that token is passed from config.
    """
    get.return_value.json.return_value = QUAY_API_DATA
    container.check_repos(CONF, {})
    get.assert_called_once_with(
        "https://quay.io/api/v1/repository/repos/testrepo/tag/?onlyActiveTags=true&limit=100&page=1",
        headers={"Authorization": "Bearer TOKEN"},
    )


@patch.dict(CONF["test"], repo="quay.io/repos/testrepo", token_env="ENV_TOKEN")
@patch.dict(container.os.environ, {})
@patch.object(container.requests, "get", autospec=True)
def test_quay_token_missing(get):
    """
    Test missing token in env but defined in config.
    """
    get.return_value.json.return_value = QUAY_API_DATA
    container.check_repos(CONF, {})
    get.assert_called_once_with(
        "https://quay.io/api/v1/repository/repos/testrepo/tag/?onlyActiveTags=true&limit=100&page=1",
        headers={},
    )


@patch.dict(CONF["test"], repo="quay.io/repos/testrepo")
@patch.object(container.requests, "get", autospec=True)
def test_quay_multitag(get):
    """
    Test that data for multiple tags from the quay.io API is handled correctly.
    """
    get.return_value.json.return_value = QUAY_API_DATA_MULTITAG
    result = container.check_repos(CONF, {})
    get.assert_called_once_with(
        "https://quay.io/api/v1/repository/repos/testrepo/tag/?onlyActiveTags=true&limit=100&page=1",
        headers={},
    )
    assert result == {
        "quay.io/repos/testrepo": {
            "stage": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "stage",
                "digest": QUAY_API_DATA_MULTITAG["tags"][0]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA_MULTITAG["tags"][0]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            },
            "prod": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "prod",
                "digest": QUAY_API_DATA_MULTITAG["tags"][1]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA_MULTITAG["tags"][1]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            },
        }
    }


@patch.dict(CONF["test"], repo="quay.io/repos/testrepo")
@patch.object(container.requests, "get", autospec=True)
def test_quay_multipage(get):
    """
    Test that multiple pages of data from the quay.io API are handled correctly.
    """
    get.return_value.json.side_effect = QUAY_API_DATA_MULTIPAGE
    result = container.check_repos(CONF, {})
    calls = [
        call(
            "https://quay.io/api/v1/repository/repos/testrepo/tag/?onlyActiveTags=true&limit=100&page=1",
            headers={},
        ),
        call(
            "https://quay.io/api/v1/repository/repos/testrepo/tag/?onlyActiveTags=true&limit=100&page=2",
            headers={},
        ),
        call(
            "https://quay.io/api/v1/repository/repos/testrepo/tag/?onlyActiveTags=true&limit=100&page=3",
            headers={},
        ),
    ]
    get.assert_has_calls(calls, any_order=True)
    assert result == {
        "quay.io/repos/testrepo": {
            "tag1": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "tag1",
                "digest": QUAY_API_DATA["tags"][0]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA["tags"][0]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            },
            "tag2": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "tag2",
                "digest": QUAY_API_DATA["tags"][0]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA["tags"][0]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            },
            "tag3": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "tag3",
                "digest": QUAY_API_DATA["tags"][0]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA["tags"][0]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            },
        }
    }


@patch.dict(CONF["test"], repo="quay.io/repos/testrepo")
@patch.dict(QUAY_API_DATA_MULTITAG, has_additional=True)
@patch.dict(QUAY_API_DATA, page=2)
@patch.object(container.requests, "get", autospec=True)
def test_quay_multitag_multipage(get):
    """
    Test that multiple pages of data containing multiple tags from the quay.io API are handled correctly.
    """
    get.return_value.json.side_effect = [QUAY_API_DATA_MULTITAG, QUAY_API_DATA]
    result = container.check_repos(CONF, {})
    calls = [
        call(
            "https://quay.io/api/v1/repository/repos/testrepo/tag/?onlyActiveTags=true&limit=100&page=1",
            headers={},
        ),
        call(
            "https://quay.io/api/v1/repository/repos/testrepo/tag/?onlyActiveTags=true&limit=100&page=2",
            headers={},
        ),
    ]
    get.assert_has_calls(calls, any_order=True)
    assert result == {
        "quay.io/repos/testrepo": {
            "stage": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "stage",
                "digest": QUAY_API_DATA_MULTITAG["tags"][0]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA_MULTITAG["tags"][0]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            },
            "prod": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "prod",
                "digest": QUAY_API_DATA_MULTITAG["tags"][1]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA_MULTITAG["tags"][1]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            },
            "latest": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": QUAY_API_DATA["tags"][0]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA["tags"][0]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            },
        }
    }


@patch.dict(CONF["test"], repo="quay.io/repos/testrepo")
@patch.object(container.requests, "get", autospec=True)
def test_quay_error_unchanged(get):
    """
    Test that a (temporary) error when querying the quay.io API leaves the data unchanged.
    """
    get.return_value.raise_for_status.side_effect = RuntimeError("request error")
    old_data = {
        "quay.io/repos/testrepo": {
            "latest": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": QUAY_API_DATA["tags"][0]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA["tags"][0]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            }
        }
    }
    result = container.check_repos(CONF, old_data)
    get.assert_called_once_with(
        "https://quay.io/api/v1/repository/repos/testrepo/tag/?onlyActiveTags=true&limit=100&page=1",
        headers={},
    )
    assert result == {
        "quay.io/repos/testrepo": {
            "ignore": True,
            "latest": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "latest",
                "digest": QUAY_API_DATA["tags"][0]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA["tags"][0]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            },
        }
    }


@patch.dict(CONF["test"], repo="quay.io/repos/testrepo")
@patch.dict(QUAY_API_DATA_MULTITAG["tags"][0], name="prod")
@patch.object(container.requests, "get", autospec=True)
def test_quay_duplicate_tag(get):
    """
    Test that data for duplicate tags with the same name from the quay.io API is handled correctly.
    """
    get.return_value.json.return_value = QUAY_API_DATA_MULTITAG
    result = container.check_repos(CONF, {})
    get.assert_called_once_with(
        "https://quay.io/api/v1/repository/repos/testrepo/tag/?onlyActiveTags=true&limit=100&page=1",
        headers={},
    )
    assert result == {
        "quay.io/repos/testrepo": {
            "prod": {
                "action": "added",
                "repo": "quay.io/repos/testrepo",
                "reponame": "testrepo",
                "tag": "prod",
                "digest": QUAY_API_DATA_MULTITAG["tags"][0]["manifest_digest"],
                "old_digest": None,
                "created": format_ts(QUAY_API_DATA_MULTITAG["tags"][0]["start_ts"]),
                "labels": {},
                "os": "",
                "arch": "",
            }
        }
    }
