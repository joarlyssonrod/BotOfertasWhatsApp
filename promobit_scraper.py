import os
import sys
import re
import json
import time
import requests
import urllib3
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Suprime avisos de certificado SSL autoassinado/inseguro em redes corporativas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configura o stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

# Lista de domínios que o bot sabe converter para afiliados
DOMINIOS_SUPORTADOS = [
    "amazon.com.br",
    "mercadolivre.com.br",
    "magazineluiza.com.br",
    "shopee.com.br",
    "aliexpress.com"
]

def resolve_target_url(offer_url):
    """
    Usa um navegador headless leve do Playwright para clicar nos botões 'Ir à loja'
    e obter a URL final (redirecionada para a loja de destino).
    """
    print(f"🔗 [Promobit Resolver] Resolvendo link de redirecionamento para: {offer_url}...")
    final_url = None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        try:
            page.goto(offer_url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1500) # pequena pausa para renderização
            
            # Clica no primeiro botão "Ir à loja" (azul na tela do produto)
            first_btn = page.locator('button:has-text("Ir à loja"), a:has-text("Ir à loja")').first
            if first_btn.is_visible():
                first_btn.click()
                page.wait_for_timeout(1500)
                
                # Verifica se há o modal de cupom aberto (que contém outro botão "Ir à loja")
                btn_locator = page.locator('button:has-text("Ir à loja"), a:has-text("Ir à loja")')
                btn_count = btn_locator.count()
                
                # Aguarda e captura a abertura da nova aba (redirecionamento da loja)
                with context.expect_page(timeout=10000) as new_page_info:
                    if btn_count > 1:
                        # O botão de ir para a loja no modal é o último adicionado no DOM
                        btn_locator.last.click()
                    else:
                        btn_locator.first.click()
                        
                new_page = new_page_info.value
                # Espera os redirects carregarem na nova aba
                new_page.wait_for_load_state("domcontentloaded", timeout=15000)
                new_page.wait_for_timeout(4000) # tempo para resolver os redirects de afiliados (ex: Lomadee/Awin)
                
                final_url = new_page.url
                
                # Trata links intermediários de Perfil Social do Mercado Livre
                if final_url and "mercadolivre.com.br/social/" in final_url:
                    try:
                        btn_selector = 'a:has-text("Ir para produto")'
                        new_page.locator(btn_selector).wait_for(state="attached", timeout=6000)
                        target_href = new_page.locator(btn_selector).first.get_attribute("href")
                        if target_href:
                            final_url = target_href
                            print(f"🎯 [Promobit Resolver] Link de Perfil Social do ML extraído com sucesso: '{final_url}'")
                    except Exception as social_err:
                        print(f"⚠️ [Promobit Resolver] Não foi possível extrair o link do botão 'Ir para produto': {social_err}")
                
                print(f"🎯 [Promobit Resolver] URL resolvida com sucesso: '{final_url}'")
            else:
                print("⚠️ [Promobit Resolver] Botão 'Ir à loja' não encontrado na página.")
                
        except Exception as e:
            print(f"🚨 [Promobit Resolver] Erro ao resolver URL via Playwright: {e}")
        finally:
            try:
                browser.close()
            except:
                pass
            
    return final_url

