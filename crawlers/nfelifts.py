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
    "https://www.nfe-lifts.com/types/3-wheel-forklift/",
    "https://www.nfe-lifts.com/types/4-wheel-forklift/",
    "https://www.nfe-lifts.com/types/explosion-proof-forklift/",
    "https://www.nfe-lifts.com/types/ex-pallet-truck-2/",
    "https://www.nfe-lifts.com/types/narrow-aisle-forklift/",
    "https://www.nfe-lifts.com/types/pallet-trucks/",
    "https://www.nfe-lifts.com/types/rough-terrain-forklift/",
    "https://www.nfe-lifts.com/types/stacker-truck/",
    "https://www.nfe-lifts.com/types/very-narrow-aisle-forklift/",

]


def _process_added_items(items):
    for item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            name = soup.find("div", class_="su-service-title").text.strip()
        except Exception:
            name = ""
        try:
            capacity = soup.find("td", text="Capacity:").find_next("td").text + "LB"
        except Exception:
            capacity = ""
        try:
            marque = soup.find("td", text="Manufacturer:").find_next("td").text
        except Exception:
            marque = ""
        try:
            model = soup.find("td", text="Model #:").find_next("td").text
        except Exception:
            model = ""
        try:
            year = soup.find("td", text="Year:").find_next("td").text
        except Exception:
            year = ""
        try:
            mat = soup.find("td", text="Mast:").find_next("td").text
        except Exception:
            mat = ""
        try:
            type_s = soup.find("td", text="Type:").find_next("td").text
        except Exception:
            type_s = ""
        try:
            tire = soup.find("td", text="Tire:").find_next("td").text
        except Exception:
            tire = ""
        try:
            condition = soup.find("td", text="Condition:").find_next("td").text
        except Exception:
            condition = ""
        data = {
            "post_name": f"{name}",
            "capacity": capacity,
            "marque": marque,
            "model": model,
            "year": year,
            "mat": mat,
            "type": type_s,
            "tire": tire,
            "condition": condition,
            "url": item,
        }
        request_("POST", API_ENDPOINT, data=data)


def _crawl_nfelifts_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.get('href')
        for el in soup.find_all("a", class_="more-link")
    ]
    return set(item_links)


def crawl_nfelifts(request):
    if request.method == "POST":
        print("[nfelifts] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_nfelifts_category(category_link)
            )
        print(f"[nfelifts] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "nfelifts")
            return "No links were found on nfelifts website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "nfelifts", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for nfelifts", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
