# Logic for checking the state of container repos
# Mike Bonnet, 2018-09-27

import subprocess
import json
import logging


log = logging.getLogger(__name__)


def inspect_repo(repo, tag):
    """
    Inspect the contents of the tag within the given repo.
    Returns a dict describing the image referenced by the given tag.
    If the repo is not accessible, or the tag does not exist, raise an
    exception.
    """
    proc = subprocess.run(['/usr/bin/skopeo', 'inspect', 'docker://{0}:{1}'.format(repo, tag)],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          encoding='utf-8')
    if proc.returncode:
        raise RuntimeError('Error inspecting {0}:{1}: {2}'.format(repo, tag, proc.stderr))
    return json.loads(proc.stdout)


def gen_result(repo, tag, tagdata):
    """
    Generate a dict containing info about the specified repo.
    """
    return {
        'repo': repo,
        'reponame': repo.split('/')[-1],
        'tag': tag,
        'digest': tagdata.get('Digest'),
        'created': tagdata.get('Created'),
        'labels': tagdata.get('Labels', {}),
        'os': tagdata.get('Os'),
        'arch': tagdata.get('Architecture'),
        'layers': tagdata.get('Layers', [])
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
        if section_name == 'broker' or section.get('type') != 'container':
            continue
        repo = section['repo']
        try:
            latest_data = inspect_repo(repo, 'latest')
        except:
            log.error('Could not query {0}:latest', repo, exc_info=True)
            continue
        new_data[repo] = {}
        tags = latest_data['RepoTags']
        for tag in tags:
            if tag == 'latest':
                tagdata = latest_data
            else:
                try:
                    tagdata = inspect_repo(repo, tag)
                except:
                    log.error('Could not query {0}:{1}', repo, tag, exc_info=True)
                    tagdata = {}
            current = gen_result(repo, tag, tagdata)
            previous = data.get(repo, {}).get(tag, {})
            if tagdata:
                if previous:
                    if current['digest'] == previous['digest']:
                        # Tag exists now, existed before, and has not changed
                        current['action'] = 'unchanged'
                        current['old_digest'] = previous['old_digest']
                        log.info('%s:%s is unchanged (digest %s)', repo, tag, current['digest'])
                    else:
                        # Tag exists now, existed before, and has changed
                        current['action'] = 'updated'
                        current['old_digest'] = previous['digest']
                        log.info('%s:%s has been updated (digest %s, was %s)',
                                 repo, tag, current['digest'], previous['digest'])
                else:
                    # Tag exists now, but did not exist before
                    current['action'] = 'added'
                    current['old_digest'] = None
                    log.info('%s:%s was added (digest %s)', repo, tag, current['digest'])
            else:
                if previous:
                    # Tag does not exist now, existed before
                    # Rare, race condition with deletion
                    current['action'] = 'removed'
                    current['old_digest'] = previous['digest']
                    log.info('%:%s has been removed (was %s)', repo, tag, previous['digest'])
                else:
                    # Tag does not exist now, did not exist before
                    # Should never happen, but could be a race condition with tag creation/deletion
                    log.warning('%s:%s is a ghost', repo, tag)
                    continue
            new_data[repo][tag] = current
        for tag, previous in data.get(repo, {}).items():
            # Need to check for tags that we've seen before and have been removed
            if tag not in new_data[repo]:
                # Tag does not exist now, existed before
                current = gen_result(repo, tag, {})
                current['action'] = 'removed'
                current['old_digest'] = previous['digest']
                new_data[repo][tag] = current
    return new_data