def buscar_ofertas_promobit(desconto_minimo=10, limite=5):
    """
    Faz a raspagem da página inicial do Promobit, filtra as ofertas pertencentes
    a lojas suportadas e as retorna formatadas para o bot de afiliados.
    """
    print("\n⚡ [Promobit Scraper] Varrendo a página inicial do Promobit por novas ofertas...")
    url_base = "https://www.promobit.com.br"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url_base, headers=headers, timeout=15, verify=False)
        if response.status_code != 200:
            print(f"❌ [Promobit Scraper] Falha ao carregar site (Status {response.status_code})")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Encontra todas as âncoras que contêm links de ofertas
        anchors = soup.find_all("a", href=True)
        oferta_links = list(set([a["href"] for a in anchors if "/oferta/" in a["href"]]))
        
        print(f"🔍 [Promobit Scraper] Encontrados {len(oferta_links)} links de oferta na página principal.")
        
        ofertas_validas = []
        for path in oferta_links:
            if len(ofertas_validas) >= limite:
                break
                
            offer_url = url_base + path
            
            # Carrega a página da oferta individual para ler a estrutura NextJS (__NEXT_DATA__)
            try:
                offer_res = requests.get(offer_url, headers=headers, timeout=10, verify=False)
                if offer_res.status_code != 200:
                    continue
                    
                offer_soup = BeautifulSoup(offer_res.text, "html.parser")
                next_data_script = offer_soup.find("script", id="__NEXT_DATA__")
                
                if not next_data_script or not next_data_script.string:
                    continue
                    
                # Analisa o estado do NextJS
                page_state = json.loads(next_data_script.string)
                server_offer = page_state.get("props", {}).get("pageProps", {}).get("serverOffer", {})
                
                if not server_offer:
                    continue
                    
                # Verifica a loja da oferta
                store_domain = server_offer.get("storeDomain", "").lower()
                
                # Valida se a loja está na nossa lista de domínios de afiliados suportados
                loja_suportada = False
                for dom in DOMINIOS_SUPORTADOS:
                    if dom in store_domain:
                        loja_suportada = True
                        break
                        
                if not loja_suportada:
                    # Ignora lojas não suportadas (Netshoes, AliExpress sem API, Samsung, etc)
                    continue
                    
                titulo = server_offer.get("offerTitle")
                preco_atual = server_offer.get("offerPrice")
                preco_original = server_offer.get("offerOldPrice") or preco_atual
                cupom = server_offer.get("offerCoupon")
                photo_path = server_offer.get("offerPhoto")
                
                if not titulo or not preco_atual:
                    continue
                    
                # Formata URL de imagem para tamanho médio (500px)
                link_imagem = f"https://i.promobit.com.br/500{photo_path}"
                
                # Calcula desconto
                preco_original = float(preco_original)
                preco_atual = float(preco_atual)
                
                # Ignora cupons genéricos e promoções com preço simbólico (como R$ 0.01 ou R$ 1.00)
                if preco_atual <= 2.00 or titulo.lower().startswith("cupom") or "cupom " in titulo.lower() or "cupom:" in titulo.lower():
                    continue
                
                desconto = 0.0
                if preco_original > preco_atual:
                    desconto = round(((preco_original - preco_atual) / preco_original) * 100, 1)
                
                # Se o desconto for menor que o desejado, mas tiver cupom, consideramos uma oferta válida
                if desconto < desconto_minimo and not cupom:
                    continue
                    
                # Resolve o link de redirecionamento final da loja usando o Playwright
                link_bruto = resolve_target_url(offer_url)
                if not link_bruto:
                    print(f"⚠️ [Promobit Scraper] Não foi possível resolver o link final de: '{titulo[:30]}'")
                    continue
                    
                # Se o desconto for 0 e tiver cupom, coloca um desconto simbólico
                if desconto == 0.0 and cupom:
                    desconto = 10.0
                    preco_original = preco_atual * 1.11
                    
                ofertas_validas.append({
                    "titulo": titulo,
                    "preco_original": preco_original,
                    "preco_atual": preco_atual,
                    "desconto": desconto,
                    "link_bruto": link_bruto,
                    "link_imagem": link_imagem,
                    "cupom": cupom
                })
                print(f"✅ [Promobit Scraper] Oferta adicionada: '{titulo[:40]}...' | R$ {preco_atual} na loja {store_domain}")
                
            except Exception as item_err:
                print(f"⚠️ [Promobit Scraper] Erro ao processar oferta individual {offer_url}: {item_err}")
                continue
                
        return ofertas_validas
        
    except Exception as e:
        print(f"🚨 [Promobit Scraper] Erro geral ao raspar Promobit: {e}")
        return []

if __name__ == "__main__":
    # Teste rápido em isolamento
    print("🧪 Executando teste do Promobit Scraper:")
    resultados = buscar_ofertas_promobit(desconto_minimo=5, limite=2)
    print(f"\n--- Resultado Final ({len(resultados)} ofertas encontradas) ---")
    for r in resultados:
        print(r)
