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
    "http://liftnorthamerica.com/equipment/",

]


def _process_added_items(items):
    for item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        soup_detilas = soup.select(".woocommerce-product-details__short-description ul li")
        if len(soup_detilas) > 0:
            try:
                name = soup.find("h1", class_="product_title").text
            except Exception:
                name = ""
            #print(soup_detilas)
            try:
                capacity = soup_detilas[4].text.split(":")[1]
            except Exception:
                capacity = ""
            try:
                marque = soup_detilas[1].text.split(':')[1]
            except Exception:
                marque = ""
            try:
                model = soup_detilas[0].text.split(":")[1]
            except Exception:
                model = ""
            try:
                mat_2 = soup_detilas[7].text.split(":")[1]
                mat_1 = soup_detilas[8].text.split(":")[1]
                mat = f"{mat_2}-{mat_1}"

            except Exception:
                mat = ""
            try:
                year = soup_detilas[2].text.split(":")[1]
            except Exception:
                year = ""
            try:
                fuel = soup_detilas[6].text.split(":")[1].strip()
            except Exception:
                fuel = ""
            try:
                types = soup_detilas[5].text.split(":")[1].strip()
            except Exception:
                types = ""
            try:
                truck_types = soup_detilas[1].text.split(":")[1].strip()
            except Exception:
                truck_types = ""
            data = {
                "post_name": f"{name} {capacity} {marque} {year}",
                "capacity": capacity,
                "marque": marque,
                "model": model,
                "mat": mat,
                "annee": year,
                "fuel": fuel,
                "type": types,
                "truck_types": truck_types,
                "url": item,
            }
            request_("POST", API_ENDPOINT, data=data)


def _crawl_liftnorthamerica_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.get('href')
        for el in soup.find_all("h4", class_="product-title")
    ]
    while True:
        next_page_link_el = soup.find("a", class_="next page-numbers")
        if next_page_link_el is not None:
            url = next_page_link_el["href"]
            response_text = request_("GET", url).text
            soup = BeautifulSoup(response_text, "html.parser")
            item_links.extend([
                el.get("href")
                for el in soup.find_all("h4", class_="product-title")
            ])
        else:
            break
    return set(item_links)


def crawl_liftnorthamerica(request):
    if request.method == "POST":
        print("[liftnorthamerica] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_liftnorthamerica_category(category_link)
            )
        print(f"[liftnorthamerica] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "liftnorthamerica")
            return "No links were found on liftnorthamerica website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "liftnorthamerica", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for liftnorthamerica", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
