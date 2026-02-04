import os
import json
import requests

# ==============================
# Credentials (from environment)
# ==============================
client_id     = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
refresh_token = os.getenv("REFRESH_TOKEN")
org_id        = os.getenv("ORG_ID")


# ==============================
# Get Access Token
# ==============================
token_response = requests.post(
    "https://accounts.zoho.com/oauth/v2/token",
    data={
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }
)

token_data = token_response.json()
access_token = token_data.get("access_token")

# ==============================
# Get Balance Sheet Report
# ==============================
headers = {
    "Authorization": f"Zoho-oauthtoken {access_token}"
}

params = {
    "organization_id": org_id
}

response = requests.get(
    "https://www.zohoapis.com/books/v3/reports/balancesheet",
    headers=headers,
    params=params
)

data = response.json()

with open("balancesheet.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Balance sheet saved successfully.")
