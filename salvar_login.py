import os
import sys
import shutil
import subprocess
from playwright.sync_api import sync_playwright

# Habilita UTF8 para os prints no Windows
sys.stdout.reconfigure(encoding='utf-8')

def salvar_sessao():
    perfil_dir = os.path.abspath("ml_perfil_temp")
    
    # Garante que a pasta temporária anterior seja apagada
    if os.path.exists(perfil_dir):
        try:
            shutil.rmtree(perfil_dir, ignore_errors=True)
        except:
            pass
            
    print("\n🚀 Iniciando login seguro no Mercado Livre...")
    print("Estamos abrindo o seu Google Chrome original em um perfil temporário.")
    print("Isso impede o bloqueio de CAPTCHA, pois o navegador NÃO estará sob controle de robôs.")
    print("\n👉 O que você precisa fazer:")
    print("1. Na janela do Chrome que abriu, clique em 'Entrar' ou faça login na sua conta.")
    print("2. Conclua o login e resolva o CAPTCHA/SMS normalmente.")
    print("3. Quando estiver logado e vendo a página inicial com seu nome, FECHE totalmente a janela do Chrome.")
    print("4. Volte para esta tela preta e aperte ENTER.")
    
    # Abre o Chrome original no Windows com um perfil específico
    cmd = f'start chrome --user-data-dir="{perfil_dir}" "https://www.mercadolivre.com.br/"'
    try:
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        print(f"\n🚨 Erro ao tentar abrir o Chrome automaticamente: {e}")
        print(f"Por favor, abra o menu Executar (Win+R) e digite:")
        print(f'chrome --user-data-dir="{perfil_dir}" "https://www.mercadolivre.com.br/"')
        
    input("\n👉 Aperte ENTER aqui no terminal APÓS ter concluído o login e fechado a janela do Chrome... ")

    print("\n💾 Extraindo dados da sessão...")
    try:
        with sync_playwright() as p:
            # Carrega o perfil que o usuário acabou de logar e salva o estado de sessão
            contexto = p.chromium.launch_persistent_context(
                user_data_dir=perfil_dir,
                headless=True
            )
            pagina = contexto.new_page()
            pagina.goto("https://www.mercadolivre.com.br/", timeout=30000)
            pagina.wait_for_load_state("domcontentloaded")
            pagina.wait_for_timeout(2000) # Pequena pausa para garantir carregamento dos cookies na memória
            contexto.storage_state(path="sessao_ml.json")
            contexto.close()
            
        print("\n✅ Sucesso! Sessão do Mercado Livre salva no arquivo 'sessao_ml.json'.")
        print("Agora o bot está pronto para rodar sem pedir login ou CAPTCHA!")
    except Exception as e:
        print(f"\n🚨 Erro ao extrair sessão do perfil temporário: {e}")
        print("Verifique se você realmente fechou a janela do Chrome antes de apertar ENTER.")

    # Tenta apagar a pasta temporária de perfil
    try:
        shutil.rmtree(perfil_dir, ignore_errors=True)
    except:
        pass

if __name__ == "__main__":
    salvar_sessao()
