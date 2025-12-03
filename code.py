import os
import json
import requests
import pandas as pd

TOKEN_FILE = "zoho_token.json"

# ===============================
# الحصول على Access Token
# ===============================
def get_access_token():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    refresh_token = os.getenv("REFRESH_TOKEN")

    token_url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }

    response = requests.post(token_url, data=data)
    token_data = response.json()

    if "access_token" not in token_data:
        raise Exception(f"Error fetching access token: {token_data}")

    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)

    return token_data["access_token"]


# ===============================
# دالة Fetch موحدة
# ===============================
def fetch_module(module_name, access_token, org_id):
    base_url = f"https://books.zoho.com/api/v3/{module_name}"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    page = 1
    per_page = 200
    all_records = []

    while True:
        url = f"{base_url}?organization_id={org_id}&page={page}&per_page={per_page}"
        response = requests.get(url, headers=headers)
        data = response.json()

        if response.status_code != 200 or module_name not in data:
            break

        records = data[module_name]
        if not records:
            break

        all_records.extend(records)
        page += 1

    return all_records


# ===============================
# دالة خاصة للـ Journal (لا يعمل مع fetch_module)
# ===============================
def fetch_journals(access_token, org_id):
    url = f"https://books.zoho.com/api/v3/journals?organization_id={org_id}"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error fetching journals: {response.text}")

    return response.json().get("journals", [])


# ===============================
# حفظ JSON
# ===============================
def save_json(df, filename):
    df.to_json(filename, orient="records", force_ascii=False, indent=4)


# ===============================
# Main Execution
# ===============================
def main():
    org_id = os.getenv("ORG_ID")
    access_token = get_access_token()

    modules = {
        "invoices": "invoices.json",
        "bills": "bills.json",
        "expenses": "expenses.json",
        "creditnotes": "creditnotes.json"
    }

    # تحميل الموديولات العادية
    for module, file_name in modules.items():
        records = fetch_module(module, access_token, org_id)
        df = pd.DataFrame(records)
        save_json(df, file_name)

    # تحميل الجورنال
    journals = fetch_journals(access_token, org_id)
    df_j = pd.DataFrame(journals)
    save_json(df_j, "journals.json")


# ===============================
# Run
# ===============================
if __name__ == "__main__":
    main()
