###############################################################################
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
###############################################################################

# Script from https://github.com/wmo-im/wis2-topic-hierarchy/blob/main/scripts/upload_changes.py

import argparse
from pathlib import Path
import requests

HEADERS = {
    'Content-type': 'text/turtle; charset=UTF-8'
}

PROD_REGISTRY = 'https://codes.wmo.int'
TEST_REGISTRY = 'https://ci.codes.wmo.int'


def authenticate(base_url: str, user_id: str,
                 password: str) -> requests.Session:
    """
    Constructs authenticated session (with JSESSIONID cookie)

    :param base_url: base URL of registry API
    :param user_id: GitHub User ID
    :param password: password

    :returns: Session for further interaction upon successful login
    """

    url = f'{base_url}/system/security/apilogin'
    print(f'Authenticating at {url}')

    session = requests.Session()

    data = {
        'userid': f'https://api.github.com/users/{user_id}',
        'password': password
    }

    auth = session.post(url, data=data)

    if auth.status_code != 200:
        raise ValueError('Authentication failed')

    return session


def post(session: requests.Session, url: str, payload: str,
         dry_run: bool, verbose: bool, status: str) -> None:
    """
    Posts new content to the intended parent register

    :param session: API session
    :param url: URL of HTTP POST
    :param payload: HTTP POST payload
    :param dry_run: whether to run as a dry run (simulates request only)
    :param verbose: whether to provide verbose output
    :param status: publication status (experimental, stable)

    :returns: `None`
    """

    params = {
        'status': status
    }

    if not dry_run:
        if verbose:
            print(f'  Posting to: {url}')
            print(f'    headers: {HEADERS}')
            print(f'    params: {params}')

        res = session.post(url, headers=HEADERS, data=payload.encode('utf-8'),
                           params=params, stream=False)

        if res.status_code != 201:
            print(f'  POST failed with {res.status_code} {res.reason}: {res.content.decode("utf-8")}')  # noqa
        elif verbose:
            print(f'  POST succeeded with {res.status_code} {res.reason}')
    else:
        print(f'  HTTP POST (dry run) to: {url}')
        print(f'    headers: {HEADERS}')
        print(f'    params: {params}')

    return


def put(session: requests.Session, url: str, payload: str,
        dry_run: bool, verbose: bool, status: str) -> None:
    """
    Updates definition of a register or entity.

    :param session: API session
    :param url: URL of HTTP POST
    :param payload: HTTP POST payload
    :param dry_run: whether to run as a dry run (simulates request only)
    :param verbose: whether to provide verbose output
    :param status: publication status (experimental, stable)

    :returns: `None`
    """

    params = {
        'status': status,
        'non-member-properties': 'true'
    }

    if not dry_run:
        if verbose:
            print(f'  HTTP PUT to: {url}')
            print(f'    headers: {HEADERS}')
            print(f'    params: {params}')

        res = session.put(url, headers=HEADERS, data=payload.encode('utf-8'),
                          params=params)

        if res.status_code != 204:
            print(f'  PUT failed with {res.status_code} {res.reason}: {res.content.decode("utf-8")}')  # noqa
            # caching issue
            if res.status_code == 404:  # try POST
                url = '/'.join(url.split('/')[:-1])
                post(session, url, payload, dry_run, verbose, status)
        elif verbose:
            print(f'  PUT succeeded with {res.status_code} {res.reason}')
    else:
        print(f'  HTTP PUT (dry run) to {url}')
        print(f'    headers: {HEADERS}')
        print(f'    params: {params}')

    return


def upload(session: requests.Session, url: str, payload: str,
           dry_run: bool, verbose: bool, status: str) -> None:
    """
    PUTs or POSTs given data depending if it already exists or not

    :param session: API session
    :param url: URL of HTTP POST
    :param payload: HTTP POST payload
    :param dry_run: whether to run as a dry run (simulates request only)
    :param verbose: whether to provide verbose output
    :param status: publication status (experimental, stable)

    :returns: `None`
    """

    # to check existence adjust the URL
    url_to_check = url + '/'
    if verbose:
        print(f'  Checking {url_to_check} - ', end=' ')
    response = session.get(url_to_check)

    if verbose:
        print(response.status_code)

    #if url == "https://ci.codes.wmo.int/bufr4-17-10-24/code_tables/0":
        #response.status_code = 404

    if response.status_code == 200:
        if verbose:
            print('Existing entry, using PUT')
        put(session, url, payload, dry_run, verbose, status)
    elif response.status_code == 404 :
        if verbose:
            print('New entry, using POST')
        url = '/'.join(url.split('/')[:-1])
        post(session, url, payload, dry_run, verbose, status)
    else:
        raise ValueError(
            f'Cannot upload to {url}: {response.status_code} {response.reason}: {response.content.decode("utf-8")}'  # noqa
        )


def upload_file(session: requests.Session, url: str, register: str,
                basepath: Path,
                relativePath: Path,
                dry_run: bool, verbose: bool, status: str) -> None:
    """
    Uploads given TTL file to the registry

    :param session: API session
    :param url: URL of HTTP POST
    :param filepath: `pathlib.Path` of filepath
    :param dry_run: whether to run as a dry run (simulates request only)
    :param verbose: whether to provide verbose output
    :param status: publication status (experimental, stable)

    :returns: `None`
    """
    # Load TTL data

    filepath = basepath.joinpath(relativePath)

    with filepath.open(encoding='utf-8') as fh:
        ttl_data = fh.read()

    # urlpath = str(filepath.parent.as_posix())
    urlpath = str(relativePath.parent.as_posix())
    node = filepath.stem

    # set URL to upload to
    if urlpath == "." :
        url = f'{url}/{register}/{node}'
    else:
        url = f'{url}/{register}/{urlpath}/{node}'

    # Some user feedback
    print(f'Uploading {filepath} to {url}')
    upload(session, url, ttl_data, dry_run, verbose, status)

    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('user_id', help='GitHub User ID')
    parser.add_argument(
        'password',
        help=f'Password or token generated at {TEST_REGISTRY}/ui/temporary-password'  # noqa
    )
    parser.add_argument('mode', help='Mode: test or prod')
    parser.add_argument('register', help='Register to upload to')
    parser.add_argument('directory',
                        help='Name of the directory with TTL files to upload')

    parser.add_argument(
        '-n',
        '--dry-run',
        action='store_true',
        help='Print what would be uploaded without actually sending anything'
    )
    parser.add_argument('-v', '--verbose',
                        action='store_true', help='Print more details')
    parser.add_argument('-s', '--status', default='experimental',
                        help='Status (experimental, stable)')

    args = parser.parse_args()

    REGISTRY = TEST_REGISTRY

    if not Path(args.directory).is_dir():
        raise ValueError(f'Directory {args.directory} does not exists.')
    if args.mode not in ['test', 'prod']:
        raise ValueError('Mode must be either "test" or "prod"')
    if args.status not in ['stable', 'experimental']:
        raise ValueError('Mode must be either "stable" or "experimental"')
    if args.mode == 'prod':
        REGISTRY = PROD_REGISTRY

    print(f'Running upload against {REGISTRY}')

    session = authenticate(REGISTRY, args.user_id, args.password)

    base_path = Path(args.directory)
    idx = 0
    for filename in base_path.rglob('*.ttl'):
        idx += 1
        relative_path = filename.relative_to(args.directory)
        print(f"Processing: {filename}")
        upload_file(session, REGISTRY,
                    args.register,
                    base_path,
                    relative_path,
                    args.dry_run,
                    args.verbose,
                    args.status)
    print('Done')