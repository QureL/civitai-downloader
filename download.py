#!/usr/bin/env python3
import sys
import argparse
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote


CHUNK_SIZE = 1638400
TOKEN_FILE = Path.home() / '.civitai' / 'config'


def get_args():
    parser = argparse.ArgumentParser(
        description='CivitAI Downloader',
    )

    parser.add_argument(
        'url',
        type=str,
        help='CivitAI Download URL'
    )

    return parser.parse_args()


def get_token():
    try:
        with open(TOKEN_FILE, 'r') as file:
            token = file.read()
            return token
    except Exception as e:
        return None


def store_token(token):
    # Ensure the directory exists
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write the token to the file
    with open(TOKEN_FILE, 'w') as file:
        file.write(token)


def prompt_for_civitai_token():
    token = input('Please enter your CivitAI API token: ')
    store_token(token)
    return token


def download_file(url, token):
    # Prepare the initial request with necessary headers
    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    }
    request = urllib.request.Request(url, headers=headers)

    # Disable automatic redirect handling
    class NoRedirection(urllib.request.HTTPErrorProcessor):
        def http_response(self, request, response):
            return response
        https_response = http_response

    opener = urllib.request.build_opener(NoRedirection)
    response = opener.open(request)

    if response.status in [301, 302, 303, 307, 308]:
        redirect_url = response.getheader('Location')

        # Extract filename from the redirect URL
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)
        content_disposition = query_params.get('response-content-disposition', [None])[0]

        if content_disposition:
            filename = unquote(content_disposition.split('filename=')[1].strip('"'))
        else:
            raise Exception('Unable to determine filename')

        response = urllib.request.urlopen(redirect_url)
    else:
        raise Exception('No redirect found, something went wrong')

    # Download the file
    total_size = response.getheader('Content-Length')
    if total_size is not None:
        total_size = int(total_size)

    with open(filename, 'wb') as f:
        downloaded = 0

        while True:
            buffer = response.read(CHUNK_SIZE)

            if not buffer:
                break

            downloaded += len(buffer)
            f.write(buffer)

            if total_size is not None:
                progress = downloaded / total_size
                sys.stdout.write(f'\rDownloading: {filename} [{progress*100:.2f}%]')
                sys.stdout.flush()

    sys.stdout.write('\n')
    print(f'Download completed. File saved as: {filename}')


def main():
    args = get_args()
    token = get_token()

    if not token:
        token = prompt_for_civitai_token()

    download_file(args.url, token)


if __name__ == '__main__':
    main()
