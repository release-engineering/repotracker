# Logic for checking the state of container repos
# Mike Bonnet, 2018-09-27

import subprocess
import json

def check_repos(conf, data):
    new_data = {}
    for section_name, section in conf.items():
        if section_name == 'broker' or section.get('type') != 'container':
            continue
        tags = section['tags'].split()
        for tag in tags:
            label = '{0}:{1}'.format(section['repo'], tag)
            proc = subprocess.run(['/usr/bin/skopeo', 'inspect', 'docker://{0}'.format(label)],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  encoding='utf-8')
            # XXX better error handling here
            proc.check_returncode()
            repodata = json.loads(proc.stdout)
            changed = False
            current = {'repo': section['repo'],
                       'tag': tag,
                       'digest': repodata['Digest']}
            if label in data:
                if data[label]['digest'] == current['digest']:
                    current['old_digest'] = data[label]['old_digest']
                    current['changed'] = False
                else:
                    current['old_digest'] = data[label]['digest']
                    current['changed'] = True
            else:
                current['old_digest'] = None
                current['changed'] = False
            new_data[label] = current
    return new_data
