from playwright.sync_api import sync_playwright
import sys

# Habilita UTF8 para os prints no Windows
sys.stdout.reconfigure(encoding='utf-8')

def salvar_sessao():
    # Usaremos uma pasta de perfil temporária para simular um navegador de uso real
    perfil_dir = "ml_perfil_temp"
    
    with sync_playwright() as p:
        print("\n🚀 Abrindo navegador seguro...")
        # Lançamento persistente com remoção de sinalizadores de automação e usando o Chrome local
        contexto = p.chromium.launch_persistent_context(
            user_data_dir=perfil_dir,
            headless=False,
            channel="chrome", # Abre o seu Chrome real instalado no Windows (mais confiável)
            ignore_default_args=["--enable-automation"],
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        pagina = contexto.new_page()
        
        # Remove a propriedade 'webdriver' que entrega ao reCAPTCHA que é um bot
        pagina.add_init_script("delete navigator.__proto__.webdriver;")

        # Acessa o Mercado Livre
        pagina.goto("https://www.mercadolivre.com.br/")

        print("\n🚨 ATENÇÃO: O navegador do Playwright foi aberto!")
        print("1. Vá até o navegador que abriu, clique em 'Entre' no topo direito.")
        print("2. Faça o seu login no Mercado Livre.")
        print("3. Resolva o reCAPTCHA (Clique nas imagens se solicitado) e passe pelas validações de SMS/E-mail.")
        print("4. Quando estiver logado e vendo a página inicial com seu nome, volte para esta tela preta.")
        
        # O script vai pausar aqui e esperar você apertar ENTER no teclado
        input("\n👉 Aperte ENTER aqui no terminal APÓS ter concluído o login no navegador... ")

        # Salva a sessão (cookies, tokens) em um arquivo JSON
        contexto.storage_state(path="sessao_ml.json")
        print("\n✅ Sucesso! Sessão do Mercado Livre salva no arquivo 'sessao_ml.json'.")

        contexto.close()
        
        # Tenta apagar a pasta temporária de perfil
        try:
            import shutil
            import time
            time.sleep(1)
            shutil.rmtree(perfil_dir, ignore_errors=True)
        except:
            pass

if __name__ == "__main__":
    salvar_sessao()
