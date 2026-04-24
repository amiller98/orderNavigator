@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\streamlit.exe" (
  echo [orderNavigator] No virtualenv found.
  echo Run:  python -m venv .venv
  echo Then:  .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)

rem Override .streamlit/config.toml server.headless so the browser opens.
".venv\Scripts\streamlit.exe" run app.py --server.headless false

endlocal
