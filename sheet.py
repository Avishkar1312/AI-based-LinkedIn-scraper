import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def write_to_sheet(data, spreadsheet_id, range_start='A1'):
    # Define the scopes
    scope = ['https://www.googleapis.com/auth/spreadsheets']

    # Authenticate using the service account JSON file
    creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
    client = gspread.authorize(creds)

    # Open the spreadsheet
    sheet = client.open_by_key(spreadsheet_id).sheet1

    # Clear previous content (optional)
    sheet.clear()

    # Update with new data
    sheet.update(range_start, data)
    print("✅ Data written to sheet!")

# 🔸 Sample usage:
sample_data = [
    ['Name', 'Headline', 'Location', 'Previous Job', 'URL'],
    ['John Doe', 'Engineer', 'NY', 'Google', 'https://...'],
]

# Replace this with your actual sheet ID
SPREADSHEET_ID = '11-81uSoERbeJ_2L5-YeEFZhYKMNx58SaG3AIH7Jq-4E'
write_to_sheet(sample_data, SPREADSHEET_ID)
