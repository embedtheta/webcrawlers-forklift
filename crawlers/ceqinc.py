import os
import re

from bs4 import BeautifulSoup
from google.cloud import firestore

from utils import add_and_compare_new_items, send_email, format_links_modified, send_warning_email, request_

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECEIVER_EMAILS_RAW = os.getenv("RECEIVER_EMAILS")
if RECEIVER_EMAILS_RAW is not None:
    RECEIVER_EMAILS = RECEIVER_EMAILS_RAW.split(",")


def _process_added_items(items):
    print(f"[ceqinc] Got {len(items)} added links")
    for item in items:
        print(f"[ceqinc] Processing added link {item}")
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            name = soup.find("span", text="Type d'équipement").find_next("strong").text
        except Exception:
            name = ""
        try:
            capacity = "".join(re.findall(r"\d+", soup.find("span", text="Capacité").find_next("strong").text)) + "LB"
        except Exception:
            capacity = ""
        try:
            marque = soup.find("span", text="Marque").find_next("strong").text
        except Exception:
            marque = ""
        try:
            model = soup.find("span", text="Modèle").find_next("strong").text
        except Exception:
            model = ""
        try:
            mat_1 = soup.find("span", text="Hauteur du mât (abaissé)").find_next("strong").text
            mat_2 = soup.find("span", text="Hauteur du mât (élévation)").find_next("strong").text
            mat = f"abaissé: {mat_1}, élévation: {mat_2}"
        except Exception:
            mat = ""
        try:
            year = soup.find("span", text="Année").find_next("strong").text
        except Exception:
            year = ""
        print(f"[ceqinc] Posting data about the {item} to forklift.news website")
        request_(
            "POST",
            "",
            data={
                "post_name": f"{name} {capacity} {marque} {year}",
                "capacity": capacity,
                "marque": marque,
                "model": model,
                "mat": mat,
                "annee": year,
                "url": item,
            })


def _crawl_ceqinc():
    link = "https://www.ceqinc.ca/inventaire?p={page}&s=1&condition=usage"
    page = 1
    response_text = request_("GET", link.format(page=page)).text
    soup = BeautifulSoup(response_text, "html.parser")
    items = [
        e.a.get("href")
        for e in soup.find_all("div", class_="car-content")
    ]
    while True:
        next_page = soup.find("ul", class_="pagination").find("a", text="»")
        if next_page is None:
            break
        page += 1
        response_text = request_("GET", link.format(page=page)).text
        soup = BeautifulSoup(response_text, "html.parser")
        items.extend([
            e.a.get("href")
            for e in soup.find_all("div", class_="car-content")
        ])
    items = [
        "https://www.ceqinc.ca" + item
        for item in items
    ]
    return items


def crawl_ceqinc(request):
    if request.method == "POST":
        print("[ceqinc] Started crawling website")
        items = _crawl_ceqinc()
        print(f"[ceqinc] Got {len(items)} items")

        if not items:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "ceqinc")
            return "No links were found on ceqinc website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "ceqinc", items)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for ceqinc", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
