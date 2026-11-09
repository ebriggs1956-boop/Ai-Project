@echo off
cd /d "%~dp0"
python -m streamlit run summarize.py
pause