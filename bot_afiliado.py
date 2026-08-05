import re
import urllib.parse
import sys
from shopee_api import converter_link_shopee
from aliexpress_api import gerar_link_afiliado_aliexpress
from magalu_scraper import obter_store_name

# Configura o stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

def gerar_link_bot(url_produto, pagina_ativa=None):
    """
    Gera instantaneamente o link de afiliado para Mercado Livre ou Amazon.
    Ignora a página ativa do Playwright pois a conversão agora é instantânea.
    """
    url_limpa = url_produto.strip()
    
    # 1. MERCADO LIVRE
    if "mercadolivre.com" in url_limpa or "mercadolibre.com" in url_limpa:
        # Limpa parâmetros adicionais
        url_limpa = url_limpa.split("?")[0].split("#")[0]
        affiliate_id = "joarlyssonrodrigues"
        link_afiliado = f"{url_limpa}?affiliate={affiliate_id}"
        print(f"✅ Link Mercado Livre convertido instantaneamente: {link_afiliado}")
        return link_afiliado
        
    # 2. AMAZON
    elif "amazon.com" in url_limpa:
        # Decodifica o link para evitar problemas com caracteres especiais
        decoded_link = urllib.parse.unquote(url_limpa)
        # Localiza o ASIN (Código identificador único da Amazon de 10 dígitos)
        asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', decoded_link, re.IGNORECASE)
        affiliate_tag = "jrodrigues07-20"
        
        if asin_match:
            asin = asin_match.group(1)
            link_afiliado = f"https://www.amazon.com.br/dp/{asin}?tag={affiliate_tag}"
        else:
            # Fallback se não encontrar o padrão clássico de ASIN
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