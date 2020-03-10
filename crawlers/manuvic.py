import os
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from google.cloud import firestore, storage

from utils import (
    request_,
    save_photos_to_bucket,
    delete_photos_from_bucket,
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


def _format_item_link(link):
    urlparse_result = urlparse(link)
    path = urlparse_result.path
    return path[1:].replace(".html", "")


def _get_images(soup: BeautifulSoup):
    initial_image_link = soup.find("meta", {"property": "og:image"}).get("content")
    if initial_image_link != "https://www.manuvic.com/pub/media/catalog/product":
        all_images = [initial_image_link]
        i = 2
        while True:
            next_image_link = initial_image_link.replace("-1.jpg", f"-{i}.jpg")
            try:
                r = request_("GET", next_image_link, timeout=2)
                r.raise_for_status()
                all_images.append(next_image_link)
                i += 1
            except requests.exceptions.RequestException:
                break
        return all_images
    return []


def _process_added_items(storage_client, items):
    print(f"[manuvic] Got {len(items)} added links")
    for item in items:
        print(f"[manuvic] Processing added link {item}")
        link_data = []
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        for page_title in soup.find_all("h1", class_="page-title"):
            na = re.sub(r"[\n\t]*", "", page_title.text)
        for description in soup.find_all("div", id="product.info.descriptionmod"):
            for data in description.find_all("span", class_="infoValue"):
                data_new = re.sub(r"[\n\t\s]*", "", data.text)
                link_data.append(data_new)
        photo_links = _get_images(soup)
        print(f"[manuvic] Saving {len(photo_links)} photos to the bucket for {item}")
        item_path = _format_item_link(item)
        blob_path = f"manuvic/photos/{item_path}"
        save_photos_to_bucket(
            storage_client,
            blob_path,
            photo_links,
            BUCKET_NAME
        )
        try:
            capacity = link_data[2]
        except IndexError:
            capacity = ""
        try:
            marque = link_data[3]
        except IndexError:
            marque = ""
        try:
            model = link_data[4]
        except IndexError:
            model = ""
        try:
            mat = link_data[8]
        except IndexError:
            mat = ""
        try:
            year = link_data[13]
        except IndexError:
            year = ""
        print(f"[manuvic] Posting data about the {item} to forklift.news website")
        request_(
            "POST",
            API_ENDPOINT,
            data={
                "post_name": f"{na} {capacity} {marque} {year}",
                "capacity": capacity,
                "marque": marque,
                "model": model,
                "mat": mat,
                "annee": year,
                "url": item,
            })


def crawl_manuvic(request):
    if request.method == "POST":
        print("[manuvic] Started crawling website")
        response_text = request_(
            "GET",
            "https://www.manuvic.com/produits/chariots-elevateurs.html?cat=116&product_list_limit=100"
        ).text

        soup = BeautifulSoup(response_text, "html.parser")
        item_links = [
            el.get("href")
            for el in soup.find_all("a", class_="product photo product-item-photo")
        ]

        db = firestore.Client()
        storage_client = storage.Client()

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "manuvic")
            return "No links were found on manuvic website"

        comparison_result = add_and_compare_new_items(db, "manuvic", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(storage_client, added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for manuvic", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
