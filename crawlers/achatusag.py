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
    "https://www.liftatout.com/achat-usag",
]


def _process_added_items(items):
    for item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        display_title = soup.find("p", class_="font_2")
        try:
            name = display_title.text
        except Exception:
            name = ""
        display_all = soup.find_all("p", class_="font_9")
        try:
            capacity = display_all[15].text
        except Exception:
            capacity = ""
        try:
            model = display_all[12].text
        except Exception:
            model = ""
        try:
            mat = display_all[18].text

        except Exception:
            mat = ""
        try:
            year = display_all[12].text
        except Exception:
            year = ""
        data = {
            "post_name": f"{name} {capacity} {year}",
            "capacity": capacity,
            "model": model,
            "mat": mat,
            "annee": year,
            "url": item,
        }
        request_("POST", API_ENDPOINT, data=data)


def _crawl_achatusag_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.find('a').get('href')
        for el in soup.find_all("div", class_="flex_display")
    ]
    return set(item_links)


def _crawl_achatusag_category_2(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.get('href')
        for el in soup.find_all("a", class_="b2link")
    ]
    return set(item_links)


def crawl_achatusag(request):
    if request.method == "POST":
        print("[achatusag] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_achatusag_category_2(category_link)
            )
        item_links_subcategory = []
        for category_link in item_links:
            item_links_subcategory.extend(
                _crawl_achatusag_category(category_link)
            )
        print(f"[achatusag] Got {len(item_links_subcategory)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "achatusag")
            return "No links were found on achatusag website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "achatusag", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for achatusag", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
