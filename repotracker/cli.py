# Command-line interface to repotracker
# Mike Bonnet <mikeb@redhat.com>, 2018-09-27

import logging
import argparse
import pprint
from repotracker import utils, container, messaging


log = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(description='Send a message when the contents of a container repository changes')
    parser.add_argument('-q', '--quiet', help='Suppress output', action='store_true')
    parser.add_argument('-c', '--config', help='Config file', default='/etc/repotracker/repotracker.ini')
    parser.add_argument('-d', '--data', help='File used to record repo state',
                        default='/var/lib/repotracker/containers/repotracker-containers.json')
    return parser.parse_args()
    

def main():
    args = get_args()
    if args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)
    conf = utils.load_config(args.config)
    data = utils.load_data(args.data)
    new_data = container.check_repos(conf, data)
    if not args.quiet:
        pprint.pprint(new_data)
    try:
        messaging.send_container_updates(conf, new_data)
    except:
        log.error('Could not send all messages, container state will not be updated. '
                  'May result in duplicate messages.')
        raise
    else:
        utils.save_data(args.data, new_data)


if __name__ == '__main__':
    main()
