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
    "http://www.machinerieplante.com/fr/equipement/",
]


def _process_added_items(items):
    for item in items:
        url_link = f"http://www.machinerieplante.com/fr/equipement/{item}"
        source = request_("GET", url_link).text
        soup = BeautifulSoup(source, "html.parser")
        try:
            name = soup.find('td', class_='Entete').text
        except Exception:
            name = ""

        try:
            capacity = soup.find("td", text="Capacité:").find_next("td").text.strip()
        except Exception:
            capacity = ""
        try:
            marque = soup.find("td", text="Marque:").find_next("td").text.strip()
        except Exception:
            marque = ""
        try:
            model = soup.find("td", text="Modèle:").find_next("td").text.strip()
        except Exception:
            model = ""
        try:
            mat_1 = soup.find("td", text="Mât:").find_next("td").text.strip()
            mat_2 = soup.find("td", text="Hauteur abaissée (mât):").find_next("td").text.strip()
            mat_3 = soup.find("td", text="Hauteur d'élévation:").find_next("td").text.strip()
            mat = f"{mat_1}/{mat_2}/{mat_3}"
        except Exception:
            mat = ""
        try:
            prix = soup.find("td", text="Prix:").find_next("td").text.strip()
        except Exception:
            prix = ""
        try:
            heures = soup.find("td", text="Hauteur du toit:").find_next("td").text.strip()
        except Exception:
            heures = ""
        try:
            type_moteur = soup.find("td", text="Moteur:").find_next("td").text.strip()
        except Exception:
            type_moteur = ""
        try:
            style_pneus_1 = soup.find("td", text="Pneus de traction:").find_next("td").text.strip()
            style_pneus_2 = soup.find("td", text="Pneus de traction:").find_next("td").text.strip()
            style_pneus = f"{style_pneus_1}/{style_pneus_2}"
        except Exception:
            style_pneus = ""
        try:
            fourches = soup.find("td", text="Fourches:").find_next("td").text.strip()
        except Exception:
            fourches = ""
        try:
            large = soup.find("td", text="Largeur du chariot:").find_next("td").text.strip()
        except Exception:
            large = ""
        try:
            long = soup.find("td", text="Longueur du chariot:").find_next("td").text.strip()
        except Exception:
            long = ""
        try:
            unit = soup.find("td", text="# Unité:").find_next("td").text.strip()
        except Exception:
            unit = ""
        data = {
            "post_name": f"{name} {capacity} {marque}",
            "capacity": capacity,
            "marque": marque,
            "model": model,
            "mat": mat,
            "prix": prix,
            'large': large,
            'long': long,
            'unit': unit,
            'fourches': fourches,
            'style_pneus': style_pneus,
            'type_moteur': type_moteur,
            'heures': heures,
            "url": url_link,
        }
        request_("POST", API_ENDPOINT, data=data)


def _crawl_machinerieplante_category(category_link):
    url_link = f"http://www.machinerieplante.com/fr/equipement/{category_link}"
    response_text = request_("GET", url_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.get('href')
        for el in soup.find_all("a", class_="Lfooter")
    ]
    return set(item_links)


def _crawl_machinerieplante_category_2(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.get('href')
        for el in soup.find_all("a", class_="Menugj")
    ]
    for ct in item_links:
        url_link = f"http://www.machinerieplante.com/fr/equipement/{ct}"
        response_text = request_("GET", url_link).text
        soup = BeautifulSoup(response_text, "html.parser")
        item_links_test = [
            el.get('href')
            for el in soup.find_all("a", class_="Menugj")
        ]
    item_links.extend(item_links_test)
    return set(item_links)


def crawl_machinerieplante(request):
    if request.method == "POST":
        print("[machinerieplante] Started crawling website")
        item_links = []
        for category_link in CATEGORIES:
            item_links.extend(
                _crawl_machinerieplante_category_2(category_link)
            )
        item_links_subcategory = []
        for category_link in item_links:
            item_links_subcategory.extend(
                _crawl_machinerieplante_category(category_link)
            )
        print(f"[machinerieplante] Got {len(item_links_subcategory)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "machinerieplante")
            return "No links were found on machinerieplante website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "machinerieplante", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for machinerieplante", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
