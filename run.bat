@echo off
REM ==============================================================================
REM 원단 원가 계산기 실행 스크립트
REM Fabric Cost Calculator Launcher
REM ==============================================================================

REM 콘솔 창 제목 설정
title 원단 원가 계산기

REM 배치 파일이 있는 디렉토리로 이동
cd /d "%~dp0"

echo ==============================================================================
REM ANSI 색상 지원 (Windows 10+)
for /F "tokens=4 delims= " %%i in ('ver') do set VERSION=%%i
echo %VERSION% | findstr /C:"10." >nul
if %ERRORLEVEL% EQU 0 (
    echo [선택사항] 가상환경(venv)을 사용하시겠습니까? (Y/N)
    echo [Optional] Use virtual environment (venv)? (Y/N)
    echo.
)

set /p USE_VENV="가상환경 사용 여부 (Use venv) [Y/N]: "

REM 대소문자 구분없이 처리
if /i "%USE_VENV%"=="Y" (
    if exist venv\Scripts\activate.bat (
        echo.
        echo 가상환경을 활성화합니다...
        echo Activating virtual environment...
        call venv\Scripts\activate.bat
    ) else (
        echo.
        echo [경고] venv 폴더를 찾을 수 없습니다.
        echo [Warning] venv folder not found.
        echo 시스템 Python을 사용합니다...
        echo Using system Python...
        echo.
    )
)

echo.
echo 원단 원가 계산기를 시작합니다...
echo Starting Fabric Cost Calculator...
echo ==============================================================================
echo.

REM Python 설치 확인
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [오류] Python이 설치되지 않았습니다.
    echo [Error] Python is not installed.
    echo.
    echo Python을 다운로드하려면 https://www.python.org/downloads/ 를 방문하세요.
    echo Visit https://www.python.org/downloads/ to download Python.
    echo.
    pause
    exit /b 1
)

REM 메인 애플리케이션 실행
python main.py

REM 실행 종료 후 메시지
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ==============================================================================
    echo [오류] 프로그램 실행 중 오류가 발생했습니다.
    echo [Error] An error occurred while running the program.
    echo.
    echo 필수 라이브러리 설치:
    echo Required libraries installation:
    echo   pip install openpyxl
    echo.
    pause
    exit /b 1
)

echo.
echo 프로그램이 종료되었습니다.
echo Program terminated.
pause
