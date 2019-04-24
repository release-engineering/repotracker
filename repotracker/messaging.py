# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2018 Mike Bonnet <mikeb@redhat.com>
# Send messages about updated repos to the UMB

import json
import logging
from rhmsg.activemq.producer import AMQProducer


log = logging.getLogger(__name__)


def gen_msg(tagdata):
    """
    Generate a (headers, body) tuple from the tag data.
    """
    headers = tagdata.copy()
    del headers['labels']
    body = json.dumps(tagdata, ensure_ascii=False)
    return (headers, body)


def send_container_updates(conf, data):
    added = []
    updated = []
    removed = []
    for repo, tags in data.items():
        if 'ignore' in tags:
            log.info('Ignoring data for %s', repo)
            continue
        for tag, tagdata in tags.items():
            msg = gen_msg(tagdata)
            if tagdata['action'] == 'unchanged':
                pass
            elif tagdata['action'] == 'updated':
                updated.append(msg)
            elif tagdata['action'] == 'added':
                added.append(msg)
            elif tagdata['action'] == 'removed':
                removed.append(msg)
            else:
                log.error('Unknown action: %s', tagdata['action'])  # pragma: no cover
    producer = AMQProducer(urls=conf['broker']['urls'].split(),
                           certificate=conf['broker']['cert'],
                           private_key=conf['broker']['key'],
                           trusted_certificates=conf['broker']['cacerts'])
    prefix = conf['broker']['topic_prefix'].rstrip('.')
    if added:
        with producer as prod:
            prod.through_topic(prefix + '.container.tag.added')
            prod.send_msgs(added)
    if updated:
        with producer as prod:
            prod.through_topic(prefix + '.container.tag.updated')
            prod.send_msgs(updated)
    if removed:
        with producer as prod:
            prod.through_topic(prefix + '.container.tag.removed')
            prod.send_msgs(removed)
    log.info('Sent %s messages', sum(map(len, [added, updated, removed])))
