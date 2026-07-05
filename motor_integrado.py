import os
import sys
import json
import time
import random
import re

# Importa nossos módulos locais
from garimpeiro import buscar_promocoes, buscar_ofertas_do_dia
from amazon_scraper import buscar_promocoes_amazon, buscar_ofertas_do_dia_amazon
from magalu_scraper import buscar_promocoes_magalu, buscar_ofertas_do_dia_magalu
from shopee_api import buscar_promocoes_shopee, buscar_ofertas_do_dia_shopee
from promobit_scraper import buscar_ofertas_promobit
from categorizador import categorizar_produto
from bot_afiliado import gerar_link_bot
from whatsapp_sender import WhatsAppSender

# Configura o stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

HISTORICO_FILE = "historico_envios.json"

# =========================================================
# CONFIGURAÇÕES DO BOT
# =========================================================
# Modos de Busca:
# "OFERTAS_DO_DIA" -> Garimpa as páginas oficiais de Ofertas do Dia / Destaques
# "TERMOS_ESPECIFICOS" -> Busca termos específicos configurados na lista TERMOS_BUSCA
#MODO_DE_BUSCA = "OFERTAS_DO_DIA"
MODO_DE_BUSCA = "TERMOS_ESPECIFICOS"

# Lojas ativas para busca:
BUSCAR_NO_MERCADO_LIVRE = True
BUSCAR_NA_AMAZON = True
BUSCAR_NA_MAGALU = True
BUSCAR_NA_SHOPEE = True
BUSCAR_NO_PROMOBIT = True

# Se True, no modo OFERTAS_DO_DIA, o bot só envia ofertas que contêm algum termo da lista TERMOS_BUSCA.
# Se False, envia qualquer boa oferta encontrada nas páginas de ofertas do dia.
FILTRAR_OFERTAS_DO_DIA_POR_TERMOS = True

# Limite máximo de ofertas que serão postadas nesta execução (para evitar inundar o grupo de uma vez)
LIMITE_MENSAGENS_POR_RODADA = 19

# Desconto mínimo para aceitar uma oferta (%)
DESCONTO_MINIMO_GERAL = 15

# Configuração de envio do WhatsApp:
# Se True, envia todas as ofertas para um único grupo/canal unificado.
# Se False, envia para grupos separados por categoria (Moda, Games, Fitness, Informática, Geral).
UNIFICAR_GRUPOS = True
GRUPO_UNICO_NOME = "Ofertas - Geral"  # Nome do grupo/canal unificado no WhatsApp


