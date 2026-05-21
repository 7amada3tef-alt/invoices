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
            "per_page": 200,
            "from_date": "2025-04-01",
            "to_date": "2026-03-31"
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
# دالة خاصة للـ Journals
# ==============================
def fetch_journals(access_token, org_id):
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    all_journals = []
    page = 1
    has_more = True
    
    while has_more:
        response = requests.get(
            "https://www.zohoapis.com/books/v3/journals",
            headers=headers,
            params={
                "organization_id": org_id,
                "page": page,
                "per_page": 200,
                "sort_column": "journal_date",
                "sort_order": "A"   # مهم جدًا
            }
        ).json()
    
        journals = response.get("journals", [])
        all_journals.extend(journals)
    
        page_context = response.get("page_context", {})
        has_more = page_context.get("has_more_page", False)
    
        page += 1

    return all_journals
    
def fetch_chart_of_accounts(access_token, org_id ):
    all_items = []
    page = 1
    has_more = True
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    while has_more and page <= 100:
        params = {
            "organization_id": org_id,
            "page": page,
            "per_page": 5000,
            "filter_by": "AccountType.All"
        }

        response = requests.get(
            "https://www.zohoapis.com/books/v3/chartofaccounts",
            headers=headers,
            params=params
         ).json()

        items = response.get("chartofaccounts", [])
        all_items.extend(items)

        has_more = response.get("page_context", {}).get("has_more_page", False)
        page += 1

    return all_items

# ==============================
# جلب البيانات
# ==============================
invoices    = fetch_all("invoices", "invoices")
bills       = fetch_all("bills", "bills")
expenses    = fetch_all("expenses", "expenses")
creditnotes = fetch_all("creditnotes", "creditnotes")
journals    = fetch_journals(access_token, org_id)
chartofaccounts = fetch_chart_of_accounts(access_token, org_id) 


# ==============================
# تحويل إلى DataFrame
# ==============================
df_invoices    = pd.DataFrame(invoices)
df_bills       = pd.DataFrame(bills)
df_expenses    = pd.DataFrame(expenses)
df_creditnotes = pd.DataFrame(creditnotes)
df_journals    = pd.DataFrame(journals)
df_chartofaccounts = pd.DataFrame(chartofaccounts)

# ==============================
# حفظ الملفات JSON
# ==============================
df_invoices.to_json("invoices.json", orient="records", force_ascii=False, indent=4)
df_bills.to_json("bills.json", orient="records", force_ascii=False, indent=4)
df_expenses.to_json("expenses.json", orient="records", force_ascii=False, indent=4)
df_creditnotes.to_json("creditnotes.json", orient="records", force_ascii=False, indent=4)
df_journals.to_json("journals.json", orient="records", force_ascii=False, indent=4)
df_chartofaccounts.to_json("chartofaccounts.json", orient="records",force_ascii=False,indent=4)

# --------------
# invoice_lines
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
df_invoice_lines.to_json("df_invoice_lines_itmes.json", orient="records", force_ascii=False, indent=4)

# ---------------------------------

# journals_lines
def fetch_journal_details(journal_id, access_token, org_id):
    url = f"https://www.zohoapis.com/books/v3/journals/{journal_id}"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    params = {"organization_id": org_id}

    response = requests.get(url, headers=headers, params=params).json()
    journal = response.get("journal", {})
    return journal.get("line_items", [])


lines_data = []

for journal_id in df_journals["journal_id"]:
    line_items = fetch_journal_details(journal_id, access_token, org_id)

    for line in line_items:
        line["journal_id"] = journal_id
        lines_data.append(line)
df_journal_lines = pd.DataFrame(lines_data)
df_journal_lines.to_json('journal_lines.json', orient="records", indent=4, force_ascii=False)

# ------------------------
# BILLS LINES

def fetch_bill_line_items(bill_id, access_token, org_id):
    url = f"https://www.zohoapis.com/books/v3/bills/{bill_id}"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    params = {"organization_id": org_id}

    response = requests.get(url, headers=headers, params=params).json()
    bill = response.get("bill", {})
    return bill.get("line_items", [])


bill_lines = []
for bill_id in df_bills["bill_id"]:
    line_items = fetch_bill_line_items(bill_id, access_token, org_id)

    for line in line_items:
        line["bill_id"] = bill_id
        bill_lines.append(line)

bills_lines_items = pd.DataFrame(bill_lines)

bills_lines_items.to_json('bills_lines_items.json', orient="records", indent=4, force_ascii=False)    

