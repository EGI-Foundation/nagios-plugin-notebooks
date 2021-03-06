import argparse
import logging
import sys

from six.moves.urllib.parse import urljoin

import requests
from requests.exceptions import ConnectionError, HTTPError

def status2code(status):
    code_map = {
        'OK': 0,
        'WARNING': 1,
        'CRITICAL': 2,
    }
    return code_map.get(status.upper(), 2)


def get_notebook_status(status_url, timeout=10):
    logging.debug('Querying %s for status', status_url)
    try:
        r = requests.get(status_url, timeout=timeout,
                         headers={'accept': 'application/json'})
        r.raise_for_status()
        status = r.json()
        logging.debug('Full status message: %s' % status)
        logging.info("%s: %s", status['code'], status['msg'])
        return status2code(status['code'])
    except (ConnectionError, HTTPError) as e:
        logging.info("CRITICAL: Unable to get status, %s", e.message)
        return status2code('CRITICAL')


def main():
    parser = argparse.ArgumentParser(
        description='Nagios plugin for EGI Notebooks',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars='@',
        conflict_handler="resolve",
    )

    parser.add_argument('-t', '--timeout', default=10, type=int,
                        help='Timeout in seconds of the probe')

    parser.add_argument('--url', help='URL of the the EGI notebooks endpoint')

    parser.add_argument('--status-path', default='services/status/',
                        help=('Path in the endpoint for the monitoring '
                              'service'))

    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help='Be verbose')

    parser.add_argument('-H', '--host', help='Host to be checked')

    parser.add_argument('-p', '--port', default=443, type=int,
                        help='Port to be checked')

    opts = parser.parse_args()
    log_level = logging.INFO
    if opts.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(stream=sys.stdout, level=log_level)

    # URL takes precedence over -H and -p
    if not opts.url:
        if not opts.host:
            logging.error('Mising url or host to check')
            sys.exit(status2code('CRITICAL'))
        status_url = 'https://%s:%d/' % (opts.host, opts.port)
    else:
        status_url = opts.url

    if not status_url.endswith('/'):
        status_url = status_url + '/'
    full_status_url = urljoin(status_url, opts.status_path)
    sys.exit(get_notebook_status(full_status_url, opts.timeout))