# Termos específicos (usados apenas se MODO_DE_BUSCA = "TERMOS_ESPECIFICOS")
TERMOS_BUSCA = [
    # Tecnologia & Hardware
    {"termo": "Console PlayStation® 5 Slim", "desconto_minimo": 10},
    {"termo": "Controle PlayStation 5", "desconto_minimo": 20},
    {"termo": "Console Xbox Series X", "desconto_minimo": 8},
    {"termo": "Console Xbox Series S", "desconto_minimo": 8},
    {"termo": "Controle para Xbox Series S", "desconto_minimo": 20},
    {"termo": "Processador Ryzen 5 AM4", "desconto_minimo": 15},
    {"termo": "Processador Intel i5", "desconto_minimo": 15},
    {"termo": "Placa de vídeo NVIDIA RTX", "desconto_minimo": 20},
    {"termo": "Placa de vídeo AMD RX", "desconto_minimo": 20},
    {"termo": "Placa mãe AM4", "desconto_minimo": 10},
    {"termo": "Placa mãe LGA1700", "desconto_minimo": 10},
    {"termo": "Memoria RAM", "desconto_minimo": 12},
    {"termo": "Fonte 80 Plus", "desconto_minimo": 10},
    {"termo": "Gabinete Gamer", "desconto_minimo": 10},
    {"termo": "Mousepad", "desconto_minimo": 10},
    {"termo": "Teclado gamer", "desconto_minimo": 10},
    {"termo": "Water Cooler", "desconto_minimo": 10},
    {"termo": "Monitor Gamer 144Hz", "desconto_minimo": 12},
    {"termo": "Teclado mecânico", "desconto_minimo": 15},
    {"termo": "Mouse gamer", "desconto_minimo": 15},
    {"termo": "Notebook i5", "desconto_minimo": 10},
    {"termo": "Notebook Gamer ryzen 5 nvidia", "desconto_minimo": 20},
    {"termo": "Tablet", "desconto_minimo": 10},
    {"termo": "Gabinete Gamer", "desconto_minimo": 10},
    {"termo": "Water Cooler RGB", "desconto_minimo": 10},
    {"termo": "Fan ARGB", "desconto_minimo": 10},
    {"termo": "Impressora", "desconto_minimo": 10},
    {"termo": "Mesa para PC", "desconto_minimo": 15},
    {"termo": "Cadeira gamer", "desconto_minimo": 12},
    #{"termo": "jogo de chaves computador celular", "desconto_minimo": 30},
    {"termo": "jogo de chaves eletrico computador celular", "desconto_minimo": 30},
    
    # Eletrônicos & Smart Home
    {"termo": "Celular Xiaomi", "desconto_minimo": 12},
    {"termo": "Smartphone Xiaomi", "desconto_minimo": 12},
    {"termo": "Samsung NFC 8GB", "desconto_minimo": 12},
    {"termo": "Samsung NFC 8gb 256gb", "desconto_minimo": 12},
    {"termo": "Smartphone 8GB NFC", "desconto_minimo": 12},
    {"termo": "Relógio inteligente", "desconto_minimo": 15},
    {"termo": "Relógio samsung", "desconto_minimo": 20},
    {"termo": "Smartwatch samsung galaxy", "desconto_minimo": 20},
    {"termo": "Smartwatch NFC", "desconto_minimo": 20},
    {"termo": "Fone de ouvido bluetooth", "desconto_minimo": 15},
    {"termo": "Smart TV", "desconto_minimo": 10},
    {"termo": "Fire TV Stick", "desconto_minimo": 12},
    {"termo": "Roku Streaming Stick", "desconto_minimo": 12},
    {"termo": "Caixa de Som Bluetooth", "desconto_minimo": 25},
    {"termo": "Pote de vidro", "desconto_minimo": 30},
    {"termo": "Echo Dot", "desconto_minimo": 15},
    
    # Eletrodomésticos & Eletroportáteis
    {"termo": "Geladeira 220v", "desconto_minimo": 10},
    {"termo": "Aspirador de pó 220v", "desconto_minimo": 15},
    {"termo": "Fritadeira Airfryer 220v", "desconto_minimo": 25},
    {"termo": "Ventilador 220v", "desconto_minimo": 10},
    {"termo": "Cafeteira 220v", "desconto_minimo": 15},
    {"termo": "Ar condicionado 220v", "desconto_minimo": 10},
    {"termo": "Secador de cabelo 220v", "desconto_minimo": 15},
    {"termo": "Microondas 220v", "desconto_minimo": 10},
    {"termo": "Sanduicheira 220v", "desconto_minimo": 30},
    {"termo": "Purificador de água 220v", "desconto_minimo": 25},
    {"termo": "lavadora de alta pressao 220v", "desconto_minimo": 50},
    {"termo": "Panela elétrica de pressão 220v", "desconto_minimo": 25},
    {"termo": "Panela elétrica de arroz 220v", "desconto_minimo": 25},
    {"termo": "Fogão Inox 220v", "desconto_minimo": 25},
    {"termo": "Fogão cooktop 220v", "desconto_minimo": 25},
    {"termo": "Chapinha 220v", "desconto_minimo": 25},
    {"termo": "Maquina de Lavar 220v", "desconto_minimo": 25},
    #{"termo": "Parafusadeira", "desconto_minimo": 50},
    #{"termo": "Furadeira", "desconto_minimo": 50},
    {"termo": "Mixer", "desconto_minimo": 50},
    {"termo": "Máquina de barbear 220v", "desconto_minimo": 15},
    {"termo": "Ferro eletrico vapor 220v", "desconto_minimo": 15},
    {"termo": "Aparador de pelos 220v", "desconto_minimo": 15},
    
    # Fitness, Saúde & Suplementos
    {"termo": "Whey protein", "desconto_minimo": 15},
    {"termo": "Creatina", "desconto_minimo": 15},
    {"termo": "Bicicleta ergométrica", "desconto_minimo": 15},
    {"termo": "Garrafa academia", "desconto_minimo": 15},
    {"termo": "Multivitaminico", "desconto_minimo": 20},
    {"termo": "Magnesio", "desconto_minimo": 10},
    {"termo": "Complexo B", "desconto_minimo": 17},
    
    # Beleza & Cuidado Pessoal
    {"termo": "Perfume Natura", "desconto_minimo": 15},
    {"termo": "Perfume Natura Kriska", "desconto_minimo": 15},
    {"termo": "Perfume Floratta", "desconto_minimo": 15},
    {"termo": "Perfume Boticario", "desconto_minimo": 15},
    {"termo": "Perfume Boticario Egeo", "desconto_minimo": 15},
    {"termo": "Perfume Arbo", "desconto_minimo": 15},
    {"termo": "Perfume masculino", "desconto_minimo": 15},
    {"termo": "Perfume feminino", "desconto_minimo": 15},
    {"termo": "Protetor solar facial", "desconto_minimo": 15},
    {"termo": "Hidratante facial", "desconto_minimo": 15},
    {"termo": "Hidratante corporal Natura", "desconto_minimo": 15},
    {"termo": "Shampoo e condicionador", "desconto_minimo": 20},
    {"termo": "Body Splash", "desconto_minimo": 15},
    {"termo": "Sabonete líquido facial", "desconto_minimo": 15},
    
    # Moda, Calçados & Utilitários
    {"termo": "Camisa dryfit", "desconto_minimo": 15},
    {"termo": "Camiseta masculina", "desconto_minimo": 15},
    {"termo": "Short fitness", "desconto_minimo": 25},
    {"termo": "Bolsa", "desconto_minimo": 15},
    {"termo": "Mochila", "desconto_minimo": 20},
    {"termo": "Roupa de academia", "desconto_minimo": 15},
    {"termo": "Tênis unissex", "desconto_minimo": 20},
    {"termo": "Kit de meias", "desconto_minimo": 20},
    {"termo": "Chinelo", "desconto_minimo": 20},
    {"termo": "Kit Cuecas Boxer", "desconto_minimo": 15},
    {"termo": "Camisa de time", "desconto_minimo": 20},
    {"termo": "Colcha de cama casal", "desconto_minimo": 15},
    {"termo": "Cortina", "desconto_minimo": 20},
    {"termo": "Copo térmico", "desconto_minimo": 15}
]
# =========================================================

def carregar_historico():
    """Carrega o histórico de envios locais para evitar duplicidades e normaliza registros antigos"""
    historico = []
    if os.path.exists(HISTORICO_FILE):
        try:
            with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, list):
                    for item in dados:
                        if isinstance(item, str):
                            item_id = obter_id_unico(item)
                            historico.append({
                                "id": item_id,
                                "link_bruto": item if item.startswith("http") else "",
                                "titulo": "",
                                "preco": 0.0,
                                "timestamp": os.path.getmtime(HISTORICO_FILE) if os.path.exists(HISTORICO_FILE) else time.time(),
                                "expirado": False
                            })
                        elif isinstance(item, dict):
                            if "id" not in item:
                                item["id"] = obter_id_unico(item)
                            if "timestamp" not in item:
                                item["timestamp"] = time.time()
                            if "expirado" not in item:
                                item["expirado"] = False
                            historico.append(item)
        except Exception as e:
            print(f"⚠️ Erro ao carregar histórico: {e}. Retornando lista vazia.")
            return []
    return historico

