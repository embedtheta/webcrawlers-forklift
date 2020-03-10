import os
import re

from bs4 import BeautifulSoup
from google.cloud import firestore

from utils import request_, send_email, format_links_modified, add_and_compare_new_items, send_warning_email

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL = os.getenv("EMAIL")


def _crawl_valleesaintsauveur_section(html):
    link = html.find("a", {"rel": "external"})
    if link is not None:
        link = link.get("href")
    else:
        return None
    try:
        name = html.find("h2").find("a").text
    except:
        name = ""
    try:
        address = html.find("p").text
    except:
        address = ""
    try:
        phone_raw = html.find_all("p")[1].text
        phone = "".join(re.findall(r"\d+", phone_raw))
    except:
        phone = ""
    return {
        "link": link,
        "name": name,
        "address": address,
        "phone": phone,
    }


def crawl_valleesaintsauveur(request):
    if request.method == "POST":
        print("[valleesaintsauveur] Started crawling website")
        response_text = request_(
            "POST",
            "https://www.valleesaintsauveur.com/1-chambre-de-commerce/repertoire-des-membres.html",
            data={
                "actionEntreprise": "1",
                "NomEntreprise": "Nom de l'entreprise",
                "VILLE_ID": "",
            }
        ).text

        soup = BeautifulSoup(response_text, "html.parser")
        links_data = []
        sections = soup.find_all("div", class_="section8")
        for section in sections:
            data = _crawl_valleesaintsauveur_section(section)
            if data is not None:
                links_data.append(data)
        page = 1
        while True:
            response_text = request_(
                "POST",
                "https://www.valleesaintsauveur.com/1-chambre-de-commerce/repertoire-des-membres.html",
                data={
                    "actionEntreprise": "1",
                    "NomEntreprise": "Nom de l'entreprise",
                    "VILLE_ID": "",
                    "start": page * 10 + 1,
                    "Ordre": "societe asc",
                }
            ).text
            soup = BeautifulSoup(response_text, "html.parser")
            sections = soup.find_all("div", class_="section8")
            new_links_data = []
            for section in sections:
                data = _crawl_valleesaintsauveur_section(section)
                if data is not None:
                    new_links_data.append(data)
            if new_links_data:
                links_data.extend(new_links_data)
            else:
                break

            page += 1

        print(f"[valleesaintsauveur] Got {len(links_data)} item links")

        if not links_data:
            send_warning_email(SENDGRID_API_KEY, EMAIL, [EMAIL], "valleesaintsauveur")
            return "No links were found on valleesaintsauveur website"

        db = firestore.Client()

        comparison_result = add_and_compare_new_items(db, "valleesaintsauveur", links_data)
        added_items, deleted_items = comparison_result["added"], comparison_result["deleted"]
        email_text = ""
        if added_items:
            email_text += format_links_modified("Added", added_items)
        if email_text != "":
            send_email(SENDGRID_API_KEY, EMAIL, [EMAIL], "Comparison results for valleesaintsauveur", email_text)
            return email_text
        else:
            return "No new added or new deleted items found"
    else:
        return "This method is not supported"
