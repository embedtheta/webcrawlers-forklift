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
    "https://paindustrial.com/used-equipment/",

]


def _process_added_items(items):
    for item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            category = soup.find("td", text="Category").text.strip()
        except Exception:
            category = ""
        try:
            capacity = "".join(re.findall(r"\d+", soup.find("td", text="Capacity").find_next("td").text)) + "LB"
        except Exception:
            capacity = ""
        try:
            marque = soup.find("td", text="Make").find_next("td").text.strip()
        except Exception:
            marque = ""
        try:
            model = soup.find("td", text="Model").find_next("td").text.strip()
        except Exception:
            model = ""
        try:
            year = soup.find("td", text="Year").find_next("td").text.strip()
        except Exception:
            year = ""
        try:
            mat_1 = soup.find("td", text="Mast").find_next("td").text.strip()
            mat = f"{mat_1}"
        except Exception:
            mat = ""
        try:
            engine = soup.find("td", text="Engine").find_next("td").text.strip()
        except Exception:
            engine = ""
        try:
            forks = soup.find("td", text="Forks").find_next("td").text.strip()
        except Exception:
            forks = ""
        try:
            attachment = soup.find("td", text="Attachment").find_next("td").text
        except Exception:
            attachment = ""
        data = {
            "post_name": f"{category} {capacity} {marque} {model} {year}",
            "capacity": capacity,
            "marque": marque,
            "model": model,
            "year": year,
            "mat": mat,
            "engine": engine,
            "forks": forks,
            "attachment": attachment,
            "url": item,
        }
        request_("POST", API_ENDPOINT, data=data)


def _crawl_paindustrial_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.get('href')
        for el in soup.find_all("a", class_="woocommerce-LoopProduct-link")
    ]
    while True:
        next_page_link_el = soup.find("a", class_="next page-numbers")
        if next_page_link_el is not None:
            url = f"https://paindustrial.com{next_page_link_el.get('href')}"
            response_text = request_("GET", url).text
            soup = BeautifulSoup(response_text, "html.parser")
            item_links.extend([
                el.get("href")
                for el in soup.find_all("a", class_="woocommerce-LoopProduct-link")
            ])
        else:
            break
    return set(item_links)


def crawl_paindustrial(request):
    if request.method == "POST":
        print("[paindustrial] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_paindustrial_category(category_link)
            )
        print(f"[paindustrial] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "paindustrial")
            return "No links were found on paindustrial website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "paindustrial", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for paindustrial", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
