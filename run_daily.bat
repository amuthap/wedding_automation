@echo off
cd /d "C:\Users\amuth\OneDrive\Documents\python\textScrape"
python scrape_names.py
if %errorlevel%==0 (
    python birthday_script.py
)
