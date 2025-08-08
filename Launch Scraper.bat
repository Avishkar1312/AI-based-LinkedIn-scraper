@echo off
REM Navigate to the directory where this batch file is located
cd /d "%~dp0"

echo Activating virtual environment...
REM Call the activate.bat script for the virtual environment (explicitly using .bat)
call .\env_scraper\Scripts\activate.bat

REM Check if activation was successful (optional, but good for debugging)
if exist ".\env_scrap\Scripts\python.exe" (
    echo Virtual environment activated.
) else (
    echo Error: Virtual environment activation failed. Check path or setup.
    pause
    exit /b 1
)

echo Starting Streamlit application...
REM --- CRITICAL CHANGE: Use the full path to streamlit.exe within the virtual environment ---
.\env_scrap\Scripts\streamlit run streamlit_app.py
REM Keep the window open after Streamlit starts (optional, but good for debugging)
pause