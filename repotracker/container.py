# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2018 Mike Bonnet <mikeb@redhat.com>
# Logic for checking the state of container repos

import os
import subprocess
import json
import logging
import requests
from repotracker.utils import format_ts, format_time


log = logging.getLogger(__name__)


def inspect_repo(repo, token=None):
    """
    Inspect the repo. Return a dict whose keys are tag names and whose values
    are dicts of data about the tag. The dicts will have at least the following
    keys:
    - Name: name of the repo
    - Tag: name of the tag
    - Digest: checksum:digest of the image
    - Created: timestamp when the tag was created or last updated, in ISO 8601
               combined format in UTC
    - Labels: a list of labels on the image
    - Os: the operating system of the image
    - Architecture: the processor architecture of the image
    """
    results = {}
    if repo.startswith("quay.io"):
        # Use the quay.io REST API
        hostname, reponame = repo.split("/", 1)
        headers = {}
        if token:
            headers["Authorization"] = "Bearer {0}".format(token)
        page = 1
        while True:
            url = "https://{0}/api/v1/repository/{1}/tag/?onlyActiveTags=true&limit=100&page={2}".format(
                hostname, reponame, page
            )
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            for tag in data["tags"]:
                if tag["name"] not in results:
                    results[tag["name"]] = {
                        "Name": repo,
                        "Tag": tag["name"],
                        "Digest": tag["manifest_digest"],
                        "Created": format_ts(tag["start_ts"]),
                        "Labels": {},
                        "Os": "",
                        "Architecture": "",
                    }
            if not data["has_additional"]:
                break
            page += 1
    else:
        # Use skopeo
        tags = []
        # Don't assume the repo has a :latest tag.
        # Record info for whatever skopeo wants to tell us when we don't specify a tag.
        default = inspect_tag(repo)
        tags = default["RepoTags"]
        for tag in tags:
            try:
                results[tag] = inspect_tag(repo, tag=tag)
            except:
                log.error("Could not query %s:%s", repo, tag, exc_info=True)
    return results


def inspect_tag(repo, tag=None):
    """
    Inspect the contents of the tag within the given repo. If no tag is specified,
    skopeo should inspect the default tag.
    Returns a dict describing the image referenced by the given tag.
    If the repo is not accessible, or the tag does not exist, raise an
    exception.
    """
    cmd = ["/usr/bin/skopeo", "inspect"]
    if tag:
        tag = ":" + tag
        # If we're querying information about a specific tag, exclude the RepoTags list to improve performance.
        cmd.append("--no-tags")
    else:
        tag = ""
    cmd.append(f"docker://{repo}{tag}")
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8"
    )
    if proc.returncode:
        if "manifest unknown" in proc.stderr:
            # This tag has been deleted, which is represented by an empty dict.
            return {}
        raise RuntimeError(
            "Error inspecting {0}:{1}: {2}".format(repo, tag, proc.stderr)
        )
    return json.loads(proc.stdout)


def gen_result(repo, tag, tagdata):
    """
    Generate a dict containing info about the specified repo.
    """
    return {
        "repo": repo,
        "reponame": repo.split("/")[-1],
        "tag": tag,
        "digest": tagdata.get("Digest"),
        "created": format_time(tagdata.get("Created")),
        "labels": tagdata.get("Labels", {}),
        "os": tagdata.get("Os"),
        "arch": tagdata.get("Architecture"),
    }


def check_repos(conf, data):
    """
    Check the status of all repos in the config.
    Return a list of dicts describing the state of each repo.
    The 'action' field of each dict will indicate whether the repo has been
    'added', 'updated', or 'removed', relative to the data provided.
    """
    new_data = {}
    for section_name, section in conf.items():
        if section_name == "broker" or section.get("type") != "container":
            continue
        repo = section["repo"]
        token = section.get("token_env")
        if token:
            token = os.environ.get(token)
        try:
            tags = inspect_repo(repo, token)
        except:
            # Error communicating with the repo.
            # Assume it's a temporary error, reuse data from the previous run.
            log.error("Could not query %s", repo, exc_info=True)
            if repo in data:
                new_data[repo] = data[repo]
                new_data[repo]["ignore"] = True
            continue
        repodata = {}
        for tag, tagdata in tags.items():
            current = gen_result(repo, tag, tagdata)
            previous = data.get(repo, {}).get(tag, {})
            if tagdata:
                if previous:
                    if previous["action"] == "removed":
                        # Tag exists now, but it was removed on the previous run.
                        # Treat this as a tag addition
                        current["action"] = "added"
                        current["old_digest"] = None
                        log.info(
                            "%s:%s was readded (digest %s, old_digest was %s)",
                            repo,
                            tag,
                            current["digest"],
                            previous["old_digest"],
                        )
                    elif current["digest"] == previous["digest"]:
                        # Tag exists now, existed before, and has not changed
                        current["action"] = "unchanged"
                        current["old_digest"] = previous["old_digest"]
                        log.info(
                            "%s:%s is unchanged (digest %s)",
                            repo,
                            tag,
                            current["digest"],
                        )
                    else:
                        # Tag exists now, existed before, and has changed
                        current["action"] = "updated"
                        current["old_digest"] = previous["digest"]
                        log.info(
                            "%s:%s has been updated (digest %s, was %s)",
                            repo,
                            tag,
                            current["digest"],
                            previous["digest"],
                        )
                else:
                    # Tag exists now, but did not exist before
                    current["action"] = "added"
                    current["old_digest"] = None
                    log.info(
                        "%s:%s was added (digest %s)", repo, tag, current["digest"]
                    )
            else:
                if previous:
                    # Tag does not exist now, existed before
                    # Rare, race condition with deletion when inspecting a repo with skopeo.
                    current["action"] = "removed"
                    current["old_digest"] = previous["digest"]
                    log.info(
                        "%s:%s has been removed (digest was %s)",
                        repo,
                        tag,
                        previous["digest"],
                    )
                else:
                    # Tag does not exist now, did not exist before
                    # Should never happen, but could be a race condition with tag creation/deletion
                    log.warning("%s:%s is a ghost", repo, tag)
                    continue
            repodata[tag] = current
        for tag, previous in data.get(repo, {}).items():
            # Skip the ignore flag
            if tag == "ignore":
                continue
            # Need to check for tags that we've seen before and have been removed
            if tag not in repodata:
                if previous["action"] == "removed":
                    # we already processed the removal of this tag, so we can ignore it not
                    log.info(
                        "%s:%s was previously removed (old_digest %s), ignoring",
                        repo,
                        tag,
                        previous["old_digest"],
                    )
                else:
                    # Tag does not exist now, existed before
                    current = gen_result(repo, tag, {})
                    current["action"] = "removed"
                    current["old_digest"] = previous["digest"]
                    repodata[tag] = current
                    log.info(
                        "%s:%s has been removed (was %s)", repo, tag, previous["digest"]
                    )
        new_data[repo] = repodata
    return new_data
