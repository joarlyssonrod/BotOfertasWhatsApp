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
# MODO_DE_BUSCA = "OFERTAS_DO_DIA"
MODO_DE_BUSCA = "TERMOS_ESPECIFICOS"

# Lojas ativas para busca:
BUSCAR_NO_MERCADO_LIVRE = True
BUSCAR_NA_AMAZON = True
BUSCAR_NA_MAGALU = True
BUSCAR_NA_SHOPEE = True

# Se True, no modo OFERTAS_DO_DIA, o bot só envia ofertas que contêm algum termo da lista TERMOS_BUSCA.
# Se False, envia qualquer boa oferta encontrada nas páginas de ofertas do dia.
FILTRAR_OFERTAS_DO_DIA_POR_TERMOS = False

# Limite máximo de ofertas que serão postadas nesta execução (para evitar inundar o grupo de uma vez)
LIMITE_MENSAGENS_POR_RODADA = 15

# Desconto mínimo para aceitar uma oferta (%)
DESCONTO_MINIMO_GERAL = 10

# Configuração de envio do WhatsApp:
# Se True, envia todas as ofertas para um único grupo/canal unificado.
# Se False, envia para grupos separados por categoria (Moda, Games, Fitness, Informática, Geral).
UNIFICAR_GRUPOS = True
GRUPO_UNICO_NOME = "Ofertas - Geral"  # Nome do grupo/canal unificado no WhatsApp


# Termos específicos (usados apenas se MODO_DE_BUSCA = "TERMOS_ESPECIFICOS")
TERMOS_BUSCA = [
    # Tecnologia & Hardware
    {"termo": "Console PlayStation 5", "desconto_minimo": 10},
    {"termo": "Nintendo Switch", "desconto_minimo": 8},
    {"termo": "Processador Ryzen", "desconto_minimo": 10},
    {"termo": "Placa de vídeo RTX", "desconto_minimo": 12},
    {"termo": "Placa mãe", "desconto_minimo": 10},
    {"termo": "Memoria RAM", "desconto_minimo": 12},
    {"termo": "Fonte para PC", "desconto_minimo": 10},
    {"termo": "Monitor", "desconto_minimo": 12},
    {"termo": "Teclado mecânico", "desconto_minimo": 15},
    {"termo": "Mouse pad gamer", "desconto_minimo": 15},
    {"termo": "Notebook", "desconto_minimo": 10},
    {"termo": "Tablet", "desconto_minimo": 10},
    {"termo": "Gabinete Gamer", "desconto_minimo": 10},
    {"termo": "Fan ARGB", "desconto_minimo": 10},
    {"termo": "Impressora", "desconto_minimo": 10},
    {"termo": "Mesa para PC", "desconto_minimo": 15},
    {"termo": "Cadeira gamer", "desconto_minimo": 12},
    
    # Eletrônicos & Smart Home
    {"termo": "Celular", "desconto_minimo": 12},
    {"termo": "Samsung NFC 8GB", "desconto_minimo": 12},
    {"termo": "Relógio inteligente", "desconto_minimo": 15},
    {"termo": "Fone de ouvido bluetooth", "desconto_minimo": 15},
    {"termo": "Smart TV", "desconto_minimo": 10},
    {"termo": "Fire Stick", "desconto_minimo": 15},
    {"termo": "Alexa Echo", "desconto_minimo": 15},
    
    # Eletrodomésticos & Eletroportáteis
    {"termo": "Geladeira", "desconto_minimo": 10},
    {"termo": "Aspirador de pó vertical", "desconto_minimo": 15},
    {"termo": "Fritadeira Airfryer", "desconto_minimo": 15},
    {"termo": "Ventilador", "desconto_minimo": 10},
    {"termo": "Cafeteira", "desconto_minimo": 15},
    {"termo": "Ar condicionado", "desconto_minimo": 10},
    {"termo": "Microondas", "desconto_minimo": 10},
    {"termo": "Mixer", "desconto_minimo": 15},
    {"termo": "Máquina de barbear", "desconto_minimo": 15},
    
    # Fitness, Saúde & Suplementos
    {"termo": "Whey protein", "desconto_minimo": 15},
    {"termo": "Creatina pura", "desconto_minimo": 15},
    {"termo": "Bicicleta ergométrica", "desconto_minimo": 15},
    {"termo": "Garrafa academia", "desconto_minimo": 15},
    {"termo": "Multivitaminico", "desconto_minimo": 15},
    {"termo": "Magnesio", "desconto_minimo": 10},
    {"termo": "Roupa de academia", "desconto_minimo": 15},
    
    # Beleza & Cuidado Pessoal
    {"termo": "Perfume importado", "desconto_minimo": 15},
    {"termo": "Protetor solar facial", "desconto_minimo": 15},
    {"termo": "Hidratante facial", "desconto_minimo": 15},
    {"termo": "Shampoo e condicionador", "desconto_minimo": 20},
    {"termo": "Máscara capilar", "desconto_minimo": 20},
    {"termo": "Sabonete líquido facial", "desconto_minimo": 15},
    
    # Moda, Calçados & Utilitários
    {"termo": "Camisa dryfit", "desconto_minimo": 15},
    {"termo": "Camiseta masculina", "desconto_minimo": 15},
    {"termo": "Tênis", "desconto_minimo": 20},
    {"termo": "Kit de meias", "desconto_minimo": 20},
    {"termo": "Chinelo", "desconto_minimo": 20},
    {"termo": "Kit Cuecas Boxer", "desconto_minimo": 15},
    {"termo": "Copo térmico", "desconto_minimo": 15}
]
# =========================================================

