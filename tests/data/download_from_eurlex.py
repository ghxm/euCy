import argparse
import os
import re
import requests
import time
from eucy import regex as eure

parser = argparse.ArgumentParser()

parser.add_argument("input",nargs="*")
parser.add_argument("-v", "--verbose", action="count", default=0, help="prints out iterations in parallel processing")
parser.add_argument("-r", "--replace", action="store_true", default=False)
parser.add_argument("-o", "--outdir", default="data")

args = parser.parse_args()

if not os.path.exists(args.outdir):
    os.makedirs(args.outdir)

def is_celex_id(id):

    id = id.strip()

    if len(id) < 8:
        return False

    if len(id) > 15:
        return False

    if re.search(eure.celex_ids, id) is not None:
        return True
    else:
        return False

def extract_celex_id(url):

    # cut off everything before CELEX
    url = url.split("CELEX:")[1]

    # cut off everything after CELEX
    url = url.split("/")[0]

    return url



def is_url(id):

    id = id.strip()

    if re.search('http[s]*?://', id) is not None:
        return True
    else:
        return False

def make_eurlex_text_url(id):

    id = id.strip()

    return "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{}".format(id)


if args.input:
    # check if filepath
    if os.path.isfile(args.input[0]):
        with open(args.input[0]) as f:
            ids = f.read().splitlines()
    else:
        ids = args.input

urls = [id if is_url(id) else make_eurlex_text_url(id) for id in ids if id.strip != ""]

if args.verbose:
    print(str(len(urls)) +" valid urls found")

for url in urls:
    if args.verbose:
        print("Downloading " + url)

    filename = extract_celex_id(url)

    if is_celex_id(filename):
        filename = filename + ".html"

    if args.verbose:
        print("Saving to " + filename)

    download_success = False
    tries = 0

    while not download_success and tries < 5:

        tries += 1

        try:
            r = requests.get(url)
            download_success = True
        except:
            print("\tError downloading " + url)
            time.sleep(5)
            continue

        try:
            r.raise_for_status()
        except:
            print("\tError downloading " + url)
            continue

    if download_success:

        if args.replace or not os.path.exists(os.path.join(args.outdir, filename)):

            if args.verbose:
                print("\tSaving to " + filename)

            with open(os.path.join(args.outdir, filename), "wb") as f:
                f.write(r.content)
        else:
            if args.verbose:
                print("\tFile exists. Skipping")

    time.sleep(1)

if args.verbose:
    print("Done")
