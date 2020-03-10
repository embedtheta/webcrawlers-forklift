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
    "https://www.tmhnc.com/used-equipment/topic/used-ic-cushion",
    "https://www.tmhnc.com/used-equipment/topic/used-ic-pneumatic",
    "https://www.tmhnc.com/used-equipment/topic/used-electric",
    "https://www.tmhnc.com/used-equipment/topic/stand-up",
    "https://www.tmhnc.com/used-equipment/topic/electric-pallet-jacks-stackers",

]


def _process_added_items(items):
    for item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            name = soup.find("div", class_="section post-header").text.strip()
        except Exception:
            name = ""
        try:
            capacity = soup.find("td", text="Base Capacity (lbs.)").find_next("td").text + "LB"
        except Exception:
            capacity = ""
        try:
            marque = soup.find("td", text="Make:").find_next("td").text
        except Exception:
            marque = ""
        try:
            model = soup.find("td", text="Model:").find_next("td").text
        except Exception:
            model = ""
        try:
            year = soup.find("td", text="Year:").find_next("td").text
        except Exception:
            year = ""
        try:
            mat_1 = soup.find("td", text="Mast Type:").find_next("td").text
            mat_2 = soup.find("td", text="Mast Type:").find_next("td").text
            mat_3 = soup.find("td", text="Mast Type:").find_next("td").text
            mat = f"{mat_1}/{mat_2}/{mat_3}"
        except Exception:
            mat = ""
        try:
            type_s = soup.find("td", text="Machine Type:").find_next("td").text
        except Exception:
            type_s = ""
        try:
            tire = soup.find("td", text="Tires:").find_next("td").text
        except Exception:
            tire = ""
        try:
            hours = soup.find("td", text="Hours:").find_next("td").text
        except Exception:
            hours = ""
        data = {
            "post_name": f"{name}",
            "capacity": capacity,
            "marque": marque,
            "model": model,
            "year": year,
            "mat": mat,
            "type": type_s,
            "tire": tire,
            "hours": hours,
            "url": item,
        }
       
        request_("POST", API_ENDPOINT, data=data)


def _crawl_tmhnc_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.get('href')
        for el in soup.find_all("a", class_="more-link")
    ]
    return set(item_links)


def crawl_tmhnc(request):
    if request.method == "POST":
        print("[tmhnc] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_tmhnc_category(category_link)
            )
        print(f"[tmhnc] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "tmhnc")
            return "No links were found on nfelifts website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "tmhnc", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for tmhnc", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
