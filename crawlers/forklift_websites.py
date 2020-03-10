import os

from google.cloud import firestore
from googleapiclient.discovery import build

from utils import get_document_data_from_collection

GOOGLE_DEVELOPER_KEY = os.getenv("GOOGLE_DEVELOPER_KEY")
GOOGLE_SEARCH_ENGINE_CONTEXT = os.getenv("GOOGLE_SEARCH_ENGINE_CONTEXT")


def get_links_from_custom_search(res):
    links = []
    if res.get("items"):
        for i in range(len(res["items"])):
            try:
                links.append(res["items"][i]["link"])
            except KeyError:
                pass
    return links


def get_queries_for_custom_search(db):
    doc_ref = db.collection("search-queries").document("used-forklifts-inventories-for-sale-in-quebec")
    snapshot = doc_ref.get()
    data = snapshot.to_dict()
    if data:
        return data["queries"]
    else:
        return []


def make_custom_search_request(service, query, cx, start, gl="countryCA"):
    return service.cse().list(
        q=query,
        cx=cx,
        gl=gl,
        start=start,
    ).execute()


def save_search_results(db, document_name, links):
    # Already saving only search results with keywords included on website
    search_results_collection = db.collection("search-results")
    search_results_doc_ref = search_results_collection.document(document_name)
    search_results_doc_ref.set({"links": links})


def compare_search_results(existing: list, new: list):
    result = []
    for n in new:
        if n not in existing:
            result.append(n)
    return result


def find_new_forklift_websites(request):
    if request.method == "POST":
        print("[find_new_forklift_websites] Starting search")
        service = build("customsearch", "v1", developerKey=GOOGLE_DEVELOPER_KEY)
        db = firestore.Client()
        queries = get_queries_for_custom_search(db)
        if queries:
            query = queries[0]
            # Searching for 100 results
            number_of_searches = 10
            links = []
            for n in range(number_of_searches):
                res = make_custom_search_request(
                    service,
                    query,
                    GOOGLE_SEARCH_ENGINE_CONTEXT,
                    10 * n + 1,
                )
                links.extend(get_links_from_custom_search(res))
            existing_links = get_document_data_from_collection(db,
                                                               "search-results",
                                                               "used-forklifts-inventories-for-sale-in-quebec")
            links_to_add = compare_search_results(existing_links, links)
            print(f"[find_new_forklift_websites] Got {len(links_to_add)} new links to add")
            save_search_results(db, "used-forklifts-inventories-for-sale-in-quebec", links_to_add)
            return "\n".join(links_to_add)
        return "No queries available for searching new forklift websites. Please add them to the Firestore."
    else:
        return "This method is not supported"
