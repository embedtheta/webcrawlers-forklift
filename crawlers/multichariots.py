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
    "https://multichariots.ca/product-category/scissor-lift/",

]


def _process_added_items(items):
    for item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            name = soup.find("h1",class_="product_title").text
        except Exception:
            name = ""
        product_details = soup.find_all('ul', class_="product_details")
        try:
            capacity = product_details[0].find_all('li')[5].text.split(':')[1].strip()
        except Exception:
            capacity = ""
        try:
            marque = product_details[0].find_all('li')[0].text.split(':')[1].strip()
        except Exception:
            marque = ""
        try:
            model = product_details[0].find_all('li')[1].text.split(':')[1].strip()
        except Exception:
            model = ""
        try:
            mat_1 = product_details[0].find_all('li')[6].text.split(':')[1].strip()
            mat_2 = product_details[0].find_all('li')[7].text.split(':')[1].strip()
            mat = f"{mat_1} {mat_2}"
        except Exception:
            mat = ""
        try:
            type_moteur = soup.find("td", text="Type moteur :").find_next("td").text.strip()
        except Exception:
            type_moteur = ""
        try:
            style_pneus = product_details[0].find_all('li')[4].text.split(':')[1].strip()
        except Exception:
            style_pneus = ""
        try:
            fourches = product_details[0].find_all('li')[9].text.split(':')[1].strip()
        except Exception:
            fourches = ""
        try:
            nourriture = product_details[0].find_all('li')[3].text.split(':')[1].strip()
        except Exception:
            nourriture = ""

        data = {
            "post_name": f"{name} {capacity} {marque}",
            "capacity": capacity,
            "marque": marque,
            "model": model,
            "mat": mat,
            "type_moteur": type_moteur,
            "style_pneus": style_pneus,
            "nourriture": nourriture,
            "fourches": fourches,
            "url": item,
        }
        request_("POST", API_ENDPOINT, data=data)


def _crawl_multichariots_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.find('a').get('href')
        for el in soup.find_all("h3", class_="product-title")
    ]
    return set(item_links)


def crawl_multichariots(request):
    if request.method == "POST":
        print("[multichariots] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_multichariots_category(category_link)
            )
        print(f"[multichariots] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "multichariots")
            return "No links were found on multichariots website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "multichariots", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for multichariots", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
