#!/bin/bash
cd /home/ubuntu/BotOfertasWhatsApp

# Define variáveis de ambiente necessárias
export PATH=$PATH:/home/ubuntu/.local/bin:/usr/bin
export PYTHONUTF8=1
export PYTHONUNBUFFERED=1

echo "==========================================" >> registro_execucao.txt
echo "🚀 Início da Rodada: $(date)" >> registro_execucao.txt

# Executa o bot em modo headless
python3 -u motor_integrado.py --headless >> registro_execucao.txt 2>&1

echo "🏁 Fim da Rodada: $(date)" >> registro_execucao.txt
