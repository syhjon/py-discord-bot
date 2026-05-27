#!/bin/bash
source venv/bin/activate
python3 -m watchdog.watchmedo auto-restart --directory='.' --pattern='*.py' --recursive -- python3 main.py