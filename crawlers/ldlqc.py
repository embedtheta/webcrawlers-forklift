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
    "https://www.ldl.qc.ca/produits/equipements-usages/",
]


def _process_added_items(items):
    for item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            name = soup.find("h1", class_="post-title").text
        except Exception:
            name = ""

        soup_detilas = soup.select(".specification li")
        try:
            capacity = soup_detilas[5].text.split(":")[1]
        except Exception:
            capacity = ""

        try:
            marque = soup_detilas[1].text.split(':')[1]
        except Exception:
            marque = ""
        try:
            model = soup_detilas[2].text.split(":")[1]
        except Exception:
            model = ""
        try:
            mat = soup_detilas[9].text.split(":")[1]

        except Exception:
            mat = ""
        try:
            year = soup_detilas[3].text.split(":")[1]
        except Exception:
            year = ""
        data = {
            "post_name": f"{name} {capacity} {marque} {year}",
            "capacity": capacity,
            "marque": marque,
            "model": model,
            "mat": mat,
            "annee": year,
            "url": item,
        }
        request_("POST", API_ENDPOINT, data=data)


def _crawl_ldlqc_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.find('a').get("href")
        for el in soup.find_all("div", class_="title")
    ]
    while True:
        next_page_link_el = soup.find("a", class_="next")
        if next_page_link_el is not None:
            response_text = request_("GET", next_page_link_el["href"]).text
            soup = BeautifulSoup(response_text, "html.parser")
            item_links.extend([
                el.find('a').get("href")
                for el in soup.find_all("div", class_="title")
            ])
        else:
            break
    return set(item_links)


def crawl_ldlqc(request):
    if request.method == "POST":
        print("[ldlqc] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_ldlqc_category(category_link)
            )
        print(f"[ldlqc] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "ldlqc")
            return "No links were found on ldlqc website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "ldlqc", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for ldlqc", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
