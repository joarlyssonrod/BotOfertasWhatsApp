@echo off
chcp 65001 > nul
title Gerador Sho IA - Achadinhos da Shopee
cd /d "%~dp0"
echo ====================================================
echo   GERADOR SHO IA - ARTES E LEGENDAS PARA INSTAGRAM
echo ====================================================
python gerador_sho_ia.py
echo.
echo Abrindo a pasta com os cards e legendas...
explorer posts_sho_ia
pause
