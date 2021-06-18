from os import error
import pathlib
import requests
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
    "User-Agent": "KotSF crawler - Report abuse to admin@kotsf.com"
}

def get_or_exit(url, params=None, err_msg="error retrieving page"):

    r = requests.get(url, params=params, headers=HEADERS)
    if r.status_code != 200:
        with open("download/err.html", "w") as err_page:
            err_page.write(r.content)
        print(r.url)
        sys.exit(err_msg)
    return r


def get_results():
    last_list = int(open("download/last_list.txt").read().strip())
    detail_folder = pathlib.Path("download/detail")

    visited_details = set([d.name for d in detail_folder.iterdir() if d.is_dir()])
    
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
            page_folder = detail_folder / id_num
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
            jpeg_url = f"https:{jpeg_href}"
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
            time.sleep(3)

        
        with open(f"download/last_list.txt", "w") as list_count:
            list_count.write(f"{i}")






