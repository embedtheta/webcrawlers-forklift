import os
import re

from bs4 import BeautifulSoup
from google.cloud import firestore

from utils import (
    request_,
    format_links_modified,
    send_email,
    add_and_compare_new_items,
    send_warning_email
)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECEIVER_EMAILS_RAW = os.getenv("RECEIVER_EMAILS")
if RECEIVER_EMAILS_RAW is not None:
    RECEIVER_EMAILS = RECEIVER_EMAILS_RAW.split(",")


def _process_added_items(items):
    print(f"[almachinery] Got {len(items)} added links")
    for item in items:
        print(f"[almachinery] Processing added link {item}")
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            name = soup.find("p", class_="category-title").text
        except Exception:
            name = ""
        try:
            capacity = soup.find("span", text="Capacité").find_next("span").text + "LB"
        except Exception:
            capacity = ""
        try:
            marque = soup.find("span", text="Marque").find_next("span").find("img").get("alt")
        except Exception:
            marque = ""
        try:
            model = soup.find("span", text="No de série").find_next("span").text
        except Exception:
            model = ""
        try:
            mat_1 = soup.find("span", text="Type de mât").find_next("span").text
            mat_2 = soup.find("span", text="Hauteur du mât").find_next("span").text
            mat = f"{mat_1},{mat_2}"
        except Exception:
            mat = ""
        try:
            year = soup.find("span", text="Année").find_next("span").text
        except Exception:
            year = ""
        print(f"[almachinery] Posting data about the {item} to forklift.news website")
        request_(
            "POST",
            "URL",
            data={
                "post_name": f"{name} {capacity} {marque} {year}",
                "capacity": capacity,
                "marque": marque,
                "model": model,
                "mat": mat,
                "annee": year,
                "url": item,
            })


def _crawl_almachinery():
    api_link = "https://www.a1machinery.com/fr/inventaire/api?capacity_from=0&capacity_to=55000&p={page}&referer=/fr/Produits?capacity_from=0&capacity_to=55000&p={page}"
    initial_page = 1
    response = request_("GET", api_link.format(page=initial_page))
    response_json = response.json()
    pages = response_json.get("pages")
    items = [
        {"link": item["url"]}
        for item in response_json.get("items")
    ]

    for page in range(2, pages + 1):
        response = request_("GET", api_link.format(page=page))
        response_json = response.json()
        items.extend([
            {"link": item["url"]}
            for item in response_json.get("items")
        ])

    items = [
        f"https://www.a1machinery.com{item['link']}"
        for item in items
    ]

    return items


def crawl_a1machinery(request):
    if request.method == "POST":
        print("[a1machinery] Started crawling website")

        items = _crawl_almachinery()
        print(f"[a1machinery] Got {len(items)} items")

        if not items:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "a1machinery")
            return "No links were found on a1machinery website"

        db = firestore.Client()
        comparison_result = add_and_compare_new_items(db, "a1machinery", items)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for a1machinery", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
