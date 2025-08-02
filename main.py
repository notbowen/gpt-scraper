import tyro
import pathlib
import sys
import re
import requests
import csv
import time

from bs4 import BeautifulSoup
from tqdm import tqdm
from waybackpy import WaybackMachineCDXServerAPI


def scrape_urls(filename):
    url = "chatgpt.com/share/*"
    user_agent = "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"
    pattern = r"https:\/\/chatgpt\.com\/share\/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"

    cdx = WaybackMachineCDXServerAPI(url, user_agent)

    with open(filename, "w+") as f:
        for item in tqdm(cdx.snapshots()):
            matches = re.findall(pattern, item.archive_url)
            if len(matches) > 0:
                f.write(matches[0] + "\n")


def parse_convo(url: str) -> tuple:
    r = requests.get(url)
    if r.status_code != 200:
        return "NOT FOUND"

    soup = BeautifulSoup(r.content, "html.parser")
    title = soup.title.string

    pattern = r"window\.__reactRouterContext\.streamController\.enqueue(.*)"
    script = re.findall(pattern, soup.prettify())[0]

    script = script.lstrip('("').rstrip('\\n");')
    script = script.replace('\\"', '"')
    script = script.replace("\\\\", "\\")

    script = script.replace("false", "False")
    script = script.replace("true", "True")

    parsed = eval(script)

    return title, parsed


def main(
    fetch_urls: bool = False, url_file: str = "urls.txt", out_file: str = "convos.csv"
):
    if fetch_urls:
        scrape_urls(url_file)

    urls = pathlib.Path(url_file)
    outfile = pathlib.Path(out_file)

    if not urls.exists():
        print(f"[x] Could not find URL file: {url_file}")
        sys.exit(-1)

    lines = urls.read_text().splitlines()
    outhandle = outfile.open("a")
    writer = csv.writer(outhandle)

    writer.writerow(["No.", "URL", "Title", "Content"])
    for i, line in tqdm(enumerate(lines), total=len(lines), desc="Parsing Convos"):
        time.sleep(1)

        res = parse_convo(line)

        if res == "NOT FOUND":
            continue

        title, parsed = res
        writer.writerow([i + 1, line, title, parsed])


if __name__ == "__main__":
    tyro.cli(main)
