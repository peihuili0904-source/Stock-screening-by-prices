@echo off
cd /d "%~dp0"
python fnguide_download.py >> run.log 2>&1
