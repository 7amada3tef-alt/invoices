import os
import requests
import pandas as pd
import json

# ==============================
# قراءة بيانات الربط من Environment Variables
# ==============================
client_id     = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
refresh_token = os.getenv("REFRESH_TOKEN")
org_id        = os.getenv("ORG_ID")

# ==============================
# الحصول على Access Token
# ==============================
def get_access_token():
    url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, data=data).json()
    return response["access_token"]

access_token = get_access_token()

# ==============================
# دالة عامة لجلب الصفحات
# ==============================
def fetch_all(endpoint, item_key):
    all_items = []
    page = 1
    has_more = True
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    while has_more and page <= 100:
        url = f"https://www.zohoapis.com/books/v3/{endpoint}"
        params = {
            "organization_id": org_id,
            "page": page,
            "per_page": 200
        }

        response = requests.get(url, headers=headers, params=params).json()

        if item_key in response:
            items = response[item_key]
            all_items.extend(items)

            has_more = response.get("page_context", {}).get("has_more_page", False)
            page += 1
        else:
            has_more = False

    return all_items

# ==============================
# جلب البيانات
# ==============================
invoices    = fetch_all("invoices", "invoices")
bills       = fetch_all("bills", "bills")
expenses    = fetch_all("expenses", "expenses")
creditnotes = fetch_all("creditnotes", "creditnotes")
journals = fetch_all("journals", "journals")

# ==============================
# تحويل إلى DataFrame
# ==============================
df_invoices    = pd.DataFrame(invoices)
df_bills       = pd.DataFrame(bills)
df_expenses    = pd.DataFrame(expenses)
df_creditnotes = pd.DataFrame(creditnotes)
df_journals = pd.DataFrame(journals)

# ==============================
# حفظ الملفات JSON
# ==============================
df_invoices.to_json("invoices.json", orient="records", force_ascii=False, indent=4)
df_bills.to_json("bills.json", orient="records", force_ascii=False, indent=4)
df_expenses.to_json("expenses.json", orient="records", force_ascii=False, indent=4)
df_creditnotes.to_json("creditnotes.json", orient="records", force_ascii=False, indent=4)
df_journals.to_json("journals.json", orient="records", force_ascii=False, indent=4)

