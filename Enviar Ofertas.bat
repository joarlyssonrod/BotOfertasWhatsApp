@echo off
title Executando Bot de Ofertas 🤖
cd /d "%~dp0"

echo ====================================================
echo 🔍 Verificando dependencias...
echo ====================================================

:: Verifica se o Python esta no PATH
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo 🚨 ERRO: O Python nao foi encontrado instalado ou nao esta no PATH do Windows!
    echo Por favor, instale o Python 3.10 ou superior e marque a opcao "Add Python to PATH".
    echo.
    pause
    exit /b
)

:: Tenta importar os modulos necessarios e iniciar o chromium para garantir que tudo esta funcional
python -c "import bs4; from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(headless=True).close(); p.stop()" >nul 2>&1
if errorlevel 1 (
    echo 📦 Dependencias ausentes detectadas.
    echo 📦 Instalando dependencias: playwright, beautifulsoup4...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 🚨 Erro ao instalar dependencias com o pip.
        pause
        exit /b
    )
    echo 🌐 Instalando navegadores do Playwright...
    python -m playwright install chromium
)

echo.
echo ====================================================
echo 🚀 Iniciando o Bot de Ofertas...
echo ====================================================
echo.
set PYTHONUTF8=1
python motor_integrado.py
echo.
echo ====================================================
echo 🏁 Execucao concluida!
echo ====================================================
echo.
pause
