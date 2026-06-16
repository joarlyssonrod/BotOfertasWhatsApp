import os
import json
import re
import sys

# Configura o stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

# Caminhos dos arquivos
env_telegram_path = r"C:\Users\jrgrangeiro\Documents\BotTelegramPromocoes\.env"
env_local_path = r"c:\Users\jrgrangeiro\Documents\BotMercadoLivre\.env"
sessao_ml_path = r"c:\Users\jrgrangeiro\Documents\BotMercadoLivre\sessao_ml.json"

def obter_cookies_ml():
    # Tenta ler do .env do Telegram primeiro
    if os.path.exists(env_telegram_path):
        with open(env_telegram_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MERCADO_LIVRE_COOKIES="):
                    # Pega o valor e remove as aspas se houver
                    val = line.split("=", 1)[1].strip()
                    val = val.strip('"').strip("'")
                    return val
                    
    # Tenta ler do .env local
    if os.path.exists(env_local_path):
        with open(env_local_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MERCADO_LIVRE_COOKIES="):
                    val = line.split("=", 1)[1].strip()
                    val = val.strip('"').strip("'")
                    return val
    return None

def main():
    cookie_str = obter_cookies_ml()
    if not cookie_str:
        print("🚨 Erro: Não foi possível encontrar a variável MERCADO_LIVRE_COOKIES nos arquivos .env!")
        return
        
    print(f"✅ Cookies encontrados! Tamanho da string: {len(cookie_str)} caracteres.")
    
    # Adiciona a chave MERCADO_LIVRE_COOKIES no .env local se não existir
    if os.path.exists(env_local_path):
        with open(env_local_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "MERCADO_LIVRE_COOKIES=" not in content:
            with open(env_local_path, "a", encoding="utf-8") as f:
                f.write(f"\nMERCADO_LIVRE_COOKIES={cookie_str}\n")
            print("💾 Variável MERCADO_LIVRE_COOKIES copiada para o .env local.")
            
    # Converte os cookies para o formato do Playwright (JSON)
    cookies_list = []
    
    # Expressão regular ou split simples para separar os cookies
    parts = cookie_str.split(";")
    for part in parts:
        part = part.strip()
        if not part or "=" not in part:
            continue
            
        name, value = part.split("=", 1)
        name = name.strip()
        value = value.strip()
        
        # Formato de cookie do Playwright
        cookies_list.append({
            "name": name,
            "value": value,
            "domain": ".mercadolivre.com.br",
            "path": "/",
            "expires": 1800000000,  # Data no futuro distante
            "httpOnly": False,
            "secure": True,
            "sameSite": "Lax"
        })
        
    # Adiciona domínio alternativo sem .br se necessário
    # (Playwright lê ambos)
    # cookies_list_extra = []
    # for c in cookies_list:
    #     c_alt = c.copy()
    #     c_alt["domain"] = ".mercadolivre.com"
    #     cookies_list_extra.append(c_alt)
    # cookies_list.extend(cookies_list_extra)
    
    storage_state = {
        "cookies": cookies_list,
        "origins": []
    }
    
    # Salva no arquivo JSON
    with open(sessao_ml_path, "w", encoding="utf-8") as f:
        json.dump(storage_state, f, indent=4, ensure_ascii=False)
        
    print(f"🎉 Sucesso! {len(cookies_list)} cookies convertidos e salvos em '{sessao_ml_path}'.")
    print("Agora você não precisa mais rodar salvar_login.py nem passar pelo reCAPTCHA!")

if __name__ == "__main__":
    main()
