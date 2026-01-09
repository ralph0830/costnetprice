@echo off
REM ==============================================================================
REM 원단 원가 계산기 - 간단 실행 (GUI 바로 시작)
REM Fabric Cost Calculator - Quick Launch
REM ==============================================================================

cd /d "%~dp0"
title 원단 원가 계산기

python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [오류] 필수 라이브러리가 설치되지 않았을 수 있습니다.
    echo 설치 명령: pip install openpyxl
    pause
)
