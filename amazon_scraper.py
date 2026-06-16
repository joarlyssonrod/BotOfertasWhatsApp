import os
import sys
import re
import urllib.parse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Configura o stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

def ler_env_local():
    """Le o arquivo .env local de forma robusta e sem dependencias externas"""
    env_data = {}
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove aspas se houver
                    value = value.strip('"').strip("'")
                    env_data[key.strip()] = value.strip()
    return env_data

def parse_cookies_amazon(cookie_str, domain=".amazon.com.br"):
    """Converte a string de cookies do .env no formato do Playwright"""
    cookies = []
    if not cookie_str:
        return cookies
    parts = cookie_str.split(";")
    for part in parts:
        part = part.strip()
        if "=" in part:
            name, value = part.split("=", 1)
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": domain,
                "path": "/"
            })
    return cookies

def buscar_promocoes_amazon(query, desconto_minimo=10, limite=5):
    """
    Busca promocoes na Amazon para uma determinada query.
    Utiliza os cookies do .env para contornar bloqueios/captchas.
    """
    print(f"🔍 [Amazon] Garimpando ofertas para: '{query}'...")
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.amazon.com.br/s?k={encoded_query}"
    
    env = ler_env_local()
    cookie_str = env.get("AMAZON_COOKIES", "")
    
    html = ""
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        
        # Cria um contexto
        contexto = navegador.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.0.0",
            locale="pt-BR"
        )
        
        # Injeta cookies da Amazon se configurados
        if cookie_str:
            try:
                cookies = parse_cookies_amazon(cookie_str)
                contexto.add_cookies(cookies)
                print(f"   [Amazon] {len(cookies)} cookies injetados com sucesso.")
            except Exception as ce:
                print(f"   [Amazon] Erro ao injetar cookies: {ce}")
        else:
            print("   ⚠️ [Amazon] AMAZON_COOKIES nao configurados no .env")
            
        pagina = contexto.new_page()
        
        try:
            pagina.goto(url, timeout=30000)
            pagina.wait_for_load_state("domcontentloaded")
            
            # Espera carregar os blocos de busca
            try:
                pagina.locator("div[data-component-type='s-search-result']").first.wait_for(state="visible", timeout=7000)
            except:
                pagina.wait_for_timeout(3000)
                
            html = pagina.content()
        except Exception as e:
            print(f"   🚨 [Amazon] Erro ao carregar pagina de busca: {e}")
        finally:
            navegador.close()
            
    if not html:
        return []
        
    soup = BeautifulSoup(html, "html.parser")
    products_divs = soup.find_all("div", {"data-component-type": "s-search-result"})
    
    ofertas_validas = []
    asins_vistos = set()
    
    for div in products_divs:
        try:
            # 1. Titulo
            title_elem = div.find("h2")
            if not title_elem:
                continue
            titulo = title_elem.text.strip()
            
            # 2. Link
            link_elem = div.find("a", class_="a-link-normal")
            if not link_elem:
                continue
            href = link_elem.get("href", "")
            link_bruto = "https://www.amazon.com.br" + href if href.startswith("/") else href
            # Pula anúncios patrocinados da Amazon
            if "sspa/click" in link_bruto or not link_bruto:
                continue
            # Limpa o link de parametros adicionais
            link_bruto = link_bruto.split("?")[0].split("#")[0]
            
            # Extrai o ASIN para evitar produtos duplicados na mesma busca
            asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', link_bruto, re.IGNORECASE)
            if asin_match:
                asin = asin_match.group(1).upper()
                if asin in asins_vistos:
                    continue
                asins_vistos.add(asin)
            
            # 3. Precos (Atual e Antigo)
            preco_atual = 0.0
            preco_original = 0.0
            
            # Preco Atual: Procuramos por .a-price que NAO tenha a classe .a-text-price
            price_elem = div.find("span", {"class": "a-price"})
            if price_elem and "a-text-price" not in price_elem.get("class", []):
                offscreen = price_elem.find("span", {"class": "a-offscreen"})
                price_text = offscreen.text if offscreen else price_elem.text
                price_clean = price_text.replace("R$", "").strip().replace(".", "").replace(",", ".")
                preco_atual = float(price_clean)
                
            # Preco Antigo: Procuramos por .a-price.a-text-price
            old_price_elem = div.find("span", class_="a-text-price")
            if old_price_elem:
                offscreen_old = old_price_elem.find("span", {"class": "a-offscreen"})
                old_price_text = offscreen_old.text if offscreen_old else old_price_elem.text
                old_price_clean = old_price_text.replace("R$", "").strip().replace(".", "").replace(",", ".")
                preco_original = float(old_price_clean)
                
            # Se nao achou preco atual, pula
            if preco_atual == 0.0:
                continue
                
            desconto = 0.0
            if preco_original > preco_atual:
                desconto = ((preco_original - preco_atual) / preco_original) * 100
                
            # Se tiver cupom listado
            coupon = None
            coupon_elem = div.find("span", class_="s-coupon-unclipped") or div.find("span", class_="a-size-base-plus")
            if coupon_elem and "cupom" in coupon_elem.text.lower():
                coupon = coupon_elem.text.strip()
                
            # 4. Imagem do produto
            img_elem = div.find("img", class_="s-image")
            img_src = img_elem.get("src") if img_elem else ""

            if desconto >= desconto_minimo or coupon:
                # Se tiver cupom mas sem desconto calculado, poe desconto ficticio de 10%
                if desconto == 0.0:
                    desconto = 10.0
                    preco_original = preco_atual * 1.11
                    
                ofertas_validas.append({
                    "titulo": titulo,
                    "preco_original": preco_original,
                    "preco_atual": preco_atual,
                    "desconto": round(desconto, 1),
                    "link_bruto": link_bruto,
                    "link_imagem": img_src
                })
                
        except Exception as e:
            continue
            
    # Ordena pelo maior desconto
    ofertas_validas = sorted(ofertas_validas, key=lambda x: x['desconto'], reverse=True)
    return ofertas_validas[:limite]

