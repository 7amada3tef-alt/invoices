import os
import requests
import json
import pandas as pd

# ==========================
# Environment Variables
# ==========================
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
refresh_token = os.getenv("REFRESH_TOKEN")
org_id = os.getenv("ORG_ID")

TOKEN_FILE = "zoho_token.json"

# ==========================
# ACCESS TOKEN MANAGEMENT
# ==========================
def get_access_token():
    url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, data=data)

    if response.status_code == 200:
        token = response.json().get("access_token")
        save_token(token)
        return token
    return None

def save_token(token):
    with open(TOKEN_FILE, "w") as f:
        json.dump({"access_token": token}, f)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f).get("access_token")
    return None


# ==========================
#   GENERIC PAGINATION FETCHER
# ==========================
def fetch_all_pages(endpoint, access_token, key_name):
    url = f"https://www.zohoapis.com/books/v3/{endpoint}"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    all_data = []
    page = 1
    per_page = 200

    while True:
        params = {
            "organization_id": org_id,
            "page": page,
            "per_page": per_page
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            break

        data = response.json()
        items = data.get(key_name, [])

        if not items:
            break

        all_data.extend(items)
        page += 1

    return all_data


# ==========================
#   SPECIFIC DATA FUNCTIONS
# ==========================
def get_invoices(token):
    return fetch_all_pages("invoices", token, "invoices")

def get_bills(token):
    return fetch_all_pages("bills", token, "bills")

def get_expenses(token):
    return fetch_all_pages("expenses", token, "expenses")

def get_creditnotes(token):
    return fetch_all_pages("creditnotes", token, "creditnotes")


# ==========================
#   SAVE FUNCTION
# ==========================
REPO_DIR = os.getcwd()   # current repo folder

def save_json(data, filename):
    if data:
        df = pd.json_normalize(data)
        filepath = os.path.join(REPO_DIR, filename)
        df.to_json(filepath, orient="records", indent=4, force_ascii=False)



# ==========================
#   MAIN SCRIPT
# ==========================
if __name__ == "__main__":
    token = load_token()
    if not token:
        token = get_access_token()

    if token:
        save_json(get_invoices(token), "invoices.json")
        save_json(get_bills(token), "bills.json")
        save_json(get_expenses(token), "expenses.json")
        save_json(get_creditnotes(token), "creditnotes.json")
