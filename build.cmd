@echo off
echo ========================================================
echo   🎙️ Transcriptor.app - Configuración y Arranque
echo ========================================================
echo.

:: 1. Instalar FFmpeg con winget
echo [1/3] Verificando e instalando FFmpeg (necesario para Whisper ASR)...
winget install --id=Gyan.FFmpeg -e --silent
if %ERRORLEVEL% NEQ 0 (
    echo [!] Winget no pudo instalar FFmpeg automáticamente. 
    echo [!] Por favor, asegúrate de tener FFmpeg instalado manualmente.
) else (
    echo [OK] FFmpeg instalado correctamente.
)

echo.
:: 2. Instalar dependencias de Python
echo [2/3] Instalando dependencias de Python...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [!] Error al instalar las dependencias.
    pause
    exit /b %ERRORLEVEL%
)

echo.
:: 3. Arrancar la aplicación
echo [3/3] Iniciando Streamlit...
streamlit run transcriptor.py

pause
