@echo off
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt -q
if not exist .env (
    copy .env.example .env
    echo Created .env from template - please fill in your credentials before running again.
    pause
    exit /b
)
echo Starting Operation Motorsport Dashboard on http://localhost:5055
start "" http://localhost:5055
python app.py
