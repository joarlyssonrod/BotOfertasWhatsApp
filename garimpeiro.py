import os
import sys
import urllib.parse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Configura o stdout para suportar UTF-8 no Windows (evita erros com emojis)
sys.stdout.reconfigure(encoding='utf-8')

def buscar_promocoes(termo, desconto_minimo=10, limite=5, headless=True):
    """
    Busca promoções no Mercado Livre para um determinado termo de busca.
    """
    print(f"🔍 [Mercado Livre Scraper] Garimpando ofertas para o termo: '{termo}'...")
    termo_url = termo.replace(" ", "-")
    url_busca = f"https://lista.mercadolivre.com.br/{urllib.parse.quote(termo_url)}"
    return _executar_scraping(url_busca, desconto_minimo, limite, headless=headless)

def buscar_ofertas_do_dia(desconto_minimo=10, limite=20, headless=True):
    """
    Busca as ofertas em destaque diretamente da página oficial de Ofertas do Dia.
    """
    print("🔥 [Mercado Livre Scraper] Garimpando as 'Ofertas do Dia' oficiais do Mercado Livre...")
    url_ofertas = "https://www.mercadolivre.com.br/ofertas"
    return _executar_scraping(url_ofertas, desconto_minimo, limite, headless=headless)

def _executar_scraping(url, desconto_minimo, limite, usar_sessao=True, headless=True):
    """
    Função interna que abre o navegador carregando a sessão logada,
    evitando CAPTCHAs, e extrai as ofertas usando BeautifulSoup.
    """
    sessao_path = "sessao_ml.json"
    html_da_pagina = ""
    redirecionado = False
    
    with sync_playwright() as p:
        # Configurações do navegador
        launch_args = {
            "headless": headless
        }
        
        # Em modo headful (visível), tenta usar o Chrome local e argumentos que ocultam automação
        if not headless:
            launch_args["channel"] = "chrome"
            launch_args["ignore_default_args"] = ["--enable-automation"]
            launch_args["args"] = [
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
            
        navegador = p.chromium.launch(**launch_args)
        
        # Carrega a sessão se ela existir e usar_sessao for True
        if usar_sessao and os.path.exists(sessao_path):
            contexto = navegador.new_context(
                storage_state=sessao_path,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
            )
        else:
            if usar_sessao:
                print("⚠️ Sessão 'sessao_ml.json' não encontrada. Rodando sem login...")
            contexto = navegador.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
            )
            
        pagina = contexto.new_page()
        # Injeta init script para esconder webdriver
        pagina.add_init_script("delete navigator.__proto__.webdriver;")
        
        try:
            pagina.goto(url, timeout=30000)
            pagina.wait_for_load_state("domcontentloaded")
            pagina.wait_for_timeout(2500) # Pequena pausa para garantir renderização do JS
            
            # Se for redirecionado para página de verificação (CAPTCHA)
            if "account-verification" in pagina.url or "captcha" in pagina.url:
                redirecionado = True
            else:
                html_da_pagina = pagina.content()
        except Exception as e:
            print(f"🚨 Erro durante o carregamento da página no Playwright: {e}")
        finally:
            navegador.close()

    if redirecionado:
        if usar_sessao and os.path.exists(sessao_path):
            print("⚠️ Bloqueio de verificação detectado com cookies de sessão. Tentando novamente como visitante sem login...")
            return _executar_scraping(url, desconto_minimo, limite, usar_sessao=False, headless=headless)
        else:
            print("🚨 Bloqueio de verificação detectado mesmo sem login! O Mercado Livre bloqueou o IP/navegador temporariamente.")
            print("👉 Por favor, execute o script 'python salvar_login.py' e conclua o login no navegador visível para obter novos cookies.")
            return []
            
    if not html_da_pagina:
        return []
        
    soup = BeautifulSoup(html_da_pagina, "html.parser")
    
    # Busca por elementos de ofertas em ambos os formatos de layout
    # Layout Grid: poly-card
    itens_grid = soup.find_all(class_=lambda c: c and "poly-card" in c)
    # Layout Lista: ui-search-layout__item
    itens_lista = soup.find_all(class_=lambda c: c and "ui-search-layout__item" in c)
    
    elementos = itens_grid if len(itens_grid) > len(itens_lista) else itens_lista
    print(f"📊 Total de itens de produto detectados na página: {len(elementos)} (Grid: {len(itens_grid)}, Lista: {len(itens_lista)})")
    
    ofertas_validas = []
    links_vistos = set()
    
    for item in elementos:
        dados = parse_item(item)
        if dados:
            link = dados["link_bruto"]
            if link not in links_vistos:
                links_vistos.add(link)
                # Filtra por desconto mínimo
                if dados["desconto"] >= desconto_minimo:
                    ofertas_validas.append(dados)
                
    # Ordena pelo maior desconto para o menor
    ofertas_validas = sorted(ofertas_validas, key=lambda x: x['desconto'], reverse=True)
    return ofertas_validas[:limite]

