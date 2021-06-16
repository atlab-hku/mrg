import requests
import time

from bs4 import BeautifulSoup

base_url = "https://www.loc.gov/pictures/search/"

params = {
    "q": "mrg",
    "sp": 1
    }


def get_results():
    page = 1

    for i in range(1, 587):
        r = requests.get(base_url, params=params)
