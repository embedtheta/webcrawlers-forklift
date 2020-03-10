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
    "http://canada.crown.com/used-inventory/electric-counter-balance",
    "http://canada.crown.com/used-inventory/internal-combustion-super-elastic-tire",
    "http://canada.crown.com/used-inventory/internal-combustion-cushion-tire",
    "http://canada.crown.com/used-inventory/pallet-trucks-stackers",
    "http://canada.crown.com/used-inventory/narrow-aisle-very-narrow-aisle"

]
item_links_all = []
main_link = "http://canada.crown.com"


def _process_added_items(items):
    for item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            capacity = soup.find("div", text="Capacity:").find_next("div").text + "LB"
        except Exception:
            capacity = ""
        try:
            marque = soup.find("div", text="Make:").find_next("div").text
        except Exception:
            marque = ""
        try:
            model = soup.find("div", text="Model:").find_next("div").text
        except Exception:
            model = ""
        try:
            year = soup.find("div", text="Year:").find_next("div").text
        except Exception:
            year = ""
        try:
            type_s = soup.find("div", text="Type:").find_next("div").text
        except Exception:
            type_s = ""
        try:
            tire = soup.find("div", text="Upright:").find_next("div").text
        except Exception:
            tire = ""
        try:
            hours = soup.find("div", text="Hours:Hours:").find_next("div").text
        except Exception:
            hours = ""
        data = {
            "post_name": f"{type_s} {capacity} {marque} {year}",
            "capacity": capacity,
            "marque": marque,
            "model": model,
            "year": year,
            "type": type_s,
            "tire": tire,
            "hours": hours,
            "url": item,
        }

        request_("POST", API_ENDPOINT, data=data)


def _crawl_canadacrown_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    for el in soup.find_all("div", class_="image"):
        try:
            url = el.find('a').get('href')
            base_url = f"{main_link}{url}"
            item_links_all.append(base_url)
        except Exception:
            pass
    return set(item_links_all)


def crawl_canadacrown(request):
    if request.method == "POST":
        print("[canadacrown] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_canadacrown_category(category_link)
            )
        print(f"[canadacrown] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "canadacrown")
            return "No links were found on canadacrown website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "canadacrown", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for canadacrown", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
