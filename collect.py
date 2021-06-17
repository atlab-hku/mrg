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


def get_results():
    last_list = int(open("download/last_list.txt").read().strip())
    detail_folder = pathlib.Path("download/detail")
    
    for i in range(last_list, 587):
        params = {
            "q": "mrg",
            "sp": i
        }
        
        r = requests.get(base_url, params=params)
        print(f"Got list page - {r.url}")
        if r.status_code != 200:
            print(r.content)
            print(r.url)
            sys.exit("error retrieving list page")
        soup = BeautifulSoup(r.content, features="lxml")
    
        with open(f"download/list/{i}.html", "w") as list_page:
            list_page.write(soup.prettify())
        # get list of links to detail pages
        links = soup.select("div.result_item > p > a")
        for link in links:
            # visit each link, save detail page, save MARC record, save JPG
            id_num = link["href"].split("/")[-2]
            dr = requests.get(link["href"])
            print(f"Got detail page {dr.url}")
            if dr.status_code != 200:
                print(dr.content)
                print(dr.url)
                print("Error retrieving detail page")
            ds = BeautifulSoup(dr.content, features="lxml")

            # save detail page
            page_folder = detail_folder / id_num
            page_folder.mkdir()
            with open(page_folder / "detail.html", "w") as detail_page:
                detail_page.write(ds.prettify())

            # save MARC record
            marc_url = ds.select("a#item_marc")[0]["href"]
            mr = requests.get(marc_url)
            ms = BeautifulSoup(mr.content, features="lxml")
            print(f"Got MARC record - {mr.url}")
            if mr.status_code != 200:
                print(mr.content)
                print(mr.url)
                sys.exit("Error retrieving marc page")
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
            time.sleep(2)

        
        with open(f"download/last_list.txt", "w") as list_count:
            list_count.write(f"{i}")

        time.sleep(2)





