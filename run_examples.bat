@echo off
REM ==============================================================================
REM 사용 예제 실행 스크립트
REM Usage Examples Runner
REM ==============================================================================

cd /d "%~dp0"
title 원단 원가 계산기 - 사용 예제

echo ==============================================================================
echo 원단 원가 계산기 - 사용 예제
echo Fabric Cost Calculator - Usage Examples
echo ==============================================================================
echo.
echo 실행할 예제를 선택하세요:
echo Select an example to run:
echo.
echo   1. 기본 계산 예제 (Basic Calculation)
echo   2. 다중 시나리오 계산 (Multiple Scenarios)
echo   3. 원사 관리 (Yarn Management)
echo   4. 계산 이력 관리 (History Management)
echo   5. Excel 내보내기 (Excel Export)
echo   6. 전체 예제 실행 (Run All Examples)
echo   0. 종료 (Exit)
echo.
set /p CHOICE="선택 (Select): "

if "%CHOICE%"=="1" (
    echo.
    echo [1/5] 기본 계산 예제 실행...
    python example_usage.py basic
) else if "%CHOICE%"=="2" (
    echo.
    echo [2/5] 다중 시나리오 계산 실행...
    python example_usage.py scenarios
) else if "%CHOICE%"=="3" (
    echo.
    echo [3/5] 원사 관리 예제 실행...
    python example_usage.py yarn
) else if "%CHOICE%"=="4" (
    echo.
    echo [4/5] 계산 이력 관리 예제 실행...
    python example_usage.py history
) else if "%CHOICE%"=="5" (
    echo.
    echo [5/5] Excel 내보내기 예제 실행...
    python example_usage.py excel
) else if "%CHOICE%"=="6" (
    echo.
    echo [전체 예제] 모든 예제를 순차적으로 실행합니다...
    python example_usage.py
) else if "%CHOICE%"=="0" (
    echo.
    echo 종료합니다.
    exit /b 0
) else (
    echo.
    echo [오류] 잘못된 선택입니다.
    pause
    exit /b 1
)

echo.
echo ==============================================================================
echo 실행 완료!
echo Press any key to exit...
pause >nul
