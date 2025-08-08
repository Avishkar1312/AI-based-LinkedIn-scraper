import streamlit as st
import subprocess
import os
import psutil # For checking if a process is running
import sys    # Import sys to get the current Python executable

st.set_page_config(page_title="LinkedIn Scraper UI", layout="centered")

st.title("🔗 LinkedIn Scraper Automation")

st.markdown("""
This interface helps you manage and automate the data transfer from your LinkedIn Scraper extension to Google Sheets.

**Important Notes:**
* **If you want to use a new sheets make sure you go to "Share" section and give this email "tribeca-scrapper@tribeca-scrapper-466812.iam.gserviceaccount.com" Editor access**
* **Before starting it create 2 tabs in Google sheets and name them the same thing that you would put in the below options**
""")

# Initialize session state for app.py process
if 'app_process' not in st.session_state:
    st.session_state.app_process = None

def is_app_py_running():
    """Checks if the app.py process is currently running."""
    if st.session_state.app_process and st.session_state.app_process.poll() is None:
        try:
            # Check if the process still exists in psutil (more robust)
            psutil.Process(st.session_state.app_process.pid)
            return True
        except psutil.NoSuchProcess:
            st.session_state.app_process = None # Clear if process died unexpectedly
            return False
    return False

st.header("1. Configuration")

google_sheet_id = st.text_input(
    "Google Spreadsheet ID:",
    value="13UUPWix3ux10kwe2N_4-hHpGzvzCy4v1rozGtzbm04A", # Your current hardcoded ID
    help="Enter the ID of your Google Spreadsheet. You can find this in the sheet's URL (e.g., docs.google.com/spreadsheets/d/THIS_IS_THE_ID/edit)."
)

# Input field for mass scraped URLs filename (remains)
mass_scrape_json_filename = st.text_input(
    "File Name for Mass Scraped URLs:",
    value="mass_scraped_urls.json",
    help="This is the name of the JSON file where your extension stores mass-scraped URLs and names. Ensure your extension uses this name."
)

# --- HIGHLIGHTED CHANGE START ---
# REMOVED the input field for individual_profile_json_filename.
# Now, it's derived automatically.

# Derive the individual profile JSON filename
# Remove .json extension if present, then append _profiles_data.json
base_name = os.path.splitext(mass_scrape_json_filename)[0]
individual_profile_json_filename = f"{base_name}_profiles_data.json"

st.info(f"Individual Profile Data JSON File Name (derived): `{individual_profile_json_filename}`")
# --- HIGHLIGHTED CHANGE END ---


mass_sheet_tab_name = st.text_input(
    "Google Sheet Tab Name for Mass Scraped Data:",
    value="MassScrapedLeads",
    help="The name of the tab in your Google Sheet where mass scraped data will be uploaded. This tab must exist in your Google Sheet."
)

individual_sheet_tab_name = st.text_input(
    "Google Sheet Tab Name for Individual Profile Data:",
    value="ProfileDetails",
    help="The name of the tab in your Google Sheet where individual profile details will be uploaded. This tab must exist in your Google Sheet."
)

st.header("2. Start the scraper")

app_status_placeholder = st.empty()

def update_app_status():
    if is_app_py_running():
        app_status_placeholder.success(f"🟢 Scraper is running (PID: {st.session_state.app_process.pid})")
    else:
        app_status_placeholder.error("🔴 Scraper is not running.")

update_app_status() # Initial status display

col1, col2 = st.columns(2)

# Get the path to the Python executable from the current environment
python_executable = sys.executable

with col1:
    if st.button("▶️ Start scraper ", disabled=is_app_py_running()):
        st.info(f"Starting `app.py` using Python executable: `{python_executable}` with `INDIVIDUAL_PROFILE_JSON_NAME` set to: `{individual_profile_json_filename}`...")
        try:
            # Set environment variable for the subprocess
            env_vars = os.environ.copy()
            env_vars["INDIVIDUAL_PROFILE_JSON_NAME"] = individual_profile_json_filename

            # Start app.py in the background
            script_path = os.path.join("server", "app.py")
            if not os.path.exists(script_path):
                st.error(f"Error: scraper not found at '{script_path}'. Please ensure it's in the 'server' subdirectory.")
            else:
                st.session_state.app_process = subprocess.Popen(
                    [python_executable, script_path],
                    env=env_vars,
                    stdout=subprocess.PIPE, # Capture output
                    stderr=subprocess.PIPE, # Capture errors
                    text=True # Decode stdout/stderr as text
                )
                st.success(f"scraper started successfully with PID: {st.session_state.app_process.pid}")
                st.warning("Keep this website open while scraper is running.")
                update_app_status()
        except Exception as e:
            st.error(f"Failed to start scraper`: {e}")
            st.session_state.app_process = None
            update_app_status()

