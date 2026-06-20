import os
import sys
import re
import time
import urllib.parse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Configura o stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

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

def obter_store_name():
    """Retorna o nome da loja Magazine Voce do usuario"""
    env = ler_env_local()
    return env.get("MAGALU_STORE_NAME", "magazinejoarlysson")

def buscar_promocoes_magalu(query, desconto_minimo=10, limite=5):
    """
    Busca promocoes na Magazine Luiza usando a loja de divulgador do usuario.
    Isso evita o bloqueio 403 das paginas principais e ja gera os links de afiliado.
    """
    store_name = obter_store_name()
    print(f"🔍 [Magalu] Garimpando ofertas para: '{query}' na loja de divulgador '{store_name}'...")
    
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.magazinevoce.com.br/{store_name}/busca/{encoded_query}/"
    
    html = ""
    with sync_playwright() as p:
        # Launch chromium with anti-automation detection arguments
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            locale="pt-BR",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        # Oculta navigator.webdriver
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            response = page.goto(url, timeout=30000, wait_until="domcontentloaded")
            # Aguarda a renderizacao dos cards
            page.wait_for_timeout(3500)
            html = page.content()
        except Exception as e:
            print(f"   🚨 [Magalu] Erro ao carregar pagina de busca: {e}")
        finally:
            try:
                browser.close()
            except:
                pass
            
    if not html:
        return []
        
    soup = BeautifulSoup(html, "html.parser")
    # Em Magazine Voce, os cards de produto sao links <a> com '/p/' no href
    product_links = soup.find_all("a", href=lambda h: h and "/p/" in h)
    
    ofertas_validas = []
    seen_links = set()
    
    for a in product_links:
        try:
            # 1. Href e Link
            href = a.get("href")
            if not href or href in seen_links:
                continue
            seen_links.add(href)
            
            link_bruto = "https://www.magazinevoce.com.br" + href if href.startswith("/") else href
            
            # 2. Titulo e Imagem
            img = a.find("img")
            titulo = img.get("alt") if img else None
            if not titulo:
                h2 = a.find("h2")
                if h2:
                    titulo = h2.text.strip()
            if not titulo:
                continue
                
            img_url = ""
            if img:
                img_url = img.get("src") or img.get("data-src") or ""
                if img_url.startswith("data:"):
                    img_url = img.get("data-src") or img.get("src") or ""
            
            # 3. Precos
            p_tags = a.find_all("p")
            preco_original = 0.0
            preco_atual = 0.0
            
            pix_price = None
            first_price = None
            
            for p in p_tags:
                text = p.text.strip()
                # Verifica preco no Pix (ex: "ou R$ 4.277,07")
                if "ou R$" in text:
                    match = re.search(r'R\$\s*([\d\.,]+)', text)
                    if match:
                        price_str = match.group(1).replace(".", "").replace(",", ".")
                        pix_price = float(price_str)
                # Verifica preco normal parcelado (ex: "R$ 5.251,97")
                elif "R$" in text and "x" not in text and "de" not in text and "Cupom" not in text and "cupom" not in text:
                    match = re.search(r'R\$\s*([\d\.,]+)', text)
                    if match:
                        price_str = match.group(1).replace(".", "").replace(",", ".")
                        if not first_price:
                            first_price = float(price_str)
            
            if pix_price:
                preco_atual = pix_price
                preco_original = first_price if first_price else pix_price
            else:
                preco_atual = first_price if first_price else 0.0
                preco_original = first_price if first_price else 0.0
                
            if preco_original < preco_atual:
                preco_original = preco_atual
                
            if preco_atual <= 0:
                continue
                
            # 4. Desconto
            desconto = 0
            if preco_original > preco_atual:
                desconto = int(((preco_original - preco_atual) / preco_original) * 100)
                
            # Verifica se ha um badge de desconto
            discount_badge = a.find(class_=lambda c: c and "discount-badge" in c)
            if discount_badge:
                badge_text = discount_badge.text
                badge_match = re.search(r'(\d+)%', badge_text)
                if badge_match:
                    desconto = max(desconto, int(badge_match.group(1)))
            else:
                text_match = re.search(r'\((\d+)%\s*de\s*desconto', a.text, re.IGNORECASE)
                if text_match:
                    desconto = max(desconto, int(text_match.group(1)))
                    
            if desconto >= desconto_minimo:
                ofertas_validas.append({
                    "titulo": titulo,
                    "preco_original": preco_original,
                    "preco_atual": preco_atual,
                    "desconto": desconto,
                    "link_bruto": link_bruto,
                    "link_imagem": img_url
                })
                
            if len(ofertas_validas) >= limite:
                break
                
        except Exception as ex:
            pass
            
    return ofertas_validas

def buscar_ofertas_do_dia_magalu(desconto_minimo=10, limite=20):
    """
    Busca ofertas quentes na Magazine Luiza simulando busca por categorias de alta conversao.
    Retorna as ofertas ordenadas pelo maior desconto.
    """
    print("🔥 [Magalu] Garimpando as melhores ofertas da Magazine Luiza por termos populares...")
    termos_quentes = ["smartphone", "notebook", "fritadeira airfryer", "smart tv", "tenis masculino"]
    
    todas_ofertas = []
    seen_links = set()
    
    # Para nao estourar o limite de tempo e requisicoes, busca ate 5 ofertas por termo
    for termo in termos_quentes:
        res = buscar_promocoes_magalu(termo, desconto_minimo=desconto_minimo, limite=6)
        for item in res:
            if item["link_bruto"] not in seen_links:
                seen_links.add(item["link_bruto"])
                todas_ofertas.append(item)
        time.sleep(1.0) # Delay amigavel
        
    # Ordena pelo maior desconto e aplica o limite final
    todas_ofertas = sorted(todas_ofertas, key=lambda x: x['desconto'], reverse=True)
    return todas_ofertas[:limite]

if __name__ == "__main__":
    print("🧪 Testando Magalu Scraper em isolamento:")
    ofertas = buscar_promocoes_magalu("PlayStation 5", desconto_minimo=5, limite=3)
    for o in ofertas:
        print(f"- {o['titulo'][:45]}... | R$ {o['preco_atual']} (De R$ {o['preco_original']}) | {o['desconto']}% OFF")
        print(f"  Link: {o['link_bruto']}")
