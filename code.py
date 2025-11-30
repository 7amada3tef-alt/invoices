import os
import requests
import json
import pandas as pd

# ==========================
# قراءة المتغيرات من GitHub Secrets
# ==========================
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
refresh_token = os.getenv("REFRESH_TOKEN")
org_id = os.getenv("ORG_ID")

TOKEN_FILE = "zoho_token.json"

# ==========================
# الحصول على access token
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
        token_data = response.json()
        access_token = token_data.get("access_token")
        print("✅ New Zoho access token received.")
        save_token(access_token)
        return access_token
    else:
        print(f"❌ Failed to refresh token: {response.text}")
        return None

def save_token(token):
    with open(TOKEN_FILE, "w") as f:
        json.dump({"access_token": token}, f)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            return data.get("access_token")
    return None


# =======================================
#   جلب الفواتير مع التعامل مع كل الصفحات
# =======================================
def get_all_invoices(access_token):
    url = "https://www.zohoapis.com/books/v3/invoices"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    all_invoices = []
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
            print(f"❌ Failed to fetch invoices (page {page}): {response.text}")
            break

        data = response.json()

        invoices = data.get("invoices", [])
        if not invoices:
            break  # انتهت الصفحات

        print(f"📄 Loaded page {page} - {len(invoices)} invoices")

        all_invoices.extend(invoices)
        page += 1

    print(f"✅ Total invoices fetched: {len(all_invoices)}")
    return all_invoices


# ==============================
#   الجزء الرئيسي للتنفيذ
# ==============================
if __name__ == "__main__":

    token = load_token()
    if not token:
        print("🔄 Requesting new Zoho access token...")
        token = get_access_token()
    else:
        print("✅ Using cached Zoho access token")

    if token:
        invoices = get_all_invoices(token)

        if invoices:
            df = pd.json_normalize(invoices)
            df.to_json("invoices.json", orient="records", indent=4, force_ascii=False)
            print("💾 invoices.json created successfully!")
