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

SMFORKLIFT_CATEGORIES = [
    "http://www.smforklift.com/index.php/fr/chariots-elevateurs-1/ci-roues-pneumatiques.html",
    "http://www.smforklift.com/index.php/fr/chariots-elevateurs-1/ci-roues-dures.html",
    "http://www.smforklift.com/index.php/fr/chariots-elevateurs-1/3-roues-electriques.html",
    "http://www.smforklift.com/index.php/fr/chariots-elevateurs-1/4-roues-electriques.html",
    "http://www.smforklift.com/index.php/fr/chariots-elevateurs-1/electriques-pneumatiques.html",
    "http://www.smforklift.com/index.php/fr/chariots-elevateurs-1/contrebalances-stand-up.html",
    "http://www.smforklift.com/index.php/fr/chariots-elevateurs-1/reach-double-reach.html",
    "http://www.smforklift.com/index.php/fr/chariots-elevateurs-1/preparateurs-de-commandes.html",
    "http://www.smforklift.com/index.php/fr/chariots-elevateurs-1/transpalettes-gerbeurs.html",
    "http://www.smforklift.com/index.php/fr/chariots-elevateurs-1/autre-type-de-chariots.html",
]


def _process_added_items(items):
    for item in items:
        codes_added = []
        source = request_("GET", item).text
        soup = BeautifulSoup(source, "html.parser")
        for category in soup.find_all('li', class_="crumb_2"):
            na = re.sub(r"[\n\t]*", "", category.text)
        for description in soup.find_all('table', id='product-attribute-specs-table'):
            for data in description.find_all('td', class_='data'):
                data_new = re.sub(r"[\n\t\s]*", "", data.text)
                codes_added.append(data_new)
        Capacity = re.sub('[,s]', '', codes_added[4]).upper()
        Marque = codes_added[2].upper()
        Model = codes_added[3]
        Mat = codes_added[6]
        Annee = codes_added[1]
        post_name = na + " " + Capacity + " " + Marque + " " + Annee
        data = {'post_name': post_name,
                'capacity': Capacity,
                'marque': Marque,
                'model': Model,
                'mat': Mat,
                'annee': Annee,
                'url': item}
        API_ENDPOINT = ""
        request_("POST", API_ENDPOINT, data=data)


def _crawl_smforklift_category(category_link):
    response_text = request_("GET", category_link).text
    soup = BeautifulSoup(response_text, "html.parser")
    item_links = [
        el.get("href")
        for el in soup.find_all("a", class_="product-image")
    ]
    while True:
        next_page_link_el = soup.find("a", class_="next i-next")
        if next_page_link_el is not None:
            response_text = request_("GET", next_page_link_el["href"]).text
            soup = BeautifulSoup(response_text, "html.parser")
            item_links.extend([
                el.get("href")
                for el in soup.find_all("a", class_="product-image")
            ])
        else:
            break
    return set(item_links)


def crawl_smforklift(request):
    if request.method == "POST":
        print("[smforklift] Started crawling website")
        item_links = []
        for category_link in SMFORKLIFT_CATEGORIES:
            item_links.extend(
                _crawl_smforklift_category(category_link)
            )
        print(f"[smforklift] Got {len(item_links)} item links")

        if not item_links:
            send_warning_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "smforklift")
            return "No links were found on smforklift website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "smforklift", item_links)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            _process_added_items(added_items)
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, SENDER_EMAIL, RECEIVER_EMAILS, "Comparison results for smforklift", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
