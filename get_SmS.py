
import smartsheet
import json

smart = smartsheet.Smartsheet("Wq3V6Ol8dc4UXjLnlSmBYWGJqEmLOAdzZ9QFe")
smart.errors_as_exceptions(True)

sheet = smart.Sheets.get_sheet(7597899809509252)

# Get column names
cols = {c.id: c.title for c in sheet.columns}

# Extract sheet data
data = []

for row in sheet.rows:
    row_data = {
        cols[c.column_id]: c.value
        for c in row.cells
    }
    data.append(row_data)

# Save data to JSON file
with open("smartsheet_data.json", "w", encoding="utf-8") as json_file:
    json.dump(data, json_file, ensure_ascii=False, indent=4)

