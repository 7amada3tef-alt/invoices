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
token_url = "https://accounts.zoho.com/oauth/v2/token"
token_data = {
    "refresh_token": refresh_token,
    "client_id": client_id,
    "client_secret": client_secret,
    "grant_type": "refresh_token"
}

access_token = requests.post(token_url, data=token_data).json()["access_token"]

headers = {
    "Authorization": f"Zoho-oauthtoken {access_token}"
}

# ==============================
# Fetch ALL Invoices (Pagination)
# ==============================
all_invoices = []
page = 1
has_more = True

while has_more:
    response = requests.get(
        "https://www.zohoapis.com/books/v3/invoices",
        headers=headers,
        params={
            "organization_id": org_id,
            "page": page,
            "per_page": 200
        }
    ).json()

    invoices = response.get("invoices", [])
    all_invoices.extend(invoices)

    page_context = response.get("page_context", {})
    has_more = page_context.get("has_more_page", False)
    page += 1

# ==============================
# Save result
# ==============================
df_invoices = pd.DataFrame(all_invoices)

# ==============================
# Fetch Invoice Line Items
# ==============================


def fetch_invoice_line_items(invoice_id, access_token, org_id):
    url = f"https://www.zohoapis.com/books/v3/invoices/{invoice_id}"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    params = {"organization_id": org_id}

    response = requests.get(url, headers=headers, params=params).json()
    invoice = response.get("invoice", {})
    return invoice.get("line_items", [])




invoice_lines = []
for invoice_id in df_invoices["invoice_id"]:
    line_items = fetch_invoice_line_items(invoice_id, access_token, org_id)

    for line in line_items:
        line["invoice_id"] = invoice_id
        invoice_lines.append(line)
df_invoice_lines = pd.DataFrame(invoice_lines)

df_invoice_lines.to_json("df_invoice_lines_items.json", orient="records", force_ascii=False, indent=4)
