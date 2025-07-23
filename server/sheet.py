import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import sys

# --- Configuration ---
if len(sys.argv) < 4:
    print("Usage: python sheet.py <json_filename> <sheet_tab_name> <spreadsheet_id>")
    sys.exit(1)

json_file_name = sys.argv[1] # e.g., "individual_profiles_data.json"
sheet_tab_name = sys.argv[2]
SPREADSHEET_ID = sys.argv[3]

# Get the directory of the current script (sheet.py)
# This ensures that files are located relative to sheet.py's actual location,
# regardless of the current working directory from which Streamlit calls it.
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the service account file
#SERVICE_ACCOUNT_FILE_PATH = os.path.join(script_dir, 'service_account.json')

# Construct the full path to the experience JSON file
# This assumes app.py saves the JSON file directly into the 'server' directory
# where sheet.py also resides.
BASE_DATA_INPUT_DIR = os.path.join(script_dir, "..", "company_urls")
EXPERIENCE_JSON_FILE_PATH = os.path.join(BASE_DATA_INPUT_DIR, json_file_name)

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

#SPREADSHEET_ID = '11-81uSoERbeJ_2L5-YeEFZhYKMNx58SaG3AIH7Jq-4E'
TARGET_WORKSHEET_NAME = sheet_tab_name


def append_profile_experience_to_sheet():
    scope = ['https://www.googleapis.com/auth/spreadsheets']

    try:
        # Use the fully qualified path for the service account file
        creds = ServiceAccountCredentials.from_json_keyfile_info(SERVICE_ACCOUNT_INFO, scope)
        client = gspread.authorize(creds)
    except Exception as e:
        # Removed the unicode character (❌) to prevent UnicodeEncodeError
        print(f"Authentication Error: Ensure '{SERVICE_ACCOUNT_FILE_PATH}' is correct and present in the same directory as sheet.py. Details: {e}")
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
        print(f"Worksheet '{TARGET_WORKSHEET_NAME}' not found in spreadsheet '{SPREADSHEET_ID}'. Please check the tab name.")
        return False
    except Exception as e:
        # Removed the unicode character (❌)
        print(f"Error opening Google Sheet or Worksheet. Details: {e}")
        return False

    # Check if the JSON data file exists using its full path
    if not os.path.exists(EXPERIENCE_JSON_FILE_PATH):
        # Removed the unicode character (❌)
        print(f"Error: The JSON file '{EXPERIENCE_JSON_FILE_PATH}' was not found. Please ensure app.py has run and saved data.")
        return False

    try:
        # Open the JSON data file using its full path
        with open(EXPERIENCE_JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            profile_data_list = json.load(f)

        if not profile_data_list or not isinstance(profile_data_list, list):
            # Removed the unicode character (ℹ️)
            print(f"No valid list of profile data found in '{EXPERIENCE_JSON_FILE_PATH}'. Nothing to append.")
            return False

        # --- Handle Headers (Append only if the sheet is empty) ---
        current_first_row = sheet.row_values(1)
        if not current_first_row or all(c == '' for c in current_first_row):
            headers = [
                'Profile Name', 'Profile URL',
                'Company 1', 'Title 1', 'Duration 1',
                'Company 2', 'Title 2', 'Duration 2',
                'Company 3', 'Title 3', 'Duration 3'
            ]
            sheet.append_row(headers)
            # Removed the unicode character (✅)
            print("Headers added to Google Sheet.")

        # --- MODIFIED LOGIC: Loop through each profile in the list ---
        for current_profile in profile_data_list:
            if not isinstance(current_profile, dict):
                # Removed the unicode character (⚠️)
                print(f"Skipping invalid profile entry: {current_profile}")
                continue

            profile_name = current_profile.get('profileName', 'N/A')
            profile_url = current_profile.get('profileUrl', 'N/A')
            experiences = current_profile.get('experiences', [])

            row_to_append = [profile_name, profile_url]

            for i in range(3):
                if i < len(experiences):
                    exp = experiences[i]
                    row_to_append.append(exp.get('company', ''))
                    row_to_append.append(exp.get('jobTitle', ''))
                    row_to_append.append(exp.get('duration', ''))
                else:
                    row_to_append.extend(['', '', ''])

            sheet.append_row(row_to_append)
            # Removed the unicode character (✅)
            print(f"Data for '{profile_name}' successfully appended to Google Sheet in tab '{TARGET_WORKSHEET_NAME}'!")

        # Removed the unicode character (🎉)
        print(f"Finished processing all {len(profile_data_list)} profiles from '{EXPERIENCE_JSON_FILE_PATH}'.")
        return True

    except json.JSONDecodeError:
        # Removed the unicode character (❌)
        print(f"Error: Could not decode JSON from '{EXPERIENCE_JSON_FILE_PATH}'. The file might be empty or corrupted.")
        return False
    except Exception as e:
        # Removed the unicode character (❌)
        print(f"An unexpected error occurred during data processing or sheet update: {e}")
        return False

if __name__ == '__main__':
    append_profile_experience_to_sheet()
