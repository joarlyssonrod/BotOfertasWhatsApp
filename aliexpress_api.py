import os
import sys
import time
import datetime
import hashlib
import requests
import urllib3

# Suprime avisos de certificado SSL autoassinado/inseguro em redes corporativas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Habilita UTF8 para os prints no Windows
sys.stdout.reconfigure(encoding='utf-8')

# Endpoint oficial da API do AliExpress (Business Interface)
URL_ALIEXPRESS_REST = "https://api-sg.aliexpress.com/rest"

def ler_env_local():
    """Le o arquivo .env local de forma robusta e sem dependencias externas"""
    env_data = {}
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        value = value.strip('"').strip("'")
                        env_data[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️ Erro ao ler .env: {e}")
    return env_data

def calcular_assinatura(params, app_secret):
    """Calcula a assinatura MD5 no formato exigido pela API do AliExpress/Taobao"""
    sorted_keys = sorted(params.keys())
    sorted_string = "".join([f"{k}{params[k]}" for k in sorted_keys])
    string_to_sign = f"{app_secret}{sorted_string}{app_secret}"
    signature = hashlib.md5(string_to_sign.encode('utf-8')).hexdigest().upper()
    return signature

def gerar_link_afiliado_aliexpress(link_bruto):
    """
    Converte uma URL bruta do AliExpress em um link de afiliado usando a API oficial.
    """
    env = ler_env_local()
    app_key = env.get("ALIEXPRESS_APP_KEY")
    app_secret = env.get("ALIEXPRESS_APP_SECRET")
    tracking_id = env.get("ALIEXPRESS_TRACKING_ID", "default")

    if not app_key or not app_secret:
        print("⚠️ [AliExpress API] Chaves ALIEXPRESS_APP_KEY ou ALIEXPRESS_APP_SECRET não configuradas no .env")
        return None

    # Limpa link de parâmetros adicionais
    link_limpo = link_bruto.split("?")[0].split("#")[0]

    # Timestamp no formato de Cingapura/Pequim (GMT+8) para evitar desvios no servidor
    now_gmt8 = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    timestamp_str = now_gmt8.strftime("%Y-%m-%d %H:%M:%S")

    # Parâmetros de sistema obrigatórios para API Taobao/AliExpress
    params = {
        "app_key": app_key,
        "method": "aliexpress.affiliate.link.generate",
        "timestamp": timestamp_str,
        "format": "json",
        "v": "2.0",
        "sign_method": "md5",
        # Parâmetros específicos da chamada
        "promotion_link_type": "0",
        "source_values": link_limpo,
        "tracking_id": tracking_id
    }

    # Calcula e injeta assinatura
    params["sign"] = calcular_assinatura(params, app_secret)

    try:
        response = requests.post(URL_ALIEXPRESS_REST, data=params, timeout=15, verify=False)
        if response.status_code == 200:
            dados = response.json()
            # Trata erros retornados na estrutura da resposta
            error_response = dados.get("error_response")
            if error_response:
                print(f"❌ [AliExpress API] Erro retornado pela API: {error_response.get('sub_msg') or error_response.get('msg')}")
                return None
                
            resp_generate = dados.get("aliexpress_affiliate_link_generate_response")
            if resp_generate:
                resp_result = resp_generate.get("resp_result", {})
                code = resp_result.get("resp_code")
                if code == 200 or str(code) == "200":
                    links = resp_result.get("result", {}).get("promotion_links", {}).get("promotion_link", [])
                    if links:
                        link_afiliado = links[0].get("promotion_link")
                        print(f"✅ [AliExpress API] Link convertido com sucesso!")
                        return link_afiliado
                else:
                    print(f"❌ [AliExpress API] Código de erro na resposta: {code} - {resp_result.get('resp_msg')}")
            else:
                print(f"❌ [AliExpress API] Resposta em formato inesperado: {dados}")
        else:
            print(f"❌ [AliExpress API] Erro HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ [AliExpress API] Erro de rede ou parse: {e}")

    return None

if __name__ == "__main__":
    # Teste rápido
    print("🧪 Testando conversão de link AliExpress:")
    test_url = "https://www.aliexpress.com/item/1005006208649931.html"
    link = gerar_link_afiliado_aliexpress(test_url)
    print(f"Resultado: {link}")