with col2:
    if st.button("⏹️ Stop scraper", disabled=not is_app_py_running()):
        if st.session_state.app_process:
            st.info("Attempting to stop scraper...")
            try:
                st.session_state.app_process.terminate() # Send SIGTERM
                st.session_state.app_process.wait(timeout=5) # Wait for it to terminate
                if st.session_state.app_process.poll() is not None:
                    st.success("scraper stopped successfully.")
                else:
                    st.warning("scraper did not terminate gracefully, attempting to kill...")
                    st.session_state.app_process.kill() # Force kill if terminate fails
                    st.session_state.app_process.wait()
                    st.success("scraper forcefully stopped.")

                # Display any output/errors from app.py
                stdout, stderr = st.session_state.app_process.communicate()
                if stdout:
                    st.subheader("Scraper Output:")
                    st.code(stdout)
                if stderr:
                    st.subheader("Scraper Errors:")
                    st.code(stderr)

            except Exception as e:
                st.error(f"Error stopping scraper: {e}")
            finally:
                st.session_state.app_process = None
                update_app_status()
        else:
            st.warning("scraper process not found in session state.")
            st.session_state.app_process = None
            update_app_status()

st.markdown("---")

st.header("3. Run Scraper Operations")

st.info("Ensure your Chrome extension has been used to collect data into the specified JSON files before running these operations.")

# Button to run sheet_mass.py
if st.button("🚀 Update Mass Scraped Data to Google Sheet"):
    st.write(f"Running `sheet_mass.py` with JSON: `{mass_scrape_json_filename}`, Tab: `{mass_sheet_tab_name}`, and Sheet ID: `{google_sheet_id}`...")
    try:
        command = [python_executable, os.path.join("server", "sheet_mass.py"), mass_scrape_json_filename, mass_sheet_tab_name, google_sheet_id]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        st.success("Mass Scraped Data Updated Successfully!")
        st.subheader("Output:")
        st.code(process.stdout)
        if process.stderr:
            st.warning("Errors/Warnings from script:")
            st.code(process.stderr)
    except subprocess.CalledProcessError as e:
        st.error(f"Error updating mass scraped data: {e}")
        st.subheader("Error Output:")
        st.code(e.stderr)
    except FileNotFoundError:
        st.error("Error: `sheet_mass.py` not found. Please ensure it's in the 'server' subdirectory relative to this Streamlit app.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

st.markdown("---")

# Button to run sheet.py
if st.button("📊 Update Individual Profile Data to Google Sheet"):
    st.write(f"Running `sheet.py` with JSON: `{individual_profile_json_filename}`, Tab: `{individual_sheet_tab_name}`, and Sheet ID: `{google_sheet_id}`...")
    try:
        command = [python_executable, os.path.join("server", "sheet.py"), individual_profile_json_filename, individual_sheet_tab_name, google_sheet_id]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        st.success("Individual Profile Data Updated Successfully!")
        st.subheader("Output:")
        st.code(process.stdout)
        if process.stderr:
            st.warning("Errors/Warnings from script:")
            st.code(process.stderr)
    except subprocess.CalledProcessError as e:
        st.error(f"Error updating individual profile data: {e}")
        st.subheader("Error Output:")
        st.code(e.stderr)
    except FileNotFoundError:
        st.error("Error: `sheet.py` not found. Please ensure it's in the 'server' subdirectory relative to this Streamlit app.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

st.markdown("""
---
**Setup and Execution:**
1.  **Run the scraper and go to the People section of a Company's page on LinkedIn**.
2.  **Click the Bulk Scrape button in the extension ands wait for it to complete**.
3.  **Once it is completed click the update mass scarped button on the website to push the urls to sheets**
4.  **Enter sheets and visit each profile and click the "Current Porfile Deatils" button in the extension. Do this for all the profiles in the sheets**
5.  **Once you are done with it click Update "Individual Profile Data" button on the website**.
""")