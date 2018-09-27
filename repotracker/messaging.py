# Send messages about updated repos to the UMB
# Mike Bonnet, 2018-09-27

import json
from rhmsg.activemq.producer import AMQProducer


def send_container_updates(conf, data):
    msgs = []
    for repo in data.values():
        if repo['changed']:
            headers = repo.copy()
            del headers['changed']
            headers['reponame'] = headers['repo'].split('/')[-1]
            body = json.dumps(headers, ensure_ascii=False)
            msgs.append((headers, body))
    if msgs:
        prod = AMQProducer(urls=conf['broker']['urls'].split(','),
                           certificate=conf['broker']['cert'],
                           private_key=conf['broker']['key'],
                           trusted_certificates=conf['broker']['cacerts'],
                           topic=conf['broker']['topic'])
        prod.send_msgs(msgs)