def salvar_historico(historico):
    """Salva o histórico atualizado em arquivo JSON"""
    with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)

def obter_id_unico(item_or_url):
    """
    Retorna uma string identificadora única para o produto.
    ASIN para Amazon, MLB ID para Mercado Livre, ID numérico/hash para Magalu.
    Se não conseguir identificar, retorna a própria URL limpa como fallback.
    Aceita tanto uma string URL quanto um dicionário contendo o item.
    """
    if isinstance(item_or_url, dict):
        if "itemId" in item_or_url and item_or_url.get("itemId"):
            return f"SHOPEE_{item_or_url['itemId']}"
        url = item_or_url.get("link_bruto", "")
    else:
        url = item_or_url
        
    url_limpa = url.strip() if url else ""
    if not url_limpa:
        return ""
    
    # 1. AMAZON
    if "amazon.com" in url_limpa:
        asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url_limpa, re.IGNORECASE)
        if asin_match:
            return f"AMAZON_{asin_match.group(1).upper()}"
            
    # 2. MERCADO LIVRE
    elif "mercadolivre.com" in url_limpa or "mercadolibre.com" in url_limpa:
        ml_match = re.search(r'(MLB[U]?[-]?\d+)', url_limpa, re.IGNORECASE)
        if ml_match:
            return f"ML_{ml_match.group(1).replace('-', '').upper()}"
            
    # 3. MAGAZINE LUIZA / MAGAZINE VOCE
    elif "magazineluiza.com" in url_limpa or "magazinevoce.com" in url_limpa:
        magalu_match = re.search(r'/p/([a-zA-Z0-9]+)', url_limpa)
        if magalu_match:
            return f"MAGALU_{magalu_match.group(1).upper()}"
            
    # 4. SHOPEE
    elif "shopee.com" in url_limpa:
        # Padrões comuns: shopee.com.br/product/shopId/itemId ou shopee.com.br/product-i.shopId.itemId ou s.shopee.com.br/hash
        shopee_match = re.search(r'product/(\d+)/(\d+)', url_limpa)
        if shopee_match:
            return f"SHOPEE_{shopee_match.group(2)}"
        shopee_match2 = re.search(r'-i\.(\d+)\.(\d+)', url_limpa)
        if shopee_match2:
            return f"SHOPEE_{shopee_match2.group(2)}"
        # Captura o hash do link curto se for s.shopee.com.br
        shopee_short = re.search(r's\.shopee\.com\.br/([a-zA-Z0-9]+)', url_limpa)
        if shopee_short:
            return f"SHOPEE_{shopee_short.group(1)}"
            
    # 5. ALIEXPRESS
    elif "aliexpress.com" in url_limpa:
        aliexpress_match = re.search(r'/item/(\d+)\.html', url_limpa)
        if aliexpress_match:
            return f"ALIEXPRESS_{aliexpress_match.group(1)}"
            
    return url_limpa.split("?")[0].split("#")[0]

def formatar_mensagem_oferta(titulo, preco_original, preco_atual, desconto, link_afiliado, cupom=None, menor_preco=False):
    """Gera o texto formatado para envio no WhatsApp com visual premium"""
    msg = ""
    if menor_preco:
        msg += "📉 *MENOR PREÇO HISTÓRICO REGISTRADO!*\n\n"
        
    msg += f"🔥 *{titulo}*\n\n"
    
    if preco_original > preco_atual:
        msg += f"❌ De: ~R$ {preco_original:.2f}~\n"
        
    msg += f"💰 *Por: R$ {preco_atual:.2f}*\n"
    msg += f"📉 *Desconto: {desconto}% OFF*\n"
    
    if cupom:
        msg += f"🏷️ *Cupom ativo:* `{cupom}`\n"
        
    msg += f"\n🛒 *Compre com segurança aqui:* {link_afiliado}\n\n"
    msg += "⚠️ _Oferta sujeita a alteração de preço e estoque a qualquer momento._"
    return msg

def baixar_imagem(url, caminho_destino):
    """Baixa uma imagem de uma URL e salva localmente"""
    if not url:
        return False
    import urllib.request
    import ssl
    try:
        # Define cabeçalhos de navegador comum para evitar bloqueios de CDN
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
        )
        # Ignora verificação SSL para evitar erros com proxies corporativos ou antivírus
        contexto_ssl = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=contexto_ssl, timeout=10) as response:
            with open(caminho_destino, 'wb') as out_file:
                out_file.write(response.read())
        return True
    except Exception as e:
        print(f"⚠️ Erro ao baixar imagem da oferta: {e}")
        return False

def atende_filtro_termos(titulo):
    """Retorna True se o titulo do produto contiver algum dos termos especificos configurados"""
    titulo_lower = titulo.lower()
    for busca in TERMOS_BUSCA:
        termo = busca["termo"].lower()
        if termo in titulo_lower:
            return True
    return False

def obter_palavras_chave(titulo):
    """Remove caracteres especiais e extrai palavras-chave significativas"""
    palavras = re.findall(r'[a-zA-Z0-9]{3,}', titulo.lower())
    stop_words = {"com", "para", "sem", "pro", "plus", "new", "lite", "azul", "preto", "branco", "cinza", "verde", "rosa", "vermelho", "bivolt", "110v", "220v"}
    return set([p for p in palavras if p not in stop_words])

def encontrar_preco_minimo_historico(item_id, titulo, historico):
    """Varre o histórico para encontrar o menor preço do produto por ID ou título similar"""
    preco_min = float('inf')
    palavras_item = obter_palavras_chave(titulo)
    
    for h in historico:
        if not isinstance(h, dict):
            continue
            
        # 1. Match exato por ID
        if h.get("id") == item_id:
            preco = h.get("preco", 0)
            if 0 < preco < preco_min:
                preco_min = preco
            continue
            
        # 2. Match por similaridade de título (intersecção de palavras-chave)
        h_titulo = h.get("titulo", "")
        if h_titulo:
            palavras_h = obter_palavras_chave(h_titulo)
            if palavras_item and palavras_h:
                comum = palavras_item.intersection(palavras_h)
                total = max(len(palavras_item), len(palavras_h))
                if len(comum) / total >= 0.60:
                    preco = h.get("preco", 0)
                    if 0 < preco < preco_min:
                        preco_min = preco
                        
    return preco_min

