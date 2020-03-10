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

CATEGORIES = [
    "https://www.komatsuforklift.com/Stockton/Used-Forklifts",
    "https://www.komatsuforklift.com/Ontario/Used-Forklifts",
    "https://www.komatsuforklift.com/Oakland/Used-Forklifts",
    "https://www.komatsuforklift.com/LosAngeles/Used-Forklifts",
    "https://www.komatsuforklift.com/Fresno/Used-Forklifts",
    "https://www.komatsuforklift.com/ChicagoNorth/Used-Forklifts",
    "https://www.komatsuforklift.com/Chicago/Used-Forklifts",
    "https://www.komatsuforklift.com/Atlanta/Used-Forklifts"
]


def _process_added_items(items):
    for url, item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        soup_main = soup.find('div', {"id": item})
        try:
            name = soup_main.find("div", class_="lbHeader").text.strip()
        except Exception:
            name = ""
        try:
            capacity = soup.find("td", text="Capacity:").find_next("td").text + "LB"
        except Exception:
            capacity = ""
        try:
            marque = soup.find("td", text="Mfr:").find_next("td").text
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
            type_s = soup.find("td", text="Fuel Type:").find_next("td").text
        except Exception:
            type_s = ""
        try:
            types = soup.find("td", text="Type:").find_next("td").text
        except Exception:
            types = ""
        try:
            description = soup.find("td", text="Description:").find_next("td").text
        except Exception:
            description = ""
        data = {
            "post_name": f"{name}",
            "capacity": capacity,
            "marque": marque,
            "model": model,
            "year": year,
            "mat": mat,
            "type": type_s,
            "types": types,
            "description": description,
            "url": item,
        }
        API_ENDPOINT = ""
        request_("POST", API_ENDPOINT, data=data)


def _crawl_komatsuforklift_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        (category_link, el.get('data-reveal-id'))
        for el in soup.find_all("a", class_="img")
    ]
    while True:
        next_page_link_el = soup.find("a", text="next »")
        if next_page_link_el is not None:
            response_text = request_("GET", next_page_link_el["href"]).text
            soup = BeautifulSoup(response_text, "html.parser")
            item_links.extend([
                (next_page_link_el["href"], el.get("data-reveal-id"))
                for el in soup.find_all("a", class_="img")
            ])
        else:
            break
    return set(item_links)


def crawl_komatsuforklift(request):
    if request.method == "POST":
        print("[komatsuforklift] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_komatsuforklift_category(category_link)
            )
        print(f"[komatsuforklift] Got {len(item_links)} item links")
        final_links = []
        for url, item in item_links:
            final_links.append(item)

        if not final_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "komatsuforklift")
            return "No links were found on komatsuforklift website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "komatsuforklift", final_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            final_items.extend([(url, i)for item in added_items for url, i in item_links if item == i])
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for komatsuforklift", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
