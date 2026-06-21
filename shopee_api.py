import os
import sys
import time
import hashlib
import json
import requests
import urllib3

# Configura o stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

# Desabilita avisos de requisicoes inseguras (SSL desativado)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL_SHOPEE_GRAPHQL = "https://open-api.affiliate.shopee.com.br/graphql"

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

def enviar_requisicao_shopee(payload):
    """Gera a assinatura SHA256 e envia a requisicao POST para o GraphQL da Shopee"""
    env = ler_env_local()
    app_id = env.get("SHOPEE_APP_ID")
    secret = env.get("SHOPEE_SECRET")
    
    if not app_id or not secret:
        print("⚠️ [Shopee API] SHOPEE_APP_ID ou SHOPEE_SECRET nao configurados no .env")
        return None
        
    try:
        # Serializa o payload JSON garantindo a exclusao de espacos para consistencia da assinatura
        payload_json = json.dumps(payload, separators=(',', ':'))
        timestamp = str(int(time.time()))
        
        # Formula da assinatura: SHA256(AppId + Timestamp + Payload + Secret)
        factor = f"{app_id}{timestamp}{payload_json}{secret}"
        signature = hashlib.sha256(factor.encode("utf-8")).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={app_id},Timestamp={timestamp},Signature={signature}"
        }
        
        # Envia usando verify=False para contornar problemas locais de certificado SSL
        response = requests.post(
            URL_SHOPEE_GRAPHQL,
            data=payload_json,
            headers=headers,
            timeout=15,
            verify=False
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ [Shopee API] Erro HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ [Shopee API] Falha na conexao: {e}")
        return None

def buscar_promocoes_shopee(termo, desconto_minimo=10, limite=5):
    """
    Busca promocoes na Shopee para um determinado termo de busca.
    Retorna uma lista de dicionarios com as chaves padronizadas.
    """
    print(f"🔍 [Shopee API] Garimpando ofertas para o termo: '{termo}'...")
    
    graphql_query = """
    query GetProductList($keyword: String, $limit: Int) {
      productOfferV2(keyword: $keyword, listType: 0, sortType: 1, page: 1, limit: $limit) {
        nodes {
          itemId
          productName
          productLink
          offerLink
          priceMin
          priceMax
          imageUrl
          priceDiscountRate
        }
      }
    }
    """
    
    payload = {
        "query": graphql_query,
        "variables": {
            "keyword": termo,
            "limit": limite * 2 # Puxa um pouco mais para filtrarmos localmente por desconto minimo
        }
    }
    
    res_data = enviar_requisicao_shopee(payload)
    if not res_data:
        return []
        
    if "errors" in res_data:
        print(f"⚠️ [Shopee API] Erros no GraphQL: {res_data['errors']}")
        return []
        
    nodes = res_data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
    ofertas_validas = []
    
    for node in nodes:
        try:
            titulo = node.get("productName")
            link_afiliado = node.get("offerLink") or node.get("productLink")
            link_imagem = node.get("imageUrl")
            
            preco_atual = float(node.get("priceMin") or node.get("priceMax") or 0.0)
            if preco_atual <= 0:
                continue
                
            # Extrai taxa de desconto da API
            desconto = int(node.get("priceDiscountRate") or 0)
            
            # Calcula o preco original aproximado se houver desconto
            if desconto > 0:
                preco_original = preco_atual / (1.0 - (desconto / 100.0))
            else:
                preco_original = preco_atual
                desconto = 0
                
            if desconto >= desconto_minimo:
                ofertas_validas.append({
                    "titulo": titulo,
                    "preco_original": preco_original,
                    "preco_atual": preco_atual,
                    "desconto": desconto,
                    "link_bruto": link_afiliado, # O link bruto ja e o link de afiliado da Shopee
                    "link_imagem": link_imagem,
                    "itemId": node.get("itemId")
                })
                
            if len(ofertas_validas) >= limite:
                break
        except Exception as e:
            pass
            
    return ofertas_validas

def buscar_ofertas_do_dia_shopee(desconto_minimo=10, limite=20):
    """
    Busca os produtos recomendados em destaque na Shopee.
    Usa o listType de recomendacoes gerais ordenados por relevancia/desconto.
    """
    print("🔥 [Shopee API] Garimpando as ofertas em destaque recomendadas da Shopee...")
    
    graphql_query = """
    query GetProductOffers($limit: Int) {
      productOfferV2(listType: 0, sortType: 1, page: 1, limit: $limit) {
        nodes {
          itemId
          productName
          productLink
          offerLink
          priceMin
          priceMax
          imageUrl
          priceDiscountRate
        }
      }
    }
    """
    
    payload = {
        "query": graphql_query,
        "variables": {
            "limit": limite * 2
        }
    }
    
    res_data = enviar_requisicao_shopee(payload)
    if not res_data:
        return []
        
    if "errors" in res_data:
        print(f"⚠️ [Shopee API] Erros no GraphQL: {res_data['errors']}")
        return []
        
    nodes = res_data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
    ofertas_validas = []
    
    for node in nodes:
        try:
            titulo = node.get("productName")
            link_afiliado = node.get("offerLink") or node.get("productLink")
            link_imagem = node.get("imageUrl")
            
            preco_atual = float(node.get("priceMin") or node.get("priceMax") or 0.0)
            if preco_atual <= 0:
                continue
                
            desconto = int(node.get("priceDiscountRate") or 0)
            
            if desconto > 0:
                preco_original = preco_atual / (1.0 - (desconto / 100.0))
            else:
                preco_original = preco_atual
                desconto = 0
                
            if desconto >= desconto_minimo:
                ofertas_validas.append({
                    "titulo": titulo,
                    "preco_original": preco_original,
                    "preco_atual": preco_atual,
                    "desconto": desconto,
                    "link_bruto": link_afiliado,
                    "link_imagem": link_imagem,
                    "itemId": node.get("itemId")
                })
                
            if len(ofertas_validas) >= limite:
                break
        except Exception as e:
            pass
            
    return ofertas_validas

def converter_link_shopee(url_original):
    """
    Converte um link bruto de produto da Shopee em link de afiliado oficial (shortLink).
    """
    # Se ja for um link curto de afiliado da Shopee, retorna diretamente
    if "s.shopee.com.br" in url_original:
        return url_original
        
    graphql_mutation = """
    mutation GenerateLink($input: ShortLinkInput!) {
      generateShortLink(input: $input) {
        shortLink
      }
    }
    """
    
    payload = {
        "query": graphql_mutation,
        "variables": {
            "input": {
                "originUrl": url_original
            }
        }
    }
    
    res_data = enviar_requisicao_shopee(payload)
    if not res_data:
        return url_original
        
    if "errors" in res_data:
        print(f"⚠️ [Shopee API] Erros ao converter link no GraphQL: {res_data['errors']}")
        return url_original
        
    short_link = res_data.get("data", {}).get("generateShortLink", {}).get("shortLink")
    if short_link:
        print(f"✅ Link Shopee convertido via API: {short_link}")
        return short_link
        
    return url_original

if __name__ == "__main__":
    print("🧪 Testando Shopee API em isolamento:")
    ofertas = buscar_promocoes_shopee("PlayStation 5", desconto_minimo=5, limite=2)
    for o in ofertas:
        print(f"- {o['titulo'][:45]}... | R$ {o['preco_atual']:.2f} (De R$ {o['preco_original']:.2f}) | {o['desconto']}% OFF")
        print(f"  Link: {o['link_bruto']}")
    
    print("\n🧪 Testando conversao de link Shopee:")
    link_bruto = "https://shopee.com.br/product-i.488358485.23927230198"
    link_convertido = converter_link_shopee(link_bruto)
    print(f"Link convertido: {link_convertido}")