def buscar_ofertas_do_dia_amazon(desconto_minimo=10, limite=15):
    """
    Busca as ofertas em destaque diretamente da página oficial de Deals da Amazon.
    """
    print("🔥 Garimpando as 'Ofertas do Dia' oficiais da Amazon...")
    url = "https://www.amazon.com.br/deals"
    html_da_pagina = ""
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        contexto = navegador.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        )
        pagina = contexto.new_page()
        try:
            pagina.goto(url, timeout=25000)
            pagina.wait_for_load_state("domcontentloaded")
            pagina.wait_for_timeout(5000) # Aguarda renderização dos cards React
            html_da_pagina = pagina.content()
        except Exception as e:
            print(f"🚨 Erro ao acessar as ofertas da Amazon: {e}")
        finally:
            navegador.close()
            
    if not html_da_pagina:
        return []
        
    soup = BeautifulSoup(html_da_pagina, 'html.parser')
    # Procura todos os elementos de card que contêm GridItem-module__container no class
    cards = [c for c in soup.find_all("div") if any("GridItem-module__container" in cls for cls in c.get("class", []))]
    
    ofertas_validas = []
    asins_vistos = set()
    
    for card in cards:
        try:
            # 1. Link
            a_elem = card.find("a")
            if not a_elem:
                continue
            href = a_elem.get("href", "")
            if not href:
                continue
            # Limpa o link
            link_bruto = href.split("?")[0].split("#")[0]
            if not link_bruto.startswith("http"):
                link_bruto = "https://www.amazon.com.br" + link_bruto
                
            # Extrai o ASIN para evitar produtos duplicados nas ofertas do dia
            asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', link_bruto, re.IGNORECASE)
            if asin_match:
                asin = asin_match.group(1).upper()
                if asin in asins_vistos:
                    continue
                asins_vistos.add(asin)
            
            # 2. Título do produto
            titulo = ""
            title_el = card.find("p", class_=re.compile("ProductCard-module__title")) or card.find("p")
            if title_el:
                full_span = title_el.find("span", class_="a-truncate-full")
                if full_span:
                    titulo = full_span.get_text(strip=True)
                else:
                    titulo = title_el.get_text(strip=True)
            
            if not titulo or len(titulo) < 3:
                continue
            
            # 3. Imagem
            img_el = card.find("img")
            img_src = img_el.get("src") if img_el else ""
            
            # 4. Preço e Desconto
            card_text = card.get_text(" | ", strip=True)
            
            # Desconto
            desconto = 0.0
            desc_match = re.search(r'(\d+)\s*%\s*(?:off|de desconto)', card_text, re.IGNORECASE)
            if desc_match:
                desconto = float(desc_match.group(1))
            
            # Preço atual
            preco_atual = 0.0
            preco_atual_match = re.search(r'(?:Preço da Oferta:|Por:)\s*R\$\s*([\d\.,]+)', card_text, re.IGNORECASE)
            if preco_atual_match:
                preco_clean = preco_atual_match.group(1).replace(".", "").replace(",", ".")
                preco_atual = float(preco_clean)
            else:
                precos_formatados = re.findall(r'R\$\s*([\d\.,]+)', card_text)
                if precos_formatados:
                    preco_clean = precos_formatados[0].replace(".", "").replace(",", ".")
                    preco_atual = float(preco_clean)
                    
            # Preço original
            preco_original = preco_atual
            preco_orig_match = re.search(r'De:\s*R\$\s*([\d\.,]+)', card_text, re.IGNORECASE)
            if preco_orig_match:
                preco_orig_clean = preco_orig_match.group(1).replace(".", "").replace(",", ".")
                preco_original = float(preco_orig_clean)
                if desconto == 0.0 and preco_original > preco_atual:
                    desconto = ((preco_original - preco_atual) / preco_original) * 100
            
            if preco_atual > 0 and desconto >= desconto_minimo:
                ofertas_validas.append({
                    "titulo": titulo,
                    "preco_original": preco_original,
                    "preco_atual": preco_atual,
                    "desconto": round(desconto, 1),
                    "link_bruto": link_bruto,
                    "link_imagem": img_src
                })
                
        except Exception as e:
            continue
            
    # Ordena pelo maior desconto
    ofertas_validas = sorted(ofertas_validas, key=lambda x: x['desconto'], reverse=True)
    return ofertas_validas[:limite]

if __name__ == "__main__":
    # Teste rapido
    ofertas = buscar_promocoes_amazon("Kindle", desconto_minimo=5, limite=2)
    if ofertas:
        print(f"\n✅ [Amazon] Encontramos {len(ofertas)} ofertas:")
        for o in ofertas:
            print(f"- {o['titulo'][:40]}... | Preco: R$ {o['preco_atual']} (De: R$ {o['preco_original']}) | Desconto: {o['desconto']}%")
            print(f"  Link: {o['link_bruto']}\n")
    else:
        print("🤷‍♂️ [Amazon] Nenhuma oferta encontrada.")
