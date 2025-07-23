from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import re # Import the regular expression module

app = Flask(__name__)
CORS(app) # ✅ Enables CORS for all routes

# --- HIGHLIGHTED CHANGE START ---
# Get the directory of the current script (app.py), which is 'server'
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the base output directory for JSON files to be 'company_urls'
# located in the parent directory of 'server' (i.e., your project root).
OUTPUT_DATA_DIR = os.path.join(script_dir, "..", "company_urls")

# Ensure the output directory exists. If it doesn't, create it.
os.makedirs(OUTPUT_DATA_DIR, exist_ok=True)
# --- HIGHLIGHTED CHANGE END ---

def extract_name_from_linkedin_url(url):
    """
    Extracts a readable name from a LinkedIn profile URL.
    Assumes URL format like: https://www.linkedin.com/in/first-name-last-name-identifier/
    """
    # Use regex to capture the part of the URL after '/in/' and before the next '/'
    match = re.search(r'linkedin\.com/in/([^/]+)', url)
    if match:
        name_part = match.group(1)

        # LinkedIn profile IDs often have alphanumeric strings at the end (e.g., -a1b2c3d4).
        # This regex removes such patterns.
        cleaned_name = re.sub(r'-\w{1,10}$', '', name_part) # Adjust the {1,10} if IDs are longer/shorter

        # Replace hyphens and dots with spaces, then title case each word
        cleaned_name = cleaned_name.replace('-', ' ').replace('.', ' ').strip()

        # Capitalize the first letter of each word
        name_words = [word.capitalize() for word in cleaned_name.split(' ') if word]
        return ' '.join(name_words)
    return "Unknown User" # Fallback name if extraction fails

@app.route('/save_urls', methods=['POST'])
def save_urls():
    data = request.json

    # --- CHANGE: Now expecting a 'urls' key from content.js, which is a list of strings ---
    urls_data = data.get('urls')

    if not urls_data:
        return jsonify({'error': 'No URLs provided'}), 400

    # ✅ Get dynamic filename or fallback to 'profile_urls'
    filename = data.get('filename', 'profile_urls')
    # --- HIGHLIGHTED CHANGE START ---
    # Construct the full path using the new OUTPUT_DATA_DIR
    filepath = os.path.join(OUTPUT_DATA_DIR, f"{filename}.json")
    # --- HIGHLIGHTED CHANGE END ---

    # Load existing profiles from the JSON file into a dictionary for efficient lookup by URL
    existing_profiles = {}
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                loaded_data = json.load(f)
                if isinstance(loaded_data, list): # Ensure loaded data is a list
                    for profile in loaded_data:
                        if 'url' in profile: # Check if the entry has a 'url' key
                            existing_profiles[profile['url']] = profile # Store the entire {'name': '...', 'url': '...'} object
            except json.JSONDecodeError:
                # If the file is empty or corrupted JSON, initialize with an empty dictionary
                existing_profiles = {}

    # --- NEW LOGIC: Process incoming URLs to extract names and merge ---
    new_profiles_added_count = 0
    for url_string in urls_data:
        # Check if the URL is new to avoid processing duplicates and to add new entries
        if url_string not in existing_profiles:
            extracted_name = extract_name_from_linkedin_url(url_string)
            new_profile_entry = {'name': extracted_name, 'url': url_string}

            existing_profiles[url_string] = new_profile_entry
            new_profiles_added_count += 1

    # Convert the dictionary of unique profiles back into a list to save as JSON
    all_profiles_to_save = list(existing_profiles.values())

    # ✅ Save merged profiles to the JSON file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # Use indent for pretty-printing the JSON
            json.dump(all_profiles_to_save, f, indent=2, ensure_ascii=False)
        # --- HIGHLIGHTED CHANGE START ---
        # Removed unicode characters
        print(f"Saved to {filepath} — {new_profiles_added_count} new profiles added, total: {len(all_profiles_to_save)}")
        return jsonify({'status': 'success', 'message': f'{new_profiles_added_count} new profiles added, total: {len(all_profiles_to_save)} profiles saved.'})
    except Exception as e:
        # Removed unicode characters
        print(f"Error saving file {filepath}: {e}")
        return jsonify({"success": False, "message": f"Error saving file: {str(e)}"}), 500
    # --- HIGHLIGHTED CHANGE END ---

# --- UPDATED ROUTE: Save Experience Details to include profile context ---
@app.route('/save_experience_details', methods=['POST'])
def save_experience_details():
    data = request.json

    # --- NOW EXPECTING profileUrl AND profileName ---
    profile_url = data.get('profileUrl')
    profile_name = data.get('profileName', 'Unknown Name') # Provide a default if name is missing
    experiences_data = data.get('experiences')

    # Basic validation
    if not profile_url or not experiences_data:
        return jsonify({'error': 'Missing profile URL or experience data'}), 400

    # --- HIGHLIGHTED CHANGE START ---
    # Construct the full path using the new OUTPUT_DATA_DIR
    # The individual profile JSON name is already dynamic via environment variable
    individual_json_filename = os.getenv("INDIVIDUAL_PROFILE_JSON_NAME", "default_individual_profiles_data.json")
    filepath = os.path.join(OUTPUT_DATA_DIR, individual_json_filename)
    # --- HIGHLIGHTED CHANGE END ---

    existing_profile_data = [] # This will hold the list of profile objects
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                loaded_data = json.load(f)
                if isinstance(loaded_data, list): # Ensure the top-level is a list
                    existing_profile_data = loaded_data
            except json.JSONDecodeError:
                # If file is empty or corrupt, treat as empty list
                existing_profile_data = []

    profile_found = False
    for i, entry in enumerate(existing_profile_data):
        # Check if a profile with this URL already exists
        if entry.get('profileUrl') == profile_url:
            # Update its experiences
            existing_profile_data[i]['experiences'] = experiences_data
            existing_profile_data[i]['profileName'] = profile_name # Also update name in case it changed
            profile_found = True
            # --- HIGHLIGHTED CHANGE START ---
            # Removed unicode characters
            print(f"Updated experiences for existing profile: {profile_name} ({profile_url})")
            # --- HIGHLIGHTED CHANGE END ---
            break

    if not profile_found:
        # Add a new entry for this profile
        existing_profile_data.append({
            'profileUrl': profile_url,
            'profileName': profile_name,
            'experiences': experiences_data
        })
        # --- HIGHLIGHTED CHANGE START ---
        # Removed unicode characters
        print(f"Added new profile and experiences: {profile_name} ({profile_url})")
        # --- HIGHLIGHTED CHANGE END ---

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_profile_data, f, indent=2, ensure_ascii=False)
        return jsonify({'status': 'success', 'message': f'Experiences for {profile_name} saved/updated.'})
    except Exception as e:
        # --- HIGHLIGHTED CHANGE START ---
        # Removed unicode characters
        print(f"Error saving experience details to {filepath}: {e}")
        return jsonify({"success": False, "message": f"Error saving experience details: {str(e)}"}), 500
    # --- HIGHLIGHTED CHANGE END ---

if __name__ == '__main__':
    # Run the Flask app on port 5000 in debug mode (useful for development)
    app.run(port=5000, debug=True)
