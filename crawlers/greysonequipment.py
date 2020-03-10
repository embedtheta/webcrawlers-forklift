import os
import re

from bs4 import BeautifulSoup
from google.cloud import firestore

from utils import request_, add_and_compare_new_items, send_email, format_links_modified, send_warning_email

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECEIVER_EMAILS_RAW = os.getenv("RECEIVER_EMAILS")
if RECEIVER_EMAILS_RAW is not None:
    RECEIVER_EMAILS = RECEIVER_EMAILS_RAW.split(",")

API_ENDPOINT = ""
CATEGORIES = [
    "https://www.greysonequipment.com/our-inventory",

]


def _process_added_items(items):
    for item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            name = soup.find("h2", class_="spec-list__heading").text.strip()
        except Exception:
            name = ""
        soup_main = soup.find_all("li", class_="spec-list__item")
        try:
            year = soup_main[1].text.split(":")[1].strip()
        except Exception:
            year = ""
        try:
            manufacturer = soup_main[2].text.split(":")[1].strip()
        except Exception:
            manufacturer = ""
        try:
            model = soup_main[3].text.split(":")[1].strip()
        except Exception:
            model = ""
        try:
            terrain = soup_main[4].text.split(":")[1].strip()
        except Exception:
            terrain = ""
        try:
            height = soup_main[5].text.split(":")[1].strip()
        except Exception:
            height = ""
        try:
            fuel = soup_main[6].text.split(":")[1].strip()
        except Exception:
            fuel = ""
        try:
            types = soup_main[7].text.split(":")[1].strip()
        except Exception:
            types = ""

        data = {
            "post_name": f"{name}",
            "marque": manufacturer,
            "model": model,
            "year": year,
            "terrain": terrain,
            "height": height,
            "fuel": fuel,
            "types":types,
            "url": item,
        }
        request_("POST", API_ENDPOINT, data=data)


def _crawl_greysonequipment_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        f"https://www.greysonequipment.com{el.get('href')}"
        for el in soup.find_all("a", class_="product-list__link")
    ]
    return set(item_links)


def crawl_greysonequipment(request):
    if request.method == "POST":
        print("[greysonequipment] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_greysonequipment_category(category_link)
            )
        print(f"[greysonequipment] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "greysonequipment")
            return "No links were found on greysonequipment website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "greysonequipment", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for greysonequipment", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
