
import smartsheet
import json
import os

API_TOKEN = os.environ["SMARTSHEET_API_TOKEN"]
SHEET_ID = 7597899809509252

smart = smartsheet.Smartsheet(API_TOKEN)
smart.errors_as_exceptions(True)

sheet = smart.Sheets.get_sheet(SHEET_ID)

cols = {c.id: c.title for c in sheet.columns}

data = []

for row in sheet.rows:
    row_data = {
        cols[c.column_id]: c.value
        for c in row.cells
    }
    data.append(row_data)

with open("smartsheet_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
