from os import error
import pathlib
import requests
import random
import re
import sys
import time

from bs4 import BeautifulSoup

base_url = "https://www.loc.gov/pictures/search/"

base_params = {
    "q": "mrg",
    "sp": 1
    }

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Safari/605.1.15"
}

DETAIL_FOLDER = pathlib.Path("download/detail")

def get_or_exit(url, params=None, err_msg="error retrieving page"):

    r = requests.get(url, params=params, headers=HEADERS)
    if r.status_code != 200:
        with open("download/err.html", "w") as err_page:
            soup = BeautifulSoup(r.content)
            err_page.write(soup.prettify())
        print(r.url)
        sys.exit(err_msg)
    return r


def get_results():
    last_list = int(open("download/last_list.txt").read().strip())


    visited_details = set([d.name for d in DETAIL_FOLDER.iterdir() if d.is_dir()])
    
    for i in range(last_list, 587):
        params = {
            "q": "mrg",
            "sp": i
        }
        
        r = get_or_exit(base_url, params, "Error retrieving list page.")
        print(f"Got list page #{i} - {r.url}")
        soup = BeautifulSoup(r.content, features="lxml")
    
        with open(f"download/list/{i}.html", "w") as list_page:
            list_page.write(soup.prettify())
        # get list of links to detail pages
        links = soup.select("div.result_item > p > a")
        for link in links:
            # visit each link, save detail page, save MARC record, save JPG
            id_num = link["href"].split("/")[-2]
            if id_num in visited_details:
                print(f"Already visited {id_num} - skipping")
                continue
            dr = get_or_exit(link["href"], err_msg="Error retrieving detail page")
            print(f"Got detail page for {id_num} - {dr.url}")
            ds = BeautifulSoup(dr.content, features="lxml")

            # save detail page
            page_folder = DETAIL_FOLDER / id_num
            page_folder.mkdir()
            with open(page_folder / "detail.html", "w") as detail_page:
                detail_page.write(ds.prettify())

            # save MARC record
            marc_url = ds.select("a#item_marc")[0]["href"]
            mr = get_or_exit(marc_url, err_msg="Error retriving MARC page")
            ms = BeautifulSoup(mr.content, features="lxml")
            print(f"Got MARC record - {mr.url}")
            with open(page_folder / "marc.html", "w") as marc_page:
                marc_page.write(ms.prettify())

            # save JPG
            jpeg_links = ds.find_all("a", string=re.compile(r'JPEG \(\d+kb\)'))
            jpeg_href = jpeg_links[-1]["href"]
            jpeg_url = f"https:{jpeg_href}" if jpeg_href.startswith("/") else jpeg_href
            time.sleep(1)
            jr = requests.get(jpeg_url)
            print(f"Got JPEG - {jr.url}")
            if jr.status_code != 200:
                print(jr.content)
                print(jr.url)
                sys.exit("Error retrieving jpeg")
            filename = jpeg_url.split("/")[-1]
            with open(page_folder / filename, "wb") as jpeg_file:
                jpeg_file.write(jr.content)
            with open("download/last_detail.txt", "w") as detail_count:
                detail_count.write(f"{i} - {id_num}")
            time.sleep(random.randint(3, 10))

        
        with open(f"download/last_list.txt", "w") as list_count:
            list_count.write(f"{i}")

def get_jpeg_url(soup):
    jpeg_links = soup.find_all("a", string=re.compile(r'JPEG \(\d+kb\)'))
    jpeg_href = jpeg_links[-1]["href"]
    jpeg_url = f"https:{jpeg_href}" if jpeg_href.startswith("/") else jpeg_href
    return jpeg_url


def missing_jpgs():
    res = []
    for d in DETAIL_FOLDER.iterdir():
        if d.is_dir():
            files = list(d.iterdir())
            if len(files) != 3:
                res.append(d.name)
    return res

def get_jpgs():
    missing = missing_jpgs()
    for folder in missing:
        detail = DETAIL_FOLDER / folder / "detail.html"
        soup = BeautifulSoup(detail.open().read())
        url = get_jpeg_url(soup)
        r = get_or_exit(url)
        img_file =  DETAIL_FOLDER / folder / f"{folder}.jpg"
        img_file.write_bytes(r.content)
        print(f"Wrote {img_file.absolute()}")
        time.sleep(3)

def rename_jpgs(dry_run=False):
    for d in DETAIL_FOLDER.iterdir():
        id_num = d.name
        jpg = list(d.glob("*.jpg"))[0]
        target = d / f"{id_num}.jpg"
        if dry_run:
            print(f"Rename {jpg.absolute()} to {target.absolute()}")
            c =  input("Continue? [Y/N]: ").upper()
            if c != "Y": break
        else:
            jpg.rename(target)
