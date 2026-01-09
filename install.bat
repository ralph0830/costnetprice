@echo off
REM ==============================================================================
REM 필수 라이브러리 설치 스크립트
REM Required Libraries Installation Script
REM ==============================================================================

cd /d "%~dp0"
title 라이브러리 설치

echo ==============================================================================
echo 원단 원가 계산기 - 필수 라이브러리 설치
echo Fabric Cost Calculator - Required Libraries Installation
echo ==============================================================================
echo.

REM Python 설치 확인
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [오류] Python이 설치되지 않았습니다.
    echo [Error] Python is not installed.
    echo.
    echo Python을 다운로드하려면 아래 링크를 방문하세요:
    echo Visit the following link to download Python:
    echo   https://www.python.org/downloads/
    echo.
    echo 설치 시 "Add Python to PATH" 옵션을 체크하세요.
    echo Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python 버전:
python --version
echo.

echo pip을 업그레이드합니다...
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

echo ==============================================================================
echo 필수 라이브러리를 설치합니다...
echo Installing required libraries...
echo ==============================================================================
echo.

echo [1/1] openpyxl (Excel 파일 처리)
pip install openpyxl

echo.
echo ==============================================================================
if %ERRORLEVEL% EQU 0 (
    echo [성공] 모든 라이브러리가 설치되었습니다!
    echo [Success] All libraries installed successfully!
    echo.
    echo 이제 run.bat을 실행하여 프로그램을 시작할 수 있습니다.
    echo You can now run run.bat to start the program.
) else (
    echo [오류] 라이브러리 설치 중 문제가 발생했습니다.
    echo [Error] An error occurred during installation.
    echo.
    echo 수동으로 설치하려면:
    echo Manual installation:
    echo   pip install openpyxl
)
echo ==============================================================================
echo.
pause