def parse_item(item):
    """
    Extrai título, link, imagem e preços de um elemento de produto (poly-card ou item de busca).
    """
    # 1. Título e Link
    title_elem = item.find(class_="poly-component__title") or item.find("h3") or item.find("h2")
    if not title_elem:
        return None
        
    if title_elem.name == 'a':
        a_tag = title_elem
    else:
        a_tag = title_elem.find("a")
        
    if not a_tag:
        a_tag = item.find("a")
        
    if not a_tag:
        return None
        
    titulo = a_tag.text.strip()
    link_bruto = a_tag.get("href")
    if not link_bruto:
        return None
        
    # Ignora links patrocinados/anúncios pagos que mudam a URL dinamicamente
    if "click1.mercadolivre" in link_bruto or "click.mercadolivre" in link_bruto:
        return None
        
    # Limpa a URL removendo rastreadores
    link_bruto = link_bruto.split("?")[0].split("#")[0]
    
    # 2. Imagem
    img_elem = item.find("img")
    link_imagem = None
    if img_elem:
        link_imagem = img_elem.get("src") or img_elem.get("data-src")
        # Se for um placeholder ou imagem em base64, tenta pegar do data-src
        if link_imagem and (link_imagem.startswith("data:image") or "lazyload" in link_imagem):
            link_imagem = img_elem.get("data-src") or link_imagem
            
    # 3. Preços
    price_box = item.find(class_="poly-component__price") or item.find(class_="poly-price") or item
    price_elements = price_box.find_all(class_=" Andes-money-amount") or price_box.find_all(class_=lambda c: c and "andes-money-amount" in c)
    
    preco_atual = None
    preco_original = None
    
    # Busca o preço original (marcado como previous, ou dentro de s/del)
    for p in price_elements:
        is_previous = (
            "andes-money-amount--previous" in p.get("class", []) 
            or p.name == "s" 
            or p.find_parent("s") is not None 
            or p.find_parent("del") is not None
        )
        if is_previous:
            fraction = p.find(class_="andes-money-amount__fraction")
            cents = p.find(class_="andes-money-amount__cents")
            val_str = fraction.text.replace(".", "") if fraction else "0"
            if cents:
                val_str += f".{cents.text}"
            try:
                preco_original = float(val_str)
                break
            except ValueError:
                pass
                
    # Busca o preço atual (o primeiro que não seja previous)
    for p in price_elements:
        is_previous = (
            "andes-money-amount--previous" in p.get("class", []) 
            or p.name == "s" 
            or p.find_parent("s") is not None 
            or p.find_parent("del") is not None
        )
        if not is_previous:
            fraction = p.find(class_="andes-money-amount__fraction")
            cents = p.find(class_="andes-money-amount__cents")
            val_str = fraction.text.replace(".", "") if fraction else "0"
            if cents:
                val_str += f".{cents.text}"
            try:
                preco_atual = float(val_str)
                break
            except ValueError:
                pass
                
    if preco_atual is None:
        return None
        
    if preco_original is None:
        preco_original = preco_atual
        
    # Calcula desconto (%)
    if preco_original > preco_atual:
        desconto = round(((preco_original - preco_atual) / preco_original) * 100, 1)
    else:
        desconto = 0.0
        
    # 4. Cupom
    coupon = None
    coupon_elem = item.find(class_=lambda c: c and "coupon" in c)
    if coupon_elem:
        coupon = coupon_elem.text.strip()
    else:
        # Busca texto que mencione cupom
        for tag in item.find_all(["span", "div", "p"]):
            text = tag.text.strip() if tag.text else ""
            if text and "cupom" in text.lower() and len(text) < 35:
                coupon = text
                break
        
    return {
        "titulo": titulo,
        "preco_original": preco_original,
        "preco_atual": preco_atual,
        "desconto": desconto,
        "link_bruto": link_bruto,
        "link_imagem": link_imagem,
        "cupom": coupon
    }

if __name__ == "__main__":
    # Teste rápido
    print("🧪 Testando busca via Playwright (Navegador com Sessão):")
    ofertas = buscar_promocoes("Creatina", desconto_minimo=5, limite=2)
    if ofertas:
        for o in ofertas:
            print(f"- {o['titulo'][:40]}... | Preço: R$ {o['preco_atual']} (De: R$ {o['preco_original']}) | Desconto: {o['desconto']}%")
            print(f"  Link: {o['link_bruto']}")
            print(f"  Imagem: {o['link_imagem']}\n")
    else:
        print("🤷‍♂️ Nenhuma oferta encontrada ou bloqueio detectado.")