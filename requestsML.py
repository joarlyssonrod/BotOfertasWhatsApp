from curl_cffi import requests

def gerar_link_afiliado(url_produto):
    # O endpoint interno que você "pescou" na aba Network
    endpoint = 'https://www.mercadolivre.com.br/affiliate-program/api/v2/stripe/user/links'

    # Os cabeçalhos de segurança (Headers). 
    # É aqui que o Python prova para o Mercado Livre que ele "é você" logado.
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'cookie': 'c_Z1DqXTD=1; inferredZipcode=true; g_state={"i_l":0,"i_ll":1779287255790,"i_b":"0bwozIdmhhvlRgykdDpWxBC4fi4+jkr6B7M/uMBUJh4","i_e":{"enable_itp_optimization":0},"i_et":1779287255788}; _d2id=d590c837-2a75-4fcc-ba81-50573a4ce3dc; ssid=ghy-052010-TZ6ZW7N5qbcp4PwSSqL0dCGk3rpWfE-__-208333335-__-1873981706964--RRR_0-RRR_0; orguserid=9ZdZ7hHHHHH9; ftid=dY3hjWPuK4gHK0cQfGBN9hYxbcwJX6fD-1779287257700; orguseridp=208333335; orgnickp=JOARLYSSONRODRIGUES; cookiesPreferencesLoggedFallback=%7B%22userId%22%3A208333335%2C%22categories%22%3A%7B%22advertising%22%3Atrue%2C%22functionality%22%3Anull%2C%22performance%22%3Anull%2C%22traceability%22%3Anull%7D%7D; cookiesPreferencesNotLogged=%7B%22categories%22%3A%7B%22advertising%22%3Atrue%2C%22functionality%22%3Anull%2C%22performance%22%3Anull%2C%22traceability%22%3Anull%7D%7D; cp=65130000; c_2l78kU=1; p_dsid=479a6300-0232-46b0-ae32-f137497fbd0a-1779458417527; p_edsid=1c8a2296-238f-446b-8bb2-9fd00c6d9082-1779458417527; tooltip=true; LAST_SEARCH=Whey%20100%25%20Hd; tooltips-configuration={"compats_highlight_tooltip":{"view_cnt":3,"close_cnt":0,"view_time":1779460115,"close_time":0}}; c_Z1l9PLD=1; _csrf=5-kUhrrT-2yVWKdmVC7pVhwA; _mldataSessionId=622ad40a-50b6-48f0-9b28-b2e185a0828f; ml_cart-quantity=0; cookiesPreferencesLogged=%7B%22userId%22%3A208333335%2C%22categories%22%3A%7B%22advertising%22%3Atrue%2C%22functionality%22%3Anull%2C%22performance%22%3Anull%2C%22traceability%22%3Anull%7D%7D; hide-cookie-banner=208333335-COOKIE_PREFERENCES_ALREADY_SET; nsa_rotok=eyJhbGciOiJSUzI1NiIsImtpZCI6IjMiLCJ0eXAiOiJKV1QifQ.eyJpZGVudGlmaWVyIjoiMGEyYmNkNDMtNjRhYS00OTBkLTgzMzMtMjdiNmZjNTQyNTIxIiwicm90YXRpb25faWQiOiI0OTk3NzA5MC04YzI1LTQ5MzMtYWRkOC02NTMxZWZlMGI0N2MiLCJwbGF0Zm9ybSI6Ik1MIiwicm90YXRpb25fZGF0ZSI6MTc4MDA1NjQxMCwiZXhwIjoxNzgyNjQ3ODEwLCJqdGkiOiJkZjdkNzU4My03MGM3LTRiNGUtOWJjNS1jM2ZjMzk0MmY4NmMiLCJpYXQiOjE3ODAwNTU4MTAsInN1YiI6IjBhMmJjZDQzLTY0YWEtNDkwZC04MzMzLTI3YjZmYzU0MjUyMSJ9.cJmJMWPZyO_pAux8qQx2kLSX8U_Bk4qnz4PJU4j38y8kSak0xd8Mwq9BKxT6CnMbJKF38RCcNtAE6cP4bkZoTm-OnHxxYIqM4rnF3alKAR0_P7zv7Fh0NfxxLYkz45a8R7zvyVYPjuTwngItR_Hj1mopzxjzLwZynlrWjcl5lzcZN-UcVGnTA-2E_gxHiMdC21VCaX1civhG-FTvYB-Oq68MPcc3rsrlZOOrIdut1U4k9gte8LpPs3mJNFni5zpxCMia08BwyYFBS3NRauD1ihvplhdHS4PzirZojRxivMqf4zIilmZIWrf5F1cb3TKD4sChbTsMaVw76o0kbVeqIg; _snoopy=eyJmaW5nZXJwcmludCI6IkJzdGFoeTdZT2xweWNkbkFrVTRoUllRZjFXYkk1d2oyK2JZOU5aMDdoRGMySW54WkhlODVLKzdvMWJiMk9vY1Q5WGVFRk5zbzNRNnNqN0NEMTBEaG5LU0xmeThYSkp4V2hrTU1yNTQzdUdmRUhpNG9OWlRabnFrMVpIcnhQWmt0WEFBYmtsSTRjdmFPb05nV0Y2eVM1NUJQTVMveGxFN3lDbjB0SGhKQlc2bnBTWEdCSytvPSIsImtleSI6Ikx3YXlzWVprQ25QakdVNXdmMmVRMU5OM29pMHdzWnEzeFpYYW1yOGZnUnNCZGFmelhHWXFkYXU1TmlFSmVTck8wT3dtMXowZHRNOFFCMHk1YkZQalJ5RzhNeGptM0hMRSJ9',
        'origin': 'https://produto.mercadolivre.com.br', # <-- ADICIONE ISSO
        'referer': 'https://produto.mercadolivre.com.br/', # <-- ADICIONE ISSO
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
        'x-csrf-token': '739J3TKw-R2neUtR9tK_HaNcDYwX5MEbdBd4'
    }

    # O corpo da requisição com a URL "limpa" e a sua tag
    payload = {
        "url": url_produto,
        "tag": "joarlyssonrodrigues"
    }

    try:
        # Dispara o POST
        resposta = requests.post(endpoint, headers=headers, json=payload, impersonate="chrome110")
        resposta.raise_for_status() # Verifica se a requisição não foi barrada (ex: erro 403 ou 401)
        
        # Converte a resposta para dicionário e extrai apenas o link encurtado
        dados = resposta.json()
        return dados.get("short_url")
        
    except requests.exceptions.RequestException as e:
        print(f"🚨 Erro na comunicação com o Mercado Livre: {e}")
        return None

# --- Testando na prática ---
# Note que tirei todo aquele lixo do final da URL (os searchVariations)
url_teste = "https://produto.mercadolivre.com.br/MLB-5298350806-capa-chuva-motoqueiro-pvc-impermeavel-motoboy-emborrachada-_JM"

print("Gerando link...")
link_final = gerar_link_afiliado(url_teste)

if link_final:
    print(f"✅ Sucesso! Seu link de afiliado é: {link_final}")