def checar_pagina_produto(page, url, preco_original_envio):
    """
    Navega em uma página de produto e verifica se a oferta expirou ou preço subiu.
    """
    url_lower = url.lower()
    
    # Verifica erro geral / página não encontrada
    try:
        title = page.title().lower()
        if "página não encontrada" in title or "404" in title or "error" in title:
            return True, None, "página não encontrada / 404"
    except:
        pass
        
    # 1. MERCADO LIVRE
    if "mercadolivre.com" in url_lower or "mercadolibre.com" in url_lower:
        # Primeiro, verifica se fomos redirecionados para captcha ou verificação de conta
        try:
            current_url = page.url.lower()
            if "account-verification" in current_url or "captcha" in current_url or "/sec/" in current_url:
                print(f"⚠️ [Verificador] Mercado Livre exigiu verificação na URL: {page.url}")
                return False, None, "bloqueio_verificacao"
        except Exception as e:
            print(f"⚠️ [Verificador] Erro ao checar URL da página: {e}")
            
        # Aguarda a renderização de algum elemento chave de status (botão comprar, fora de estoque ou pausado)
        try:
            status_locator = page.locator(".ui-pdp-actions__button, .ui-pdp-buybox__out-of-stock, p.ui-pdp-color--BLACK:has-text('Anúncio pausado')").first
            status_locator.wait_for(state="attached", timeout=3000)
        except:
            pass

        try:
            paused = page.locator("p.ui-pdp-color--BLACK:has-text('Anúncio pausado')").is_visible()
            out_of_stock = page.locator(".ui-pdp-buybox__out-of-stock").is_visible()
            buy_btn = page.locator(".ui-pdp-actions__button").first
            no_buy_button = not buy_btn.is_visible() or buy_btn.get_attribute("disabled") is not None
            
            if paused or out_of_stock or no_buy_button:
                # Double-check se fomos redirecionados para captcha ou verificação de conta
                try:
                    current_url = page.url.lower()
                    if "account-verification" in current_url or "captcha" in current_url or "/sec/" in current_url:
                        print(f"⚠️ [Verificador] Mercado Livre exigiu verificação na URL (double-check): {page.url}")
                        return False, None, "bloqueio_verificacao"
                except:
                    pass
                return True, None, "fora de estoque/anúncio pausado"
                
            meta_price = page.locator('meta[itemprop="price"]').first.get_attribute("content")
            if not meta_price:
                meta_price = page.locator('meta[property="product:price:amount"]').first.get_attribute("content")
            
            preco_atual = None
            if meta_price:
                try:
                    preco_atual = float(meta_price)
                except ValueError:
                    pass
            
            if preco_atual is None:
                price_fraction_elem = page.locator(".ui-pdp-price__part .andes-money-amount__fraction").first
                if price_fraction_elem.is_visible():
                    price_str = price_fraction_elem.text_content().replace(".", "")
                    cents_elem = page.locator(".ui-pdp-price__part .andes-money-amount__cents").first
                    if cents_elem.is_visible():
                        price_str += f".{cents_elem.text_content()}"
                    try:
                        preco_atual = float(price_str)
                    except ValueError:
                        pass
            
            if preco_atual is not None:
                if preco_atual > preco_original_envio * 1.05:
                    return True, preco_atual, f"preço subiu para R$ {preco_atual:.2f}"
                return False, preco_atual, "ok"
                
        except Exception as e:
            print(f"⚠️ [Verificador] Erro ao checar Mercado Livre: {e}")
            
    # 2. AMAZON
    elif "amazon.com" in url_lower:
        try:
            out_of_stock_selectors = [
                "#outOfStock", 
                "#availability:has-text('Não disponível')",
                "#availability:has-text('Fora de estoque')",
                "#availability:has-text('Não temos previsão')",
                "#availability:has-text('indisponível')"
            ]
            for sel in out_of_stock_selectors:
                if page.locator(sel).first.is_visible():
                    return True, None, "fora de estoque"
            
            price_selectors = [
                "#corePrice_feature_div .a-price .a-offscreen",
                ".a-price.apexPriceToPay .a-offscreen",
                ".priceToPay .a-offscreen",
                "span.a-price .a-offscreen",
                "#priceblock_ourprice",
                "#priceblock_dealprice"
            ]
            
            preco_atual = None
            for sel in price_selectors:
                el = page.locator(sel).first
                if el.is_visible():
                    price_text = el.text_content()
                    if price_text:
                        price_clean = price_text.replace("R$", "").strip().replace(".", "").replace(",", ".")
                        try:
                            preco_atual = float(price_clean)
                            break
                        except ValueError:
                            pass
                            
            if preco_atual is not None:
                if preco_atual > preco_original_envio * 1.05:
                    return True, preco_atual, f"preço subiu para R$ {preco_atual:.2f}"
                return False, preco_atual, "ok"
                
        except Exception as e:
            print(f"⚠️ [Verificador] Erro ao checar Amazon: {e}")
            
    # 3. MAGAZINE LUIZA
    elif "magazineluiza.com" in url_lower or "magazinevoce.com" in url_lower:
        try:
            unavailable = page.locator("[data-testid='product-unavailable']").is_visible() or page.locator("text='indisponível'").first.is_visible()
            if unavailable:
                return True, None, "fora de estoque/indisponível"
                
            price_selectors = [
                "[data-testid='price-value']",
                ".price-template",
                ".priceToPay"
            ]
            preco_atual = None
            for sel in price_selectors:
                el = page.locator(sel).first
                if el.is_visible():
                    price_text = el.text_content()
                    if price_text:
                        match = re.search(r'R\$\s*([\d\.,]+)', price_text)
                        if match:
                            price_clean = match.group(1).replace(".", "").replace(",", ".")
                        else:
                            price_clean = price_text.replace("R$", "").strip().replace(".", "").replace(",", ".")
                        try:
                            preco_atual = float(price_clean)
                            break
                        except ValueError:
                            pass
                            
            if preco_atual is not None:
                if preco_atual > preco_original_envio * 1.05:
                    return True, preco_atual, f"preço subiu para R$ {preco_atual:.2f}"
                return False, preco_atual, "ok"
                
        except Exception as e:
            print(f"⚠️ [Verificador] Erro ao checar Magalu: {e}")
            
    # 4. SHOPEE
    elif "shopee.com" in url_lower:
        try:
            unavailable = page.locator("text='esgotado'").first.is_visible() or page.locator("text='indisponível'").first.is_visible()
            if unavailable:
                return True, None, "esgotado/indisponível"
                
            price_el = page.locator(".pmmxdd").first
            if not price_el.is_visible():
                price_el = page.locator("span:has-text('R$')").first
                
            preco_atual = None
            if price_el.is_visible():
                price_text = price_el.text_content()
                if price_text:
                    match = re.search(r'R\$\s*([\d\.,]+)', price_text)
                    if match:
                        price_clean = match.group(1).replace(".", "").replace(",", ".")
                        try:
                            preco_atual = float(price_clean)
                        except ValueError:
                            pass
                            
            if preco_atual is not None:
                if preco_atual > preco_original_envio * 1.05:
                    return True, preco_atual, f"preço subiu para R$ {preco_atual:.2f}"
                return False, preco_atual, "ok"
                
        except Exception as e:
            print(f"⚠️ [Verificador] Erro ao checar Shopee: {e}")
            
    # 5. ALIEXPRESS
    elif "aliexpress.com" in url_lower:
        try:
            unavailable = page.locator("text='esgotado'").first.is_visible() or page.locator("text='indisponível'").first.is_visible() or page.locator("text='out of stock'").first.is_visible()
            if unavailable:
                return True, None, "esgotado/indisponível"
                
            # Tenta meta tags primeiro
            meta_price = page.locator('meta[itemprop="price"]').first.get_attribute("content")
            if not meta_price:
                meta_price = page.locator('meta[property="og:price:amount"]').first.get_attribute("content")
                
            preco_atual = None
            if meta_price:
                try:
                    preco_atual = float(meta_price)
                except ValueError:
                    pass
                    
            if preco_atual is None:
                price_selectors = [
                    ".product-price-value",
                    ".uniform-banner-box-price",
                    ".price--current",
                    ".product-price"
                ]
                for sel in price_selectors:
                    el = page.locator(sel).first
                    if el.is_visible():
                        price_text = el.text_content()
                        if price_text:
                            match = re.search(r'R\$\s*([\d\.,]+)', price_text)
                            if match:
                                price_clean = match.group(1).replace(".", "").replace(",", ".")
                            else:
                                price_clean = price_text.replace("R$", "").strip().replace(".", "").replace(",", ".")
                            try:
                                preco_atual = float(price_clean)
                                break
                            except ValueError:
                                pass
                                
            if preco_atual is not None:
                if preco_atual > preco_original_envio * 1.05:
                    return True, preco_atual, f"preço subiu para R$ {preco_atual:.2f}"
                return False, preco_atual, "ok"
                
        except Exception as e:
            print(f"⚠️ [Verificador] Erro ao checar AliExpress: {e}")
            
    return False, None, "não pôde determinar"

