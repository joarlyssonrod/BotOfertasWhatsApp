import re

caminho = "/home/ubuntu/BotOfertasWhatsApp/whatsapp_sender.py"
with open(caminho, "r", encoding="utf-8") as f:
    codigo = f.read()

# Substitui o bloco de espera para dar 90 segundos e aceitar seletores flexíveis
antigo = """            # Aguarda a tela inicial carregar. O input de pesquisa indica que as conversas carregaram.
            print("⏳ Aguardando sincronização das conversas (isso pode levar alguns segundos)...")
            search_bar = self.page.locator('input[data-tab="3"], div[contenteditable="true"][data-tab="3"], div[data-testid="chat-list-search"]').first
            search_bar.wait_for(state="visible", timeout=45000)
            print("✅ WhatsApp Web conectado com sucesso!")
            return True"""

novo = """            # Aguarda a tela inicial carregar (painel de conversas ou barra de pesquisa)
            print("⏳ Aguardando sincronização das conversas (isso pode levar até 90s)...")
            seletor_principal = '#side, [data-testid="chat-list"], input[data-tab="3"], div[contenteditable="true"][data-tab="3"], div[data-testid="chat-list-search"]'
            try:
                self.page.wait_for_selector(seletor_principal, timeout=90000)
                print("✅ WhatsApp Web conectado com sucesso!")
                return True
            except Exception as e:
                self.page.screenshot(path="wpp_erro_conexao.png")
                print(f"🚨 Screenshot do erro salvo em wpp_erro_conexao.png: {e}")
                raise e"""

if antigo in codigo:
    codigo = codigo.replace(antigo, novo)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(codigo)
    print("✅ whatsapp_sender.py atualizado com sucesso!")
else:
    print("⚠️ Procurando substituição alternativa...")
    padrao = r"search_bar\s*=\s*self\.page\.locator\([^)]+\)\.first\s+search_bar\.wait_for\([^)]+\)"
    subst = """seletor_principal = '#side, [data-testid="chat-list"], input[data-tab="3"], div[contenteditable="true"][data-tab="3"], div[data-testid="chat-list-search"]'
            self.page.wait_for_selector(seletor_principal, timeout=90000)"""
    novo_codigo, cont = re.subn(padrao, subst, codigo)
    if cont > 0:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(novo_codigo)
        print("✅ Atualizado via Regex com sucesso!")
    else:
        print("❌ Não foi possível substituir automaticamente.")
