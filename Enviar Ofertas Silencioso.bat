@echo off
title Rodando Bot em Segundo Plano 🤖
cd /d "%~dp0"
call "Enviar Ofertas.bat" --headless