def checar_e_alertar_expirados(whatsapp, historico):
    """
    Verifica se as ofertas enviadas nas últimas 12 horas mudaram de preço ou esgotaram.
    """
    print("\n🔍 [Verificador] Iniciando verificação de ofertas expiradas nas últimas 12 horas...")
    agora = time.time()
    limite_tempo = 12 * 3600
    
    recentes = [item for item in historico if isinstance(item, dict) and not item.get("expirado", False) and (agora - item.get("timestamp", 0)) < limite_tempo]
    
    if not recentes:
        print("🤷‍♂️ [Verificador] Nenhuma oferta recente para verificar.")
        return
        
    print(f"📊 [Verificador] {len(recentes)} ofertas recentes serão checadas.")
    
    try:
        if os.path.exists("sessao_ml.json"):
            with open("sessao_ml.json", "r", encoding="utf-8") as f:
                ml_state = json.load(f)
                ml_cookies = ml_state.get("cookies", [])
                whatsapp.context.add_cookies(ml_cookies)
                print("   [Verificador] Cookies do Mercado Livre injetados.")
                
        from amazon_scraper import ler_env_local, parse_cookies_amazon
        env_vars = ler_env_local()
        cookie_str = env_vars.get("AMAZON_COOKIES", "")
        if cookie_str:
            amz_cookies = parse_cookies_amazon(cookie_str)
            whatsapp.context.add_cookies(amz_cookies)
            print("   [Verificador] Cookies da Amazon injetados.")
    except Exception as e:
        print(f"⚠️ [Verificador] Erro ao injetar cookies para checagem: {e}")

    historico_alterado = False
    
    for item in recentes:
        link_bruto = item.get("link_bruto")
        preco_envio = item.get("preco", 0.0)
        titulo = item.get("titulo", "Produto")
        
        if not link_bruto or preco_envio <= 0:
            continue
            
        print(f"🔄 [Verificador] Checando: '{titulo[:30]}'...")
        temp_page = None
        try:
            temp_page = whatsapp.context.new_page()
            temp_page.goto(link_bruto, timeout=25000, wait_until="domcontentloaded")
            temp_page.wait_for_load_state("domcontentloaded")
            temp_page.wait_for_timeout(2000)
            
            expirou, preco_novo, motivo = checar_pagina_produto(temp_page, link_bruto, preco_envio)
            
            # Se fomos bloqueados por cookies expirados/inválidos no Mercado Livre, limpamos os cookies e tentamos novamente sem login
            if "mercadolivre.com" in link_bruto.lower() and motivo == "bloqueio_verificacao":
                print("   [Verificador] Mercado Livre exigiu verificação. Limpando cookies e tentando novamente...")
                try:
                    whatsapp.context.clear_cookies(domain="mercadolivre.com.br")
                    whatsapp.context.clear_cookies(domain=".mercadolivre.com.br")
                    whatsapp.context.clear_cookies(domain="mercadolibre.com")
                    whatsapp.context.clear_cookies(domain=".mercadolibre.com")
                except Exception as e:
                    print(f"   [Verificador] Erro ao limpar cookies do Mercado Livre: {e}")
                    
                # Fecha a página bloqueada e abre uma nova
                temp_page.close()
                temp_page = whatsapp.context.new_page()
                temp_page.goto(link_bruto, timeout=25000, wait_until="domcontentloaded")
                temp_page.wait_for_load_state("domcontentloaded")
                temp_page.wait_for_timeout(2000)
                
                expirou, preco_novo, motivo = checar_pagina_produto(temp_page, link_bruto, preco_envio)
            
            if expirou:
                print(f"🚨 [Verificador] Oferta expirada! Motivo: {motivo}")
                item["expirado"] = True
                historico_alterado = True
                
                msg_alerta = f"⚠️ *OFERTA ENCERRADA* ⚠️\n\n*Produto:* {titulo}\n\nO produto esgotou ou voltou ao preço normal."
                if preco_novo and preco_novo > preco_envio:
                    msg_alerta = f"⚠️ *PREÇO ALTERADO* ⚠️\n\n*Produto:* {titulo}\n\nO valor subiu de ~R$ {preco_envio:.2f}~ para *R$ {preco_novo:.2f}*."
                
                categoria = categorizar_produto(titulo)
                grupo_destino = GRUPO_UNICO_NOME if UNIFICAR_GRUPOS else categoria
                
                print(f"✉️ Enviando alerta de encerramento para grupo '{grupo_destino}'...")
                whatsapp.enviar_mensagem_grupo(grupo_destino, msg_alerta)
                time.sleep(2)
            else:
                if motivo == "bloqueio_verificacao":
                    print(f"   [Verificador] Não foi possível verificar o item (Bloqueio de CAPTCHA/Verificação). Mantendo ativo.")
                else:
                    print(f"   [Verificador] Oferta ativa (Preço atual: R$ {preco_novo if preco_novo else preco_envio})")
                
        except Exception as err:
            print(f"⚠️ [Verificador] Erro ao checar item {titulo[:20]}: {err}")
        finally:
            if temp_page:
                try:
                    temp_page.close()
                except:
                    pass
                    
    if historico_alterado:
        salvar_historico(historico)

