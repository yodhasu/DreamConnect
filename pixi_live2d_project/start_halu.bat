@echo off
start call start_backend.bat
call..\venv\SCripts\activate
python make_widget.py
