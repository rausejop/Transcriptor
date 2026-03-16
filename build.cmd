@echo off
:: ========================================================
:: 🛡️ CONFIANZA23 - Secure SDLC v15
:: Project: Transcriptor.app (Professional Edition)
:: Description: Automated Zero-Touch Deployment Script
:: Platform: Microsoft Windows 11
:: ========================================================

setlocal enabledelayedexpansion

:: Aesthetic Header
color 0B
echo.
echo  ########################################################
echo  #                                                      #
echo  #    Transcriptor.app - Professional Deployment        #
echo  #          Standards: Secure SDLC v15                  #
echo  #                                                      #
echo  ########################################################
echo.

:: 1. FFmpeg Validation and Installation
echo [TASK 1/3] Validating Multimedia Engine (FFmpeg)...
where ffmpeg >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] FFmpeg not found. Initiating secure installation via Winget...
    winget install --id=Gyan.FFmpeg -e --silent
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Automatic installation failed. 
        echo [ADVISORY] Please install FFmpeg manually and add it to PATH.
    ) else (
        echo [OK] FFmpeg successfully installed and registered.
    )
) else (
    echo [OK] FFmpeg already presence in system.
)

echo.
:: 2. Python Environment & Dependencies
echo [TASK 2/3] Synchronizing Python Dependencies...
pip install --quiet --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Dependency synchronization failed.
    echo [ACTION] Please check your network connection and requirements.txt.
    pause
    exit /b %ERRORLEVEL%
)
echo [OK] All dependencies successfully synchronized.

echo.
:: 3. Application Launch
echo [TASK 3/3] Orchestrating Application Startup...
echo [INFO] Target: src/transcriptor.py
echo [INFO] Logging: Structured JSON (Loguru Enabled)
echo.
streamlit run src/transcriptor.py

:: Automatic cleanup/pause for diagnostic
if %ERRORLEVEL% NEQ 0 (
    echo [CRITICAL] Application terminated with exit code %ERRORLEVEL%.
    pause
)

endlocal
