import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import sys
import re # Import the regular expression module

# --- Configuration ---
if len(sys.argv) < 4:
    print("Usage: python sheet_mass.py <json_filename> <sheet_tab_name> <spreadsheet_id>")
    sys.exit(1)

json_file_name = sys.argv[1] # e.g., "mass_scraped_urls.json"
sheet_tab_name = sys.argv[2]
SPREADSHEET_ID = sys.argv[3]

# Get the directory of the current script (sheet_mass.py)
# This ensures that files are located relative to sheet_mass.py's actual location,
# regardless of the current working directory from which Streamlit calls it.
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the service account file
#SERVICE_ACCOUNT_FILE_PATH = os.path.join(script_dir, 'service_account.json')


# Construct the full path to the profile URLs JSON file
# This assumes app.py saves the JSON file directly into the 'server' directory
# where sheet_mass.py also resides.
BASE_DATA_INPUT_DIR = os.path.join(script_dir, "..", "company_urls")
PROFILE_URLS_JSON_FILE_PATH = os.path.join(BASE_DATA_INPUT_DIR, json_file_name)

SERVICE_ACCOUNT_INFO = None
try:
    service_account_json_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json_str:
        SERVICE_ACCOUNT_INFO = json.loads(service_account_json_str)
    else:
        # Fallback for local development: try to load from local file
        local_service_account_path = os.path.join(script_dir, 'service_account.json')
        if os.path.exists(local_service_account_path):
            with open(local_service_account_path, 'r') as f:
                SERVICE_ACCOUNT_INFO = json.load(f)
        else:
            print("Error: GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set and local 'service_account.json' not found.")
            sys.exit(1) # Exit if credentials aren't found
except json.JSONDecodeError:
    print("Error: GOOGLE_SERVICE_ACCOUNT_JSON environment variable contains invalid JSON.")
    sys.exit(1)
except Exception as e:
    print(f"Error loading service account info: {e}")
    sys.exit(1)

#SPREADSHEET_ID = '11-81uSoERbeJ_2L5-YeEFZhYKMNx58SaG3AIH7Jq-4E' # Your Google Sheet ID
TARGET_WORKSHEET_NAME = sheet_tab_name


def extract_name_from_linkedin_url(url):
    """
    Extracts a readable name from a LinkedIn profile URL, similar to your app.py.
    Assumes URL format like: https://www.linkedin.com/in/first-name-last-name-identifier/
    """
    match = re.search(r'linkedin\.com/in/([^/]+)', url)
    if match:
        name_part = match.group(1)
        # LinkedIn profile IDs often have alphanumeric strings at the end (e.g., -a1b2c3d4).
        cleaned_name = re.sub(r'-\w{1,10}$', '', name_part) # Adjust the {1,10} if IDs are longer/shorter
        cleaned_name = cleaned_name.replace('-', ' ').replace('.', ' ').strip()
        name_words = [word.capitalize() for word in cleaned_name.split(' ') if word]
        return ' '.join(name_words)
    return "Unknown User" # Fallback name if extraction fails


def append_profile_urls_to_sheet():
    scope = ['https://www.googleapis.com/auth/spreadsheets']

    try:
        # Use the fully qualified path for the service account file
        creds = ServiceAccountCredentials.from_json_keyfile_info(SERVICE_ACCOUNT_INFO, scope)
        client = gspread.authorize(creds)
    except Exception as e:
        # Removed the unicode character (❌)
        print(f"Authentication Error: Ensure '{SERVICE_ACCOUNT_FILE_PATH}' is correct and present in the same directory as sheet_mass.py. Details: {e}")
        return False

    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(TARGET_WORKSHEET_NAME)
    except gspread.exceptions.SpreadsheetNotFound:
        # Removed the unicode character (❌)
        print(f"Spreadsheet with ID '{SPREADSHEET_ID}' not found. Please check the ID and that the service account has editor access.")
        return False
    except gspread.exceptions.WorksheetNotFound:
        # Removed the unicode character (❌)
        print(f"Worksheet '{TARGET_WORKSHEET_NAME}' not found in spreadsheet '{SPREADSHEET_ID}'. Creating it now...")
        try:
            sheet = spreadsheet.add_worksheet(title=TARGET_WORKSHEET_NAME, rows="100", cols="26")
            # Removed the unicode character (✅)
            print(f"Created new worksheet: '{TARGET_WORKSHEET_NAME}'.")
        except Exception as e:
            # Removed the unicode character (❌)
            print(f"Error creating new worksheet. Details: {e}")
            return False
    except Exception as e:
        # Removed the unicode character (❌)
        print(f"Error opening Google Sheet or Worksheet. Details: {e}")
        return False

    # Check if the JSON data file exists using its full path
    if not os.path.exists(PROFILE_URLS_JSON_FILE_PATH):
        # Removed the unicode character (❌)
        print(f"Error: The JSON file '{PROFILE_URLS_JSON_FILE_PATH}' was not found. Please ensure app.py has run and saved profile URLs.")
        return False

    try:
        # Open the JSON data file using its full path
        with open(PROFILE_URLS_JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        profile_entries = []
        if isinstance(loaded_data, list):
            for item in loaded_data:
                if isinstance(item, dict) and 'url' in item:
                    profile_entries.append({'url': item['url'], 'name': item.get('name', extract_name_from_linkedin_url(item['url']))})
                elif isinstance(item, str): # Handle case where it's just a list of URL strings
                    profile_entries.append({'url': item, 'name': extract_name_from_linkedin_url(item)})
        else:
            # Removed the unicode character (ℹ️)
            print(f"No valid list of profile data found in '{PROFILE_URLS_JSON_FILE_PATH}'. Nothing to append.")
            return False

        if not profile_entries:
            # Removed the unicode character (ℹ️)
            print(f"No profile URLs to append from '{PROFILE_URLS_JSON_FILE_PATH}'.")
            return False

        # --- Handle Headers (Append only if the sheet is empty) ---
        current_first_row = sheet.row_values(1)
        if not current_first_row or all(c == '' for c in current_first_row):
            headers = ['Profile Name', 'Profile URL']
            sheet.append_row(headers)
            # Removed the unicode character (✅)
            print("Headers added to Google Sheet.")

        # --- Prepare data for batch append ---
        rows_to_append = []
        appended_count = 0
        for entry in profile_entries:
            row = [entry['name'], entry['url']]
            rows_to_append.append(row)
            appended_count += 1
            print(f"Prepared to append: Name='{entry['name']}', URL='{entry['url']}'")

        if rows_to_append:
            sheet.append_rows(rows_to_append) # Use append_rows for efficiency
            # Removed the unicode character (🎉)
            print(f"Successfully appended {appended_count} profile URLs to Google Sheet in tab '{TARGET_WORKSHEET_NAME}'!")
        else:
            # Removed the unicode character (ℹ️)
            print("No new profile URLs were prepared for appending.")

        return True

    except json.JSONDecodeError:
        # Removed the unicode character (❌)
        print(f"Error: Could not decode JSON from '{PROFILE_URLS_JSON_FILE_PATH}'. The file might be empty or corrupted.")
        return False
    except Exception as e:
        # Removed the unicode character (❌)
        print(f"An unexpected error occurred during data processing or sheet update: {e}")
        return False

if __name__ == '__main__':
    append_profile_urls_to_sheet()
