@echo off
title Fire & Smoke YOLO Detection System
echo Starting Fire & Smoke YOLO PyQt6 Application...
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe main.py %*
) else (
    python main.py %*
)
pause
