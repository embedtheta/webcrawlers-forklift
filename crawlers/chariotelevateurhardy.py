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
    "https://chariotelevateurhardy.ca/category/chariot-elevateur/",
    "https://chariotelevateurhardy.ca/category/transpalette/",

]


def _process_added_items(items):
    for item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            capacity = soup.find("td", text="Capacité:").find_next("td").text
        except Exception:
            capacity = ""
        try:
            marque = soup.find("h1", class_="entry-title").text.split('')[0]
        except Exception:
            marque = ""
        try:
            model = soup.find("h1", class_="entry-title").text.split('')[1]
        except Exception:
            model = ""
        try:
            mat_1 = soup.find("td", text="Mât:").find_next("td").text
            mat_2 = soup.find("td", text="Hauteur mât :").find_next("td").text
            mat = f"{mat_1},{mat_2}"
        except Exception:
            mat = ""
        try:
            year = soup.find("span", text="Année:").find_next("td").text
        except Exception:
            year = ""
        data = {
            "post_name": f"{capacity} {marque} {year}",
            "capacity": capacity,
            "marque": marque,
            "model": model,
            "mat": mat,
            "annee": year,
            "url": item,
        }
        request_("POST", API_ENDPOINT, data=data)


def _crawl_chariotelevateurhardy_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.find('a').get('href')
        for el in soup.find_all("h2", class_="entry-title")
    ]
    return set(item_links)


def crawl_chariotelevateurhardy(request):
    if request.method == "POST":
        print("[achatusag] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_chariotelevateurhardy_category(category_link)
            )
        print(f"[chariotelevateurhardy] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "chariotelevateurhardy")
            return "No links were found on chariotelevateurhardy website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "chariotelevateurhardy", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for chariotelevateurhardy", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
