import os
import requests
import json
import pandas as pd

# ─────────────────────────────────────────────
# 1. CREDENTIALS
# ─────────────────────────────────────────────
client_id     = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
refresh_token = os.getenv("REFRESH_TOKEN")
org_id        = os.getenv("ORG_ID")

from_date = "2025-04-01"
to_date   = "2026-03-31"

# ─────────────────────────────────────────────
# 2. GET ACCESS TOKEN
# ─────────────────────────────────────────────
token_response = requests.post(
    "https://accounts.zoho.com/oauth/v2/token",
    data={
        "refresh_token": refresh_token,
        "client_id":     client_id,
        "client_secret": client_secret,
        "grant_type":    "refresh_token"
    }
)

token_data   = token_response.json()
access_token = token_data.get("access_token")

headers = {
    "Authorization": f"Zoho-oauthtoken {access_token}"
}

# ─────────────────────────────────────────────
# 3. GET ALL REPORTING TAGS
# ─────────────────────────────────────────────
tags_response = requests.get(
    "https://www.zohoapis.com/books/v3/reportingtags",
    headers=headers,
    params={"organization_id": org_id}
)
tags_data = tags_response.json()
all_tags  = tags_data.get("tags", [])

tag_options = []

for tag in all_tags:
    tag_id   = tag.get("tag_id")
    tag_name = tag.get("tag_name")

    options_response = requests.get(
        f"https://www.zohoapis.com/books/v3/reportingtags/{tag_id}/options/all",
        headers=headers,
        params={
            "organization_id": org_id,
            "tag_id":          tag_id
        }
    )

    options_data = options_response.json()
    options_list = options_data.get("results", [])

    for option in options_list:
        option_id   = option.get("option_id")
        option_name = option.get("option_name")

        if option_id == "untagged":
            continue

        tag_options.append({
            "tag_id":      tag_id,
            "tag_name":    tag_name,
            "option_id":   option_id,
            "option_name": option_name
        })

import json

# ─────────────────────────────────────────────
# 5. FETCH P&L WITH ALL TAG OPTIONS IN ONE CALL
# ─────────────────────────────────────────────
compare_entities = json.dumps([
    {
        "field": "tag_option_id1",
        "value": ["all"],
        "group": "reporting_tag"
    }
])

pl_response = requests.get(
    "https://www.zohoapis.com/books/v3/reports/profitandloss",
    headers=headers,
    params={
        "organization_id":     org_id,
        "from_date":           from_date,
        "to_date":             to_date,
        "cash_based":          "false",
        "is_hierarchy_report": "true",
        "compare_entities":    compare_entities
    }
 )

pl_data = pl_response.json()
pl      = pl_data.get("profit_and_loss", [])

# ─────────────────────────────────────────────
# 6. BUILD option_id → option_name LOOKUP
# ─────────────────────────────────────────────
option_lookup = {item["option_id"]: item["option_name"] for item in tag_options}
option_lookup["untagged"] = "Untagged"

# ─────────────────────────────────────────────
# 7. FLATTEN INTO RECORDS
# ─────────────────────────────────────────────
all_pl_records = []

for top in pl:
    for sub_section in top.get("account_transactions", []):
        sub_label = sub_section.get("name", "")
        for account in sub_section.get("account_transactions", []):
            account_name = account.get("name", "")
            account_code = account.get("account_code", "")
            total        = account.get("total", 0.0)

            # Overall row
            all_pl_records.append({
                "Tag_Option":       "Overall",
                "Account_Category": sub_label,
                "Account_Name":     account_name,
                "Account_Code":     account_code,
                "Total":            total
            })

            # One row per tag option
            entity_compare = account.get("entity_compare", [])
            if entity_compare:
                values = entity_compare[0].get("values", {})
                for option_id, amount in values.items():
                    if option_id.endswith("_sub_account"):
                        continue
                    all_pl_records.append({
                        "Tag_Option":       option_lookup.get(option_id, option_id),
                        "Account_Category": sub_label,
                        "Account_Name":     account_name,
                        "Account_Code":     account_code,
                        "Total":            amount
                    })

# ─────────────────────────────────────────────
# 8. SAVE TO CSV
# ─────────────────────────────────────────────
df = pd.DataFrame(all_pl_records)
df.to_csv("profit_loss_with_tags.csv", index=False, encoding="utf-8-sig")


all_transactions = []

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

chartofaccounts = fetch_chart_of_accounts(access_token, org_id)
df_chartofaccounts = pd.DataFrame(chartofaccounts)

account_ids = df_chartofaccounts['account_id']

for acc_id in account_ids:
    page = 1
    has_more = True

    while has_more and page <= 100:
        txns_response = requests.get(
            "https://www.zohoapis.com/books/v3/chartofaccounts/transactions",
            headers=headers,
            params={
                "organization_id": org_id,
                "account_id":      acc_id,
                "date.start":      from_date,
                "date.end":        to_date,
                "page":            page,
                "per_page":        5000
            }
         )

        txns_data = txns_response.json()
        account_txns = txns_data.get("transactions", [])

        for txn in account_txns:
            txn["account_id"] = acc_id
            all_transactions.append(txn)

        has_more = txns_data.get("page_context", {}).get("has_more_page", False)
        page += 1

# ─────────────────────────────────────────────
# 10. SAVE TRANSACTIONS TO JSON
# ─────────────────────────────────────────────
with open("account_transactions.json", "w", encoding="utf-8") as f:
    json.dump(all_transactions, f, ensure_ascii=False, indent=4)