def carregar_historico():
    """Carrega o histórico de envios locais para evitar duplicidades"""
    if os.path.exists(HISTORICO_FILE):
        try:
            with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_historico(historico):
    """Salva o histórico atualizado em arquivo JSON"""
    with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)

def obter_id_unico(url):
    """
    Retorna uma string identificadora única para o produto.
    ASIN para Amazon, MLB ID para Mercado Livre, ID numérico/hash para Magalu.
    Se não conseguir identificar, retorna a própria URL limpa como fallback.
    """
    url_limpa = url.strip()
    
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
            
    return url_limpa.split("?")[0].split("#")[0]

def formatar_mensagem_oferta(titulo, preco_original, preco_atual, desconto, link_afiliado):
    """Gera o texto formatado para envio no WhatsApp com visual premium"""
    msg = f"🔥 *{titulo}*\n\n"
    
    if preco_original > preco_atual:
        msg += f"❌ De: ~R$ {preco_original:.2f}~\n"
        
    msg += f"💰 *Por: R$ {preco_atual:.2f}*\n"
    msg += f"📉 *Desconto: {desconto}% OFF*\n\n"
    msg += f"🛒 *Compre com segurança aqui:* {link_afiliado}\n\n"
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
    
    historico = carregar_historico()
    ofertas_encontradas = []
    seen_ids = set() # Evita duplicados capturados na mesma execução do bot
    
    # 1. FASE DE SCRAPING: Busca as ofertas do Mercado Livre, Amazon, Magalu e Shopee
    print("🔍 [1/3] Iniciando varredura de ofertas...")
    
    if MODO_DE_BUSCA == "OFERTAS_DO_DIA":
        # Mercado Livre
        if BUSCAR_NO_MERCADO_LIVRE:
            resultados = buscar_ofertas_do_dia(desconto_minimo=DESCONTO_MINIMO_GERAL, limite=30)
            for item in resultados:
                if FILTRAR_OFERTAS_DO_DIA_POR_TERMOS and not atende_filtro_termos(item["titulo"]):
                    continue
                item_id = obter_id_unico(item["link_bruto"])
                if item_id not in historico and item_id not in seen_ids and item["link_bruto"] not in historico:
                    seen_ids.add(item_id)
                    categoria = categorizar_produto(item["titulo"])
                    item["categoria"] = categoria
                    ofertas_encontradas.append(item)
                    
        # Amazon
        if BUSCAR_NA_AMAZON:
            resultados_amz = buscar_ofertas_do_dia_amazon(desconto_minimo=DESCONTO_MINIMO_GERAL, limite=15)
            for item in resultados_amz:
                if FILTRAR_OFERTAS_DO_DIA_POR_TERMOS and not atende_filtro_termos(item["titulo"]):
                    continue
                item_id = obter_id_unico(item["link_bruto"])
                if item_id not in historico and item_id not in seen_ids and item["link_bruto"] not in historico:
                    seen_ids.add(item_id)
                    categoria = categorizar_produto(item["titulo"])
                    item["categoria"] = categoria
                    ofertas_encontradas.append(item)

        # Magazine Luiza
        if BUSCAR_NA_MAGALU:
            resultados_mgl = buscar_ofertas_do_dia_magalu(desconto_minimo=DESCONTO_MINIMO_GERAL, limite=15)
            for item in resultados_mgl:
                if FILTRAR_OFERTAS_DO_DIA_POR_TERMOS and not atende_filtro_termos(item["titulo"]):
                    continue
                item_id = obter_id_unico(item["link_bruto"])
                if item_id not in historico and item_id not in seen_ids and item["link_bruto"] not in historico:
                    seen_ids.add(item_id)
                    categoria = categorizar_produto(item["titulo"])
                    item["categoria"] = categoria
                    ofertas_encontradas.append(item)

        # Shopee
        if BUSCAR_NA_SHOPEE:
            resultados_shp = buscar_ofertas_do_dia_shopee(desconto_minimo=DESCONTO_MINIMO_GERAL, limite=15)
            for item in resultados_shp:
                if FILTRAR_OFERTAS_DO_DIA_POR_TERMOS and not atende_filtro_termos(item["titulo"]):
                    continue
                item_id = obter_id_unico(item["link_bruto"])
                if item_id not in historico and item_id not in seen_ids and item["link_bruto"] not in historico:
                    seen_ids.add(item_id)
                    categoria = categorizar_produto(item["titulo"])
                    item["categoria"] = categoria
                    ofertas_encontradas.append(item)
    else:
        # Garimpa termo por termo nas lojas ativas
        for busca in TERMOS_BUSCA:
            termo = busca["termo"]
            desc_min = busca["desconto_minimo"]
            
            # Mercado Livre
            if BUSCAR_NO_MERCADO_LIVRE:
                ml_res = buscar_promocoes(termo, desconto_minimo=desc_min, limite=1)
                for item in ml_res:
                    item_id = obter_id_unico(item["link_bruto"])
                    if item_id not in historico and item_id not in seen_ids and item["link_bruto"] not in historico:
                        seen_ids.add(item_id)
                        item["categoria"] = categorizar_produto(item["titulo"])
                        ofertas_encontradas.append(item)
                        
            # Amazon
            if BUSCAR_NA_AMAZON:
                amz_res = buscar_promocoes_amazon(termo, desconto_minimo=desc_min, limite=1)
                for item in amz_res:
                    item_id = obter_id_unico(item["link_bruto"])
                    if item_id not in historico and item_id not in seen_ids and item["link_bruto"] not in historico:
                        seen_ids.add(item_id)
                        item["categoria"] = categorizar_produto(item["titulo"])
                        ofertas_encontradas.append(item)

            # Magazine Luiza
            if BUSCAR_NA_MAGALU:
                mgl_res = buscar_promocoes_magalu(termo, desconto_minimo=desc_min, limite=1)
                for item in mgl_res:
                    item_id = obter_id_unico(item["link_bruto"])
                    if item_id not in historico and item_id not in seen_ids and item["link_bruto"] not in historico:
                        seen_ids.add(item_id)
                        item["categoria"] = categorizar_produto(item["titulo"])
                        ofertas_encontradas.append(item)

            # Shopee
            if BUSCAR_NA_SHOPEE:
                shp_res = buscar_promocoes_shopee(termo, desconto_minimo=desc_min, limite=1)
                for item in shp_res:
                    item_id = obter_id_unico(item["link_bruto"])
                    if item_id not in historico and item_id not in seen_ids and item["link_bruto"] not in historico:
                        seen_ids.add(item_id)
                        item["categoria"] = categorizar_produto(item["titulo"])
                        ofertas_encontradas.append(item)
                        
            time.sleep(1.5)
            
    # Filtra e ordena as ofertas encontradas pelo maior desconto
    ofertas_encontradas = sorted(ofertas_encontradas, key=lambda x: x['desconto'], reverse=True)
    
    # Limita o número de posts desta rodada para não dar spam
    ofertas_encontradas = ofertas_encontradas[:LIMITE_MENSAGENS_POR_RODADA]
    
    print(f"\n📊 Encontradas {len(ofertas_encontradas)} novas ofertas aptas para envio nesta rodada!")
    if not ofertas_encontradas:
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
    if not ofertas_prontas:
        print("🤷‍♂️ Nenhuma oferta com link convertido pronto para envio.")
        return

    # 3. FASE DE ENVIO WHATSAPP: Abre o WhatsApp e envia as mensagens
    print("\n📱 [3/3] Iniciando conexão com o WhatsApp Web para envio...")
    whatsapp = WhatsAppSender()
    
    # Inicia o WhatsApp (pode rodar headless=True se você já salvou a sessão)
    if whatsapp.iniciar(headless=False):
        for idx, item in enumerate(ofertas_prontas):
            mensagem = formatar_mensagem_oferta(
                titulo=item["titulo"],
                preco_original=item["preco_original"],
                preco_atual=item["preco_atual"],
                desconto=item["desconto"],
                link_afiliado=item["link_afiliado"]
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
            sucesso = whatsapp.enviar_mensagem_grupo(grupo_destino, message_cap := mensagem, caminho_imagem)
            
            # Limpa o arquivo de imagem temporário após o envio
            if caminho_imagem and os.path.exists(caminho_imagem):
                try:
                    os.remove(caminho_imagem)
                except Exception as ex:
                    print(f"⚠️ Erro ao remover imagem temporária: {ex}")
            
            if sucesso:
                # Adiciona ao histórico local o ID único para evitar duplicações mesmo se a URL mudar parâmetros de busca
                item_id = obter_id_unico(item["link_bruto"])
                historico.append(item_id)
                salvar_historico(historico)
            
            # Adiciona delay humanizado anti-banimento se ainda houver mais mensagens a enviar
            if idx < len(ofertas_prontas) - 1:
                delay_tempo = random.randint(10, 25)
                print(f"⏳ Aguardando {delay_tempo} segundos (delay anti-ban) antes do próximo envio...")
                time.sleep(delay_tempo)
            
        whatsapp.fechar()
    else:
        print("🚨 Falha ao conectar no WhatsApp Web. Verifique a sessão.")

    print("\n🏁 Operação concluída com sucesso!")

if __name__ == "__main__":
    orquestrar_bot()