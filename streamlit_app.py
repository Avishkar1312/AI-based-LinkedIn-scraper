import streamlit as st
import subprocess
import os
import psutil # For checking if a process is running
import sys    # <--- NEW: Import sys to get the current Python executable

st.set_page_config(page_title="LinkedIn Scraper UI", layout="centered")

st.title("🔗 LinkedIn Scraper Automation")

st.markdown("""
This interface helps you manage and automate the data transfer from your LinkedIn Scraper extension to Google Sheets.

**Important Notes:**
* **Ensure Google Sheet Setup:** Your Google Sheet must be properly connected to your Python scripts (e.g., via `gspread` or similar authentication) and the tabs you specify below must exist.
* **`app.py` Backend:** The `app.py` backend server **must be running** for your Chrome extension to send data. Use the controls below to start and stop it.
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

# --- HIGHLIGHTED CHANGE START ---
google_sheet_id = st.text_input(
    "Google Spreadsheet ID:",
    value="11-81uSoERbeJ_2L5-YeEFZhYKMNx58SaG3AIH7Jq-4E", # Your current hardcoded ID
    help="Enter the ID of your Google Spreadsheet. You can find this in the sheet's URL (e.g., docs.google.com/spreadsheets/d/THIS_IS_THE_ID/edit)."
)
# --- HIGHLIGHTED CHANGE END ---

# Input fields for dynamic names
mass_scrape_json_filename = st.text_input(
    "JSON File Name for Mass Scraped URLs (from Extension):",
    value="mass_scraped_urls.json",
    help="This is the name of the JSON file where your extension stores mass-scraped URLs and names. Ensure your extension uses this name."
)

individual_profile_json_filename = st.text_input(
    "JSON File Name for Individual Profile Data (from app.py):",
    value="individual_profiles_data.json",
    help="This is the name of the JSON file where `app.py` stores individual profile details. This name will be passed to `app.py` via an environment variable."
)

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

st.header("2. Manage `app.py` (Backend Server)")

app_status_placeholder = st.empty()

def update_app_status():
    if is_app_py_running():
        app_status_placeholder.success(f"🟢 `app.py` is running (PID: {st.session_state.app_process.pid})")
    else:
        app_status_placeholder.error("🔴 `app.py` is not running.")

update_app_status() # Initial status display

col1, col2 = st.columns(2)

# Get the path to the Python executable from the current environment
python_executable = sys.executable # <--- NEW: Get the current Python executable

with col1:
    if st.button("▶️ Start scraper ", disabled=is_app_py_running()):
        st.info(f"Starting `app.py` using Python executable: `{python_executable}` with `INDIVIDUAL_PROFILE_JSON_NAME` set to: `{individual_profile_json_filename}`...")
        try:
            # Set environment variable for the subprocess
            env_vars = os.environ.copy()
            env_vars["INDIVIDUAL_PROFILE_JSON_NAME"] = individual_profile_json_filename

            # Start app.py in the background
            # We assume app.py is in a 'server' subdirectory relative to this script
            script_path = os.path.join("server", "app.py")
            if not os.path.exists(script_path):
                st.error(f"Error: `app.py` not found at '{script_path}'. Please ensure it's in the 'server' subdirectory.")
            else:
                st.session_state.app_process = subprocess.Popen(
                    [python_executable, script_path], # <--- CHANGED: Use python_executable
                    env=env_vars,
                    stdout=subprocess.PIPE, # Capture output
                    stderr=subprocess.PIPE, # Capture errors
                    text=True # Decode stdout/stderr as text
                )
                st.success(f"`app.py` started successfully with PID: {st.session_state.app_process.pid}")
                st.warning("Keep this Streamlit app open while `app.py` is running.")
                update_app_status()
        except Exception as e:
            st.error(f"Failed to start `app.py`: {e}")
            st.session_state.app_process = None # Clear process if failed
            update_app_status()

with col2:
    if st.button("⏹️ Stop scraper", disabled=not is_app_py_running()):
        if st.session_state.app_process:
            st.info("Attempting to stop `app.py`...")
            try:
                st.session_state.app_process.terminate() # Send SIGTERM
                st.session_state.app_process.wait(timeout=5) # Wait for it to terminate
                if st.session_state.app_process.poll() is not None:
                    st.success("`app.py` stopped successfully.")
                else:
                    st.warning("`app.py` did not terminate gracefully, attempting to kill...")
                    st.session_state.app_process.kill() # Force kill if terminate fails
                    st.session_state.app_process.wait()
                    st.success("`app.py` forcefully stopped.")

                # Display any output/errors from app.py
                stdout, stderr = st.session_state.app_process.communicate()
                if stdout:
                    st.subheader("`app.py` Output:")
                    st.code(stdout)
                if stderr:
                    st.subheader("`app.py` Errors:")
                    st.code(stderr)

            except Exception as e:
                st.error(f"Error stopping `app.py`: {e}")
            finally:
                st.session_state.app_process = None
                update_app_status()
        else:
            st.warning("`app.py` process not found in session state.")
            st.session_state.app_process = None # Ensure state is clean
            update_app_status()

st.markdown("---")

st.header("3. Run Scraper Operations")

st.info("Ensure your Chrome extension has been used to collect data into the specified JSON files before running these operations.")

# Button to run sheet_mass.py
if st.button("🚀 Update Mass Scraped Data to Google Sheet"):
    st.write(f"Running `sheet_mass.py` with JSON: `{mass_scrape_json_filename}`, Tab: `{mass_sheet_tab_name}`, and Sheet ID: `{google_sheet_id}`...")
    try:
        # --- HIGHLIGHTED CHANGE START ---
        # Pass the Google Sheet ID as a new argument
        command = [python_executable, os.path.join("server", "sheet_mass.py"), mass_scrape_json_filename, mass_sheet_tab_name, google_sheet_id]
        # --- HIGHLIGHTED CHANGE END ---
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
        # --- HIGHLIGHTED CHANGE START ---
        # Pass the Google Sheet ID as a new argument
        command = [python_executable, os.path.join("server", "sheet.py"), individual_profile_json_filename, individual_sheet_tab_name, google_sheet_id]
        # --- HIGHLIGHTED CHANGE END ---
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
1.  **Save this code:** Save the code above as `streamlit_app.py` in the **parent directory** of your `server` folder (i.e., at the same level as `server`, `filtering`, etc.).
2.  **Install Streamlit and psutil:** If you haven't already, install them: `pip install streamlit psutil`
3.  **Make changes to your scripts (as previously instructed).**
4.  **Activate your virtual environment (`env_scrap`).**
5.  **Run Streamlit:** Open your terminal, navigate to the directory where you saved `streamlit_app.py`, and run: `streamlit run streamlit_app.py`
6.  A new tab will open in your web browser with the UI.
""")
