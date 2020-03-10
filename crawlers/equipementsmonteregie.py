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
    "https://www.equipementsmonteregie.com/index.php/site/chariots-elevateurs-usages",

]


def _process_added_items(items):
    for item in items:
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            capacity = soup.find("td", text="Capacité :").find_next("td").text.strip() + "LB"
        except Exception:
            capacity = ""
        try:
            marque = soup.find("span", class_="marque").text.strip()
        except Exception:
            marque = ""
        try:
            model = soup.find("span", class_="modele").text.strip()
        except Exception:
            model = ""
        try:
            mat_1 = soup.find("td", text="Mât :").find_next("td").text.strip()
            mat = f"{mat_1}"
        except Exception:
            mat = ""
        try:
            year = soup.find("td", text="Année :").find_next("td").text.strip()
        except Exception:
            year = ""
        try:
            heures = soup.find("td", text="Heures :").find_next("td").text.strip()
        except Exception:
            heures = ""
        try:
            type_moteur = soup.find("td", text="Type moteur :").find_next("td").text.strip()
        except Exception:
            type_moteur = ""
        try:
            style_pneus = soup.find("td", text="Styles pneus :").find_next("td").text.strip()
        except Exception:
            style_pneus = ""
        try:
            fourches = soup.find("td", text="Fourches :").find_next("td").text.strip()
        except Exception:
            fourches = ""
        data = {
            "post_name": f"{capacity} {marque} {year}",
            "capacity": capacity,
            "marque": marque,
            "model": model,
            "mat": mat,
            "annee": year,
            "heures": heures,
            "type_moteur": type_moteur,
            "style_pneus": style_pneus,
            "fourches": fourches,
            "url": item,
        }
        request_("POST", API_ENDPOINT, data=data)


def _crawl_equipementsmonteregie_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.find('a').get('href')
        for el in soup.find_all("div", class_="itemInfo")
    ]
    return set(item_links)


def crawl_equipementsmonteregie(request):
    if request.method == "POST":
        print("[equipementsmonteregie] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_equipementsmonteregie_category(category_link)
            )
        print(f"[equipementsmonteregie] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "equipementsmonteregie")
            return "No links were found on equipementsmonteregie website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "equipementsmonteregie", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for equipementsmonteregie", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
