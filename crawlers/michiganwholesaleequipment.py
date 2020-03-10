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
CATEGORIES = ["https://www.michiganwholesaleequipment.com/equipment/equipment_type/forklift-1"]


def _process_added_items(items):
    for item in items:
        url_link = f"https://www.michiganwholesaleequipment.com{item}"
        source = request_("GET", url_link).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            name = soup.find("section", {"id": "block-zurb-foundation-page-title"}).text.strip()
        except Exception:
            name = ""
        try:
            capacity = soup.find("div", text="Capacity").find_next("div").text
        except Exception:
            capacity = ""
        try:
            model = soup.find("div", text="Equipment Model").find_next("div").text
        except Exception:
            model = ""
        try:
            hours = soup.find("div", text="Hours").find_next("div").text
        except Exception:
            hours = ""
        try:
            mat = soup.find("div", text="Mast").find_next("div").text
        except Exception:
            mat = ""
        try:
            type_s = soup.find("div", text="Fuel Type").find_next("div").text
        except Exception:
            type_s = ""
        try:
            tire = soup.find("div", text="Equipment Type").find_next("div").text
        except Exception:
            tire = ""
        try:
            year = soup.find("div", text="Year").find_next("div").text
        except Exception:
            year = ""
        data = {
            "post_name": f"{name}",
            "capacity": capacity,
            "hours": hours,
            "model": model,
            "mat": mat,
            "type": type_s,
            "tire": tire,
            "year": year,
            "url": url_link,
        }
        request_("POST", API_ENDPOINT, data=data)


def _crawl_michiganwholesaleequipment_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    soup_main = soup.find('div', class_="item-list")
    item_links = [
        el.find('a').get('href')
        for el in soup_main.find_all("div", class_="views-field-title")
    ]
    while True:
        next_page_link_el = soup.find("ul", class_="js-pager__items")
        sub_url = next_page_link_el.find("a").get("href")
        sub_text = next_page_link_el.find("span", class_="visually-hidden").text
        if sub_url is not None and sub_text == "Next page":
            url = f"https://www.michiganwholesaleequipment.com{sub_url}"
            response_text = request_("GET", url).text
            soup = BeautifulSoup(response_text, "html.parser")
            soup_main = soup.find('div', class_="item-list")
            item_links.extend([
                el.find('a').get('href')
                for el in soup_main.find_all("div", class_="views-field-title")
            ])
        else:
            break
    return set(item_links)


def crawl_michiganwholesaleequipment(request):
    if request.method == "POST":
        print("[michiganwholesaleequipment] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_michiganwholesaleequipment_category(category_link)
            )
        print(f"[michiganwholesaleequipment] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "michiganwholesaleequipment")
            return "No links were found on michiganwholesaleequipment website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "michiganwholesaleequipment", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for michiganwholesaleequipment", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