def git_sync_pull():
    """Tenta puxar atualizações do histórico no GitHub antes de rodar"""
    import subprocess
    try:
        print("🔄 [Git Sync] Buscando atualizações do histórico no GitHub...")
        result = subprocess.run(
            ["git", "pull", "--rebase"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            timeout=15
        )
        if result.returncode == 0:
            print("✅ [Git Sync] Histórico atualizado com sucesso do GitHub.")
        else:
            print(f"⚠️ [Git Sync] Aviso ao atualizar do GitHub (pull): {result.stderr.strip()}")
    except Exception as e:
        print(f"⚠️ [Git Sync] Não foi possível atualizar do GitHub: {e}")

def git_sync_push():
    """Tenta commitar e enviar as atualizações do histórico para o GitHub"""
    import subprocess
    try:
        # Verifica se há alterações no historico_envios.json
        status_res = subprocess.run(
            ["git", "status", "--porcelain", HISTORICO_FILE],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if status_res.stdout.strip():
            print("📤 [Git Sync] Enviando novo histórico para o GitHub...")
            subprocess.run(["git", "add", HISTORICO_FILE], check=True, timeout=5)
            msg = f"Auto-update history: {int(time.time())}"
            subprocess.run(["git", "commit", "-m", msg], check=True, timeout=5)
            push_res = subprocess.run(
                ["git", "push"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20
            )
            if push_res.returncode == 0:
                print("✅ [Git Sync] Histórico atualizado e enviado com sucesso ao GitHub!")
            else:
                print(f"⚠️ [Git Sync] Falha no git push: {push_res.stderr.strip()}")
        else:
            print("🤷‍♂️ [Git Sync] Histórico de envios sem alterações para enviar.")
    except Exception as e:
        print(f"⚠️ [Git Sync] Não foi possível sincronizar o histórico com o GitHub: {e}")

def orquestrar_bot():
    # Salvaguarda: Evita enviar mensagens de madrugada (das 23h às 08h) para não incomodar os membros
    import datetime
    hora_atual = datetime.datetime.now().hour
    if hora_atual >= 23 or hora_atual < 8:
        print("💤 Shhh! Está muito tarde ou muito cedo. Evitando envios de madrugada para não incomodar os membros.")
        print("🏁 Operação cancelada devido ao horário silencioso.")
        return

    print("🚀 =========================================")
    print("🤖 BOT DE AFILIADOS MERCADO LIVRE & WHATSAPP")
    print(f"📡 Modo de Busca Ativo: {MODO_DE_BUSCA}")
    print("🚀 =========================================\n")
    
    git_sync_pull()
    
    headless_mode = "--headless" in sys.argv
    
    historico = carregar_historico()
    historico_ids = {h["id"] for h in historico if isinstance(h, dict)}
    historico_links = {h["link_bruto"] for h in historico if isinstance(h, dict) and h.get("link_bruto")}
    
    ofertas_encontradas = []
    seen_ids = set() # Evita duplicados capturados na mesma execução do bot
    
    # 1. FASE DE SCRAPING: Busca as ofertas do Mercado Livre, Amazon, Magalu, Shopee e Promobit
    print("🔍 [1/3] Iniciando varredura de ofertas...")
    
    if MODO_DE_BUSCA == "OFERTAS_DO_DIA":
        # Promobit
        if BUSCAR_NO_PROMOBIT:
            try:
                resultados_pb = buscar_ofertas_promobit(desconto_minimo=DESCONTO_MINIMO_GERAL, limite=15)
                for item in resultados_pb:
                    if FILTRAR_OFERTAS_DO_DIA_POR_TERMOS and not atende_filtro_termos(item["titulo"]):
                        continue
                    item_id = obter_id_unico(item)
                    if item_id not in historico_ids and item_id not in seen_ids and item["link_bruto"] not in historico_links:
                        seen_ids.add(item_id)
                        categoria = categorizar_produto(item["titulo"])
                        item["categoria"] = categoria
                        ofertas_encontradas.append(item)
            except Exception as pb_err:
                print(f"⚠️ Erro ao buscar no Promobit: {pb_err}")

        # Mercado Livre
        if BUSCAR_NO_MERCADO_LIVRE:
            try:
                resultados = buscar_ofertas_do_dia(desconto_minimo=DESCONTO_MINIMO_GERAL, limite=30, headless=headless_mode)
                for item in resultados:
                    if FILTRAR_OFERTAS_DO_DIA_POR_TERMOS and not atende_filtro_termos(item["titulo"]):
                        continue
                    item_id = obter_id_unico(item)
                    if item_id not in historico_ids and item_id not in seen_ids and item["link_bruto"] not in historico_links:
                        seen_ids.add(item_id)
                        categoria = categorizar_produto(item["titulo"])
                        item["categoria"] = categoria
                        ofertas_encontradas.append(item)
            except Exception as ml_err:
                print(f"⚠️ Erro ao buscar no Mercado Livre: {ml_err}")
                    
        # Amazon
        if BUSCAR_NA_AMAZON:
            try:
                resultados_amz = buscar_ofertas_do_dia_amazon(desconto_minimo=DESCONTO_MINIMO_GERAL, limite=15)
                for item in resultados_amz:
                    if FILTRAR_OFERTAS_DO_DIA_POR_TERMOS and not atende_filtro_termos(item["titulo"]):
                        continue
                    item_id = obter_id_unico(item)
                    if item_id not in historico_ids and item_id not in seen_ids and item["link_bruto"] not in historico_links:
                        seen_ids.add(item_id)
                        categoria = categorizar_produto(item["titulo"])
                        item["categoria"] = categoria
                        ofertas_encontradas.append(item)
            except Exception as amz_err:
                print(f"⚠️ Erro ao buscar na Amazon: {amz_err}")

        # Magazine Luiza
        if BUSCAR_NA_MAGALU:
            try:
                resultados_mgl = buscar_ofertas_do_dia_magalu(desconto_minimo=DESCONTO_MINIMO_GERAL, limite=15)
                for item in resultados_mgl:
                    if FILTRAR_OFERTAS_DO_DIA_POR_TERMOS and not atende_filtro_termos(item["titulo"]):
                        continue
                    item_id = obter_id_unico(item)
                    if item_id not in historico_ids and item_id not in seen_ids and item["link_bruto"] not in historico_links:
                        seen_ids.add(item_id)
                        categoria = categorizar_produto(item["titulo"])
                        item["categoria"] = categoria
                        ofertas_encontradas.append(item)
            except Exception as mgl_err:
                print(f"⚠️ Erro ao buscar na Magalu: {mgl_err}")

        # Shopee
        if BUSCAR_NA_SHOPEE:
            try:
                resultados_shp = buscar_ofertas_do_dia_shopee(desconto_minimo=DESCONTO_MINIMO_GERAL, limite=15)
                for item in resultados_shp:
                    if FILTRAR_OFERTAS_DO_DIA_POR_TERMOS and not atende_filtro_termos(item["titulo"]):
                        continue
                    item_id = obter_id_unico(item)
                    if item_id not in historico_ids and item_id not in seen_ids and item["link_bruto"] not in historico_links:
                        seen_ids.add(item_id)
                        categoria = categorizar_produto(item["titulo"])
                        item["categoria"] = categoria
                        ofertas_encontradas.append(item)
            except Exception as shp_err:
                print(f"⚠️ Erro ao buscar na Shopee: {shp_err}")
    else:
        # Garimpa termo por termo nas lojas ativas
        for busca in TERMOS_BUSCA:
            termo = busca["termo"]
            desc_min = busca["desconto_minimo"]
            
            # Mercado Livre
            if BUSCAR_NO_MERCADO_LIVRE:
                try:
                    ml_res = buscar_promocoes(termo, desconto_minimo=desc_min, limite=1, headless=headless_mode)
                    for item in ml_res:
                        item_id = obter_id_unico(item)
                        if item_id not in historico_ids and item_id not in seen_ids and item["link_bruto"] not in historico_links:
                            seen_ids.add(item_id)
                            item["categoria"] = categorizar_produto(item["titulo"])
                            ofertas_encontradas.append(item)
                except Exception as ml_err:
                    print(f"⚠️ Erro ao buscar '{termo}' no Mercado Livre: {ml_err}")
                        
            # Amazon
            if BUSCAR_NA_AMAZON:
                try:
                    amz_res = buscar_promocoes_amazon(termo, desconto_minimo=desc_min, limite=1)
                    for item in amz_res:
                        item_id = obter_id_unico(item)
                        if item_id not in historico_ids and item_id not in seen_ids and item["link_bruto"] not in historico_links:
                            seen_ids.add(item_id)
                            item["categoria"] = categorizar_produto(item["titulo"])
                            ofertas_encontradas.append(item)
                except Exception as amz_err:
                    print(f"⚠️ Erro ao buscar '{termo}' na Amazon: {amz_err}")

            # Magazine Luiza
            if BUSCAR_NA_MAGALU:
                try:
                    mgl_res = buscar_promocoes_magalu(termo, desconto_minimo=desc_min, limite=1)
                    for item in mgl_res:
                        item_id = obter_id_unico(item)
                        if item_id not in historico_ids and item_id not in seen_ids and item["link_bruto"] not in historico_links:
                            seen_ids.add(item_id)
                            item["categoria"] = categorizar_produto(item["titulo"])
                            ofertas_encontradas.append(item)
                except Exception as mgl_err:
                    print(f"⚠️ Erro ao buscar '{termo}' na Magalu: {mgl_err}")

            # Shopee
            if BUSCAR_NA_SHOPEE:
                try:
                    shp_res = buscar_promocoes_shopee(termo, desconto_minimo=desc_min, limite=1)
                    for item in shp_res:
                        item_id = obter_id_unico(item)
                        if item_id not in historico_ids and item_id not in seen_ids and item["link_bruto"] not in historico_links:
                            seen_ids.add(item_id)
                            item["categoria"] = categorizar_produto(item["titulo"])
                            ofertas_encontradas.append(item)
                except Exception as shp_err:
                    print(f"⚠️ Erro ao buscar '{termo}' na Shopee: {shp_err}")
                        
            time.sleep(1.5)
            
    # Filtra e ordena as ofertas encontradas pelo maior desconto
    ofertas_encontradas = sorted(ofertas_encontradas, key=lambda x: x['desconto'], reverse=True)
    
    # Limita o número de posts desta rodada para não dar spam
    ofertas_encontradas = ofertas_encontradas[:LIMITE_MENSAGENS_POR_RODADA]
    
    print(f"\n📊 Encontradas {len(ofertas_encontradas)} novas ofertas aptas para envio nesta rodada!")
    if not ofertas_encontradas and MODO_DE_BUSCA != "OFERTAS_DO_DIA": # No ofertas_do_dia, rodamos o verificador mesmo se sem novas ofertas
        print("🤷‍♂️ Nenhuma oferta nova para enviar nesta rodada.")
        return
        
    # 2. FASE DE CONVERSÃO: Converte os links para afiliados instantaneamente (sem navegador)
    print("\n🔗 [2/3] Iniciando conversão de links brutas para links de afiliado...")
    ofertas_prontas = []
    
    for item in ofertas_encontradas:
        print(f"🔄 Convertendo link para: {item['titulo'][:40]}...")
        link_afiliado = gerar_link_bot(item["link_bruto"])
        
        if link_afiliado:
            item["link_afiliado"] = link_afiliado
            ofertas_prontas.append(item)
        else:
            print(f"❌ Não foi possível gerar link de afiliado para '{item['titulo'][:30]}'")
        
    print(f"\n✅ {len(ofertas_prontas)} links convertidos com sucesso!")

    # 3. FASE DE ENVIO WHATSAPP: Abre o WhatsApp e envia as mensagens
    print("\n📱 [3/3] Iniciando conexão com o WhatsApp Web para envio...")
    whatsapp = WhatsAppSender()
    
    # Inicia o WhatsApp (usa o headless_mode detectado)
    if whatsapp.iniciar(headless=headless_mode):
        # Executa verificação e envio de alertas de ofertas expiradas antes de novos envios
        # checar_e_alertar_expirados(whatsapp, historico)

        
        for idx, item in enumerate(ofertas_prontas):
            item_id = obter_id_unico(item)
            
            # Verifica se é menor preço histórico
            menor_preco = False
            preco_min_hist = encontrar_preco_minimo_historico(item_id, item["titulo"], historico)
            if preco_min_hist != float('inf') and item["preco_atual"] < preco_min_hist:
                menor_preco = True
                
            mensagem = formatar_mensagem_oferta(
                titulo=item["titulo"],
                preco_original=item["preco_original"],
                preco_atual=item["preco_atual"],
                desconto=item["desconto"],
                link_afiliado=item["link_afiliado"],
                cupom=item.get("cupom"),
                menor_preco=menor_preco
            )
            
            # Faz o download da imagem do produto se existir
            caminho_imagem = None
            url_img = item.get("link_imagem")
            if url_img:
                caminho_imagem = "temp_oferta.jpg"
                print(f"📥 Baixando imagem do produto para envio...")
                baixado = baixar_imagem(url_img, caminho_imagem)
                if not baixado:
                    caminho_imagem = None
            
            # Define se envia para o grupo unificado ou para o grupo de categoria
            grupo_destino = GRUPO_UNICO_NOME if UNIFICAR_GRUPOS else item["categoria"]
            
            # Envia para o grupo de destino com a imagem correspondente
            sucesso = whatsapp.enviar_mensagem_grupo(grupo_destino, mensagem, caminho_imagem)
            
            # Limpa o arquivo de imagem temporário após o envio
            if caminho_imagem and os.path.exists(caminho_imagem):
                try:
                    os.remove(caminho_imagem)
                except Exception as ex:
                    print(f"⚠️ Erro ao remover imagem temporária: {ex}")
            
            if sucesso:
                # Adiciona ao histórico o objeto detalhado
                historico.append({
                    "id": item_id,
                    "link_bruto": item["link_bruto"],
                    "titulo": item["titulo"],
                    "preco": float(item["preco_atual"]),
                    "timestamp": time.time(),
                    "expirado": False
                })
                salvar_historico(historico)
            
            # Adiciona delay humanizado anti-banimento se ainda houver mais mensagens a enviar
            if idx < len(ofertas_prontas) - 1:
                delay_tempo = random.randint(10, 25)
                print(f"⏳ Aguardando {delay_tempo} segundos (delay anti-ban) antes do próximo envio...")
                time.sleep(delay_tempo)
            
        whatsapp.fechar()
    else:
        print("🚨 Falha ao conectar no WhatsApp Web. Verifique a sessão.")

    git_sync_push()
    print("\n🏁 Operação concluída com sucesso!")

if __name__ == "__main__":
    orquestrar_bot()