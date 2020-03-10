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

BUCKET_NAME = os.getenv("BUCKET_NAME")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECEIVER_EMAILS_RAW = os.getenv("RECEIVER_EMAILS")
if RECEIVER_EMAILS_RAW is not None:
    RECEIVER_EMAILS = RECEIVER_EMAILS_RAW.split(",")
API_ENDPOINT = ""
BASE_URL = "https://www.gregorypoolelift.com"


def _parse_item(link):
    print(f"[southeastforklifts] Processing added link {link}")
    source = request_("GET", link).text
    soup = BeautifulSoup(source, "html.parser")

    try:
        name = soup.find("h1").find("span").text
    except Exception:
        name = ""
    try:
        capacity = "".join(
            re.findall(
                r"\d+", soup.find("span", text="Capacity:").find_next("i").text)) + "LB"
    except Exception:
        capacity = ""
    try:
        marque = soup.find("span", text="Manufacturer:").find_next("i").text
    except Exception:
        marque = ""
    try:
        model = soup.find("span", text="Model:").find_next("i").text
    except Exception:
        model = ""
    try:
        mat_1, mat_2 = re.findall(r"\d+", soup.find("span", text="Mast:").find_next("i").text)
        mat = f"{mat_1}/{mat_2} triple"
    except Exception:
        mat = ""
    try:
        year = soup.find("span", text="Year:").find_next("i").text
    except Exception:
        year = ""
    return {
        "name": name,
        "capacity": capacity,
        "marque": marque,
        "year": year,
        "model": model,
        "annee": year,
        "mat": mat,
    }


def _process_added_items(items):
    print(f"[southeastforklifts] Got {len(items)} added links")
    for item in items:
        print(f"[southeastforklifts] Posting data about the {item} to forklift.news website")
        item_data = _parse_item(item)
        request_(
            "POST",
            API_ENDPOINT,
            data={
                "post_name": f"{item_data['name']} {item_data['capacity']} {item_data['marque']} {item_data['year']}",
                "capacity": item_data['capacity'],
                "marque": item_data['marque'],
                "model": item_data['model'],
                "mat": item_data['mat'],
                "annee": item_data['year'],
                "url": item,
            })


def crawl_southeastforklifts_pages():
    results_url = "https://www.gregorypoolelift.com/used-equipment-inventory/results"
    url = "https://www.gregorypoolelift.com/used-equipment-inventory/results?page=1&limit=12"
    item_links = []

    while True:
        response_text = request_("GET", url).text
        soup = BeautifulSoup(response_text, "html.parser")
        parent_elements = soup.find_all("div", class_="product-panel")
        for e in parent_elements:
            link = e.find("a")
            if link is not None:
                item_links.append(BASE_URL + link.get("href"))
        parent_element_next_link = soup.find("li", class_="pagination-next")
        if parent_element_next_link is None:
            break
        next_link = parent_element_next_link.find("a")
        if next_link is not None:
            next_link = next_link.get("href")
        else:
            break
        url = results_url + next_link
    return item_links


def crawl_southeastforklifts(request):
    if request.method == "POST":
        print("[southeastforklifts] Started crawling website")
        item_links = crawl_southeastforklifts_pages()

        db = firestore.Client()

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "southeastforklifts")
            return "No links were found on southeastforklifts website"

        comparison_result = add_and_compare_new_items(db, "southeastforklifts", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for southeastforklifts",
                       email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
