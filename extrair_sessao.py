from playwright.sync_api import sync_playwright

def extrair():
    with sync_playwright() as p:
        print("🔌 Conectando ao Chrome aberto na porta 9222...")
        # Conecta no navegador que você abriu manualmente via Win+R
        navegador = p.chromium.connect_over_cdp("http://localhost:9222")
        
        # Pega o contexto da aba atual
        contexto = navegador.contexts[0]
        
        # Tira o raio-x e salva
        contexto.storage_state(path="sessao_ml.json")
        
        print("✅ Sucesso! Sessão extraída e salva como 'sessao_ml.json'.")
        print("Agora o bot está pronto para agir nos bastidores.")

if __name__ == "__main__":
    extrair()