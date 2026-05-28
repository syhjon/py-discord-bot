#!/bin/bash
source .venv/bin/activate
python -m watchdog.watchmedo auto-restart --directory='.' --pattern='*.py' --recursive -- python main.py