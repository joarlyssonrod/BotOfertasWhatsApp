import sys
import os
import shutil
import stat
import time
from playwright.sync_api import sync_playwright

# Habilita UTF8 para os prints no Windows
sys.stdout.reconfigure(encoding='utf-8')

PERFIL_DIR = "wpp_perfil"

def remove_readonly(func, path, excinfo):
    """
    Handler para remover atributo de somente-leitura e deletar arquivos no Windows.
    Comum ao copiar arquivos de pendrives ou quando o SO trava permissões.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        # Se mesmo mudando a permissão falhar, tenta ignorar ou avisar
        pass

def salvar_sessao_whatsapp():
    # Se já existir a pasta de perfil, pergunta se o usuário quer resetar
    if os.path.exists(PERFIL_DIR):
        print(f"⚠️ A pasta de perfil '{PERFIL_DIR}' já existe.")
        opcao = input("Deseja apagar a sessão atual do WhatsApp e escanear um novo QR Code? (s/n): ").strip().lower()
        if opcao == 's':
            print("Apagando sessão antiga...")
            try:
                # Tenta apagar usando o handler para permissões de somente-leitura
                shutil.rmtree(PERFIL_DIR, onerror=remove_readonly)
                time.sleep(1) # Dá um tempo para o Windows liberar os arquivos do disco
                
                # Se a pasta ainda persistir (caso o processo do Chrome esteja travando na memória)
                if os.path.exists(PERFIL_DIR):
                    print("⚠️ A pasta ainda não pôde ser totalmente apagada. Tentando forçar remoção...")
                    # Força nova tentativa de chmod
                    for root, dirs, files in os.walk(PERFIL_DIR):
                        for momo in files:
                            os.chmod(os.path.join(root, momo), stat.S_IWRITE)
                        for momo in dirs:
                            os.chmod(os.path.join(root, momo), stat.S_IWRITE)
                    shutil.rmtree(PERFIL_DIR, ignore_errors=True)
                    
            except Exception as e:
                print(f"🚨 Erro ao apagar pasta antiga: {e}.")
                print("DICA: Feche todos os navegadores de teste e o VS Code, ou reinicie o PC, e tente novamente.")
                return
        else:
            print("Mantendo sessão existente.")
            return

    with sync_playwright() as p:
        print("\n🚀 Abrindo navegador com Perfil Persistente...")
        contexto = p.chromium.launch_persistent_context(
            user_data_dir=PERFIL_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            args=['--disable-blink-features=AutomationControlled']
        )
        pagina = contexto.new_page()

        print("🔗 Acessando o WhatsApp Web...")
        pagina.goto("https://web.whatsapp.com/")

        print("\n🚨 ATENÇÃO: O navegador do Playwright foi aberto!")
        print("1. Pegue o seu celular, vá em Aparelhos Conectados e escaneie o QR Code na tela.")
        print("2. Espere suas conversas carregarem completamente no navegador.")
        print("3. Quando as conversas estiverem aparecendo, volte aqui e aperte ENTER.")
        
        input("\n👉 Aperte ENTER aqui no terminal APÓS ter feito o login e carregado as conversas... ")

        print("💾 Salvando dados de sessão...")
        contexto.close()
        
        print("\n✅ Sucesso! Sessão do WhatsApp persistida na pasta 'wpp_perfil'.")

if __name__ == "__main__":
    salvar_sessao_whatsapp()
