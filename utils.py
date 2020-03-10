import io
from typing import Text, List

import requests
import sendgrid
from google.api_core.exceptions import NotFound
from google.cloud import storage
from retry import retry
from sendgrid.helpers.mail import Mail, PlainTextContent


def request_(method, link, data=None, timeout=10, verify=True):
    return requests.request(
        method,
        link,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
        },
        data=data,
        timeout=timeout,
        verify=verify,
    )


def save_photos_to_bucket(
        storage_client: storage.Client,
        blob_path_general,
        photo_links,
        bucket_name):
    bucket = storage_client.get_bucket(bucket_name)

    for i, link in enumerate(photo_links):
        r = request_("GET", link)

        with io.BytesIO() as buf:
            buf.write(r.content)
            buf.seek(0)

            blob_path = blob_path_general + f"{i}.jpg"
            blob = bucket.blob(blob_path)
            blob.upload_from_file(buf)


def delete_photos_from_bucket(storage_client: storage.Client, blob_path, bucket_name):
    bucket = storage_client.get_bucket(bucket_name)

    try:
        bucket.delete_blob(blob_path)
    except NotFound:
        print(f"Deleting photos from bucket, blob {blob_path} not found")


def add_and_compare_new_items(db, website, items, field=None):
    new_counter = add_new_counter_to_storage(db, website)
    add_items_to_storage(db, new_counter, website, items)

    comparison_result = compare_results(db, website, new_counter, field)
    return comparison_result


@retry(tries=3, delay=10)
def send_email(
        sendgrid_api_key: Text,
        from_email: Text,
        to_emails: List[Text],
        subject: Text,
        email_text: Text) -> None:
    sg = sendgrid.SendGridAPIClient(
        api_key=sendgrid_api_key
    )
    content = PlainTextContent(email_text)
    mail = Mail(
        from_email=from_email,
        to_emails=to_emails,
        subject=subject,
        plain_text_content=content
    )
    sg.send(mail)
    print(f"Sent email from {from_email} to {to_emails} with subject '{subject}' and text: '{email_text}'")


def send_warning_email(
        sendgrid_api_key: Text,
        from_email: Text,
        to_emails: List[Text],
        parser_name: Text) -> None:
    send_email(
        sendgrid_api_key,
        from_email,
        to_emails,
        f"Warning: {parser_name}",
        f"Something wrong with getting links from {parser_name} website"
    )


def compare_results(db, website, new_counter, field=None):
    if new_counter == 1:  # no runs before - nothing to compare
        return {
            "added": [],
            "deleted": []
        }
    counter = new_counter - 1
    links_collection = db.collection("links")
    current_doc_ref = links_collection.document(f"{website}-{counter}")
    current_snapshot = current_doc_ref.get()
    current_data = current_snapshot.to_dict()
    current_links = current_data["links"]
    if field is not None:
        current_links = [
            e[field] for e in current_links
        ]

    new_doc_ref = links_collection.document(f"{website}-{new_counter}")
    new_snapshot = new_doc_ref.get()
    new_data = new_snapshot.to_dict()
    new_links = new_data["links"]
    if field is not None:
        new_links = [
            e[field] for e in new_links
        ]

    codes_added = []
    for n_c in new_links:
        if n_c not in current_links:
            codes_added.append(n_c)
    codes_deleted = []
    for c_c in current_links:
        if c_c not in new_links:
            codes_deleted.append(c_c)
    return {
        "added": codes_added,
        "deleted": codes_deleted
    }


def format_links_modified(_type, links):
    links_formatted = ""
    for link in links:
        links_formatted += "\t" + link + "\n"
    return f"{_type}:\n{links_formatted}\n\n"


def get_document_data_from_collection(db, collection, document):
    _collection = db.collection(collection)
    _doc_ref = _collection.document(document)
    snapshot = _doc_ref.get()
    data = snapshot.to_dict()
    # Returning empty list if data is None
    return [] if not data else data


def add_items_to_storage(db, new_counter, website, links):
    doc_ref = db.collection("links").document(f"{website}-{new_counter}")
    doc_ref.set({"links": links})


def add_new_counter_to_storage(db, website):
    doc_ref = db.collection("counters").document(f"{website}")
    snapshot = doc_ref.get()
    data = snapshot.to_dict()
    if data:
        current_value = data["value"]
        field_updates = {"value": current_value + 1}
        doc_ref.update(field_updates)
        return current_value + 1
    else:
        doc_ref.set({"value": 1})
        return 1
