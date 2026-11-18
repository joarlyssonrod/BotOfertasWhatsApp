import os
import re
import json
import urllib.parse
import sys
from shopee_api import converter_link_shopee, ler_env_local
from aliexpress_api import gerar_link_afiliado_aliexpress

# Configura o stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

def obter_store_name():
    """Retorna o nome da loja Magazine Voce do usuario sem depender do Playwright"""
    env = ler_env_local()
    return env.get("MAGALU_STORE_NAME", "magazinejoarlysson")

def _converter_link_ml_api(url_limpa, affiliate_id="joarlyssonrodrigues"):
    """
    Tenta converter o link do Mercado Livre via API interna do Stripe/Linkbuilder
    usando os cookies do .env ou sessao_ml.json para gerar o short_url (/sec/...) oficial.
    """
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        import requests as cffi_requests

    env = ler_env_local()
    cookie_str = env.get("MERCADO_LIVRE_COOKIES", "")

    # Se não tiver no .env, monta a partir do sessao_ml.json
    if not cookie_str and os.path.exists("sessao_ml.json"):
        try:
            with open("sessao_ml.json", "r", encoding="utf-8") as f:
                ml_data = json.load(f)
                cookies_list = ml_data.get("cookies", [])
                cookie_pairs = [f"{c['name']}={c['value']}" for c in cookies_list if "mercadoli" in c.get("domain", "")]
                cookie_str = "; ".join(cookie_pairs)
        except Exception:
            pass

    if not cookie_str:
        return None

    # Extrai _csrf se disponível nos cookies
    csrf_match = re.search(r'_csrf=([^;\s]+)', cookie_str)
    csrf_token = csrf_match.group(1) if csrf_match else ""

    endpoint = "https://www.mercadolivre.com.br/affiliate-program/api/v2/stripe/user/links"
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "cookie": cookie_str,
        "origin": "https://produto.mercadolivre.com.br",
        "referer": url_limpa,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    if csrf_token:
        headers["x-csrf-token"] = csrf_token

    payload = {
        "url": url_limpa,
        "tag": affiliate_id
    }

    try:
        if hasattr(cffi_requests, "Session") and "curl_cffi" in cffi_requests.__name__:
            resp = cffi_requests.post(endpoint, headers=headers, json=payload, impersonate="chrome110", timeout=10, verify=False)
        else:
            resp = cffi_requests.post(endpoint, headers=headers, json=payload, timeout=10, verify=False)

        if resp.status_code == 200:
            dados = resp.json()
            short_url = dados.get("short_url") or dados.get("url")
            if short_url:
                print(f"✅ Link Mercado Livre oficial (/sec/) gerado com sucesso: {short_url}")
                return short_url
    except Exception as e:
        print(f"⚠️ [ML Afiliado] Aviso ao tentar API Linkbuilder: {e}")

    return None

def gerar_link_bot(url_produto, pagina_ativa=None):
    """
    Gera instantaneamente o link de afiliado para Shopee, Amazon, Mercado Livre, Magalu ou AliExpress.
    """
    url_limpa = url_produto.strip()
    env = ler_env_local()
    
    # 1. MERCADO LIVRE
    if "mercadolivre.com" in url_limpa or "mercadolibre.com" in url_limpa:
        # Remove parâmetros de afiliados de terceiros (como Promobit matt_tool_id=76706625)
        url_limpa = url_limpa.split("?")[0].split("#")[0]
        affiliate_id = env.get("ML_AFFILIATE_ID", "joarlyssonrodrigues")
        
        # Tenta gerar o link curto oficial /sec/ via API do Linkbuilder
        link_sec = _converter_link_ml_api(url_limpa, affiliate_id)
        if link_sec:
            return link_sec
            
        # Fallback com parâmetros de campanha limpa
        link_afiliado = f"{url_limpa}?matt_word={affiliate_id}&affiliate={affiliate_id}"
        print(f"✅ Link Mercado Livre convertido (fallback): {link_afiliado}")
        return link_afiliado
        
    # 2. AMAZON
    elif "amazon.com" in url_limpa:
        decoded_link = urllib.parse.unquote(url_limpa)
        asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', decoded_link, re.IGNORECASE)
        affiliate_tag = env.get("AMAZON_AFFILIATE_TAG", "jrodrigues07-20")
        
        if asin_match:
            asin = asin_match.group(1)
            link_afiliado = f"https://www.amazon.com.br/dp/{asin}?tag={affiliate_tag}"
        else:
            url_limpa = url_limpa.split("?")[0].split("#")[0]
            link_afiliado = f"{url_limpa}?tag={affiliate_tag}"
            
        print(f"✅ Link Amazon convertido instantaneamente: {link_afiliado}")
        return link_afiliado
        
    # 3. MAGAZINE LUIZA
    elif "magazineluiza.com.br" in url_limpa or "magazinevoce.com.br" in url_limpa:
        store_name = obter_store_name()
        if "magazinevoce.com.br" in url_limpa:
            # Garante que usa o store_name correto no link de divulgador
            url_convertida = re.sub(r'magazinevoce\.com\.br/[a-zA-Z0-9_-]+', f'magazinevoce.com.br/{store_name}', url_limpa)
            url_convertida = url_convertida.split("?")[0].split("#")[0]
            print(f"✅ Link Magalu (Magazine Voce) já é afiliado: {url_convertida}")
            return url_convertida
        # Substitui o domínio padrão pelo seu link de divulgador
        url_convertida = url_limpa.replace("www.magazineluiza.com.br", f"www.magazinevoce.com.br/{store_name}")
        url_convertida = url_convertida.replace("magazineluiza.com.br", f"www.magazinevoce.com.br/{store_name}")
        # Remove parâmetros
        url_convertida = url_convertida.split("?")[0].split("#")[0]
        print(f"✅ Link Magalu convertido: {url_convertida}")
        return url_convertida

    # 4. SHOPEE
    elif "shopee.com" in url_limpa:
        return converter_link_shopee(url_produto)
        
    # 5. ALIEXPRESS
    elif "aliexpress.com" in url_limpa:
        return gerar_link_afiliado_aliexpress(url_produto)
        
    # Lojas não afiliadas retornam None para serem descartadas automaticamente pelo bot
    print(f"🚫 [Filtro Afiliados] Ignorando oferta de loja não afiliada: {url_limpa[:60]}...")
    return None

if __name__ == "__main__":
    # Testes rápidos de conversão
    ml_url = "https://produto.mercadolivre.com.br/MLB-5298350806-capa-chuva-motoqueiro-pvc-impermeavel-motoboy-emborrachada-_JM#position=1&tracking_id=123"
    amazon_url = "https://www.amazon.com.br/Kindle-11a-Gera%C3%A7%C3%A3o-Fic%C3%A7%C3%A3o-Preto/dp/B09T2CXSGT55/ref=sr_1_1?qid=123"
    magalu_url = "https://www.magazineluiza.com.br/smartphone-samsung-galaxy-a15-4g-128gb-preto-azul-4gb-ram-65-cam-tripla-50mp-selfie-13mp/p/238127900/te/ga15/"
    ig_url = "https://www.instant-gaming.com/pt/14842-comprar-ea-sports-fc-25-pc-jogo-ea-app/"
    shopee_url = "https://shopee.com.br/product/123/456"
    
    print("🧪 Testando conversões rápidas:")
    gerar_link_bot(ml_url)
    gerar_link_bot(amazon_url)
    gerar_link_bot(magalu_url)
    gerar_link_bot(ig_url)
    gerar_link_bot(shopee_url)