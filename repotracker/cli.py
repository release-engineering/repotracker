# Command-line interface to repotracker
# Mike Bonnet <mikeb@redhat.com>, 2018-09-27

import argparse
import pprint
from repotracker import utils, container, messaging


def get_args():
    parser = argparse.ArgumentParser(description='Send a message when the contents of a yum or container repository changes')
    parser.add_argument('-c', '--config', help='Config file', default='/etc/repotracker/repotracker.ini')
    parser.add_argument('-d', '--data', help='File used to record repo state', default='/var/lib/repotracker/containers/repotracker-containers.json')
    return parser.parse_args()
    

def main():
    args = get_args()
    conf = utils.load_config(args.config)
    data = utils.load_data(args.data)
    new_data = container.check_repos(conf, data)
    pprint.pprint(new_data)
    utils.save_data(args.data, new_data)
    messaging.send_container_updates(conf, new_data)


if __name__ == '__main__':
    main()
