import os
import sys
from playwright.sync_api import sync_playwright

# Habilita UTF8 para os prints no Windows
sys.stdout.reconfigure(encoding='utf-8')

class WhatsAppSender:
    def __init__(self, profile_dir="wpp_perfil"):
        self.profile_dir = profile_dir
        self.context = None
        self.page = None
        self.playwright = None

    def iniciar(self, headless=False):
        """Inicializa o navegador com o perfil persistente do WhatsApp"""
        if not os.path.exists(self.profile_dir):
            print(f"🚨 Pasta de perfil '{self.profile_dir}' não encontrada. Por favor, execute salvar_login_whatsapp.py primeiro.")
            return False

        print("🤖 Iniciando navegador com perfil do WhatsApp...")
        self.playwright = sync_playwright().start()
        
        try:
            # Lançamos o contexto persistente direto. Como o perfil já está salvo em wpp_perfil,
            # ele vai restaurar a sessão com Cookies, LocalStorage e IndexedDB intactos.
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=headless,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            # No launch_persistent_context, uma página padrão já é criada.
            # Pegamos ela se existir, senão criamos uma nova.
            if len(self.context.pages) > 0:
                self.page = self.context.pages[0]
            else:
                self.page = self.context.new_page()
            
            print("🔗 Carregando WhatsApp Web...")
            self.page.goto("https://web.whatsapp.com/")
            
            # Aguarda a tela inicial carregar. O input de pesquisa indica que as conversas carregaram.
            print("⏳ Aguardando sincronização das conversas (isso pode levar alguns segundos)...")
            search_bar = self.page.locator('input[data-tab="3"], div[contenteditable="true"][data-tab="3"], div[data-testid="chat-list-search"]').first
            search_bar.wait_for(state="visible", timeout=45000)
            print("✅ WhatsApp Web conectado com sucesso!")
            return True
            
        except Exception as e:
            print(f"🚨 Erro ou tempo limite esgotado ao conectar no WhatsApp Web: {e}")
            self.fechar()
            return False

    def enviar_mensagem_grupo(self, nome_grupo, mensagem, caminho_imagem=None):
        """Pesquisa um grupo pelo nome e envia uma mensagem formatada (com imagem opcional)"""
        if not self.page:
            print("🚨 WhatsApp não está iniciado.")
            return False

        print(f"\n🔍 Procurando o grupo/canal: '{nome_grupo}'...")
        try:
            caminho_imagem_abs = os.path.abspath(caminho_imagem) if caminho_imagem else None

            # 1. Localiza a barra de pesquisa
            search_input = self.page.locator('input[data-tab="3"], div[contenteditable="true"][data-tab="3"], div[data-testid="chat-list-search"]').first
            search_input.click(force=True)
            
            # Limpa qualquer texto anterior
            search_input.fill("")
            # Digita o nome do grupo
            search_input.type(nome_grupo, delay=50)
            self.page.wait_for_timeout(2000) # Aguarda os resultados da pesquisa
            
            # 2. Procura pelo elemento que tem o título exato do grupo na barra lateral
            grupo_locator = self.page.locator(f'span[title="{nome_grupo}"], div[title="{nome_grupo}"]').first
            
            if not grupo_locator.is_visible():
                # Se não achar o título exato, tenta conter o título
                grupo_locator = self.page.locator(f'span[title*="{nome_grupo}"], div[title*="{nome_grupo}"]').first
            
            if grupo_locator.is_visible():
                print(f"👉 Grupo encontrado! Clicando para abrir o chat...")
                grupo_locator.click(force=True)
                self.page.wait_for_timeout(1500) # Espera o chat abrir
                
                # 3. Verifica se tem imagem para enviar com legenda
                if caminho_imagem_abs and os.path.exists(caminho_imagem_abs):
                    print(f"🖼️ Enviando imagem: {os.path.basename(caminho_imagem_abs)} com legenda...")
                    
                    upload_sucesso = False
                    
                    # 1. Abre o menu de anexar (+) e seleciona via File Chooser ou injeção direta de mídia
                    try:
                        plus_btn = self.page.locator('button[data-tab="10"], button[aria-label="Anexar"], button[aria-label="Attach"], button[aria-label="Adjuntar"], span[data-icon="plus-rounded"], span[data-icon="plus"]').first
                        plus_btn.click(timeout=5000, force=True)
                        self.page.wait_for_timeout(800)
                        
                        menu_item = self.page.locator('button[aria-label="Fotos e vídeos"], button[aria-label="Photos & videos"], button[aria-label="Fotos y videos"], button[aria-label*="Fotos"], button[aria-label*="Photos"]').first
                        with self.page.expect_file_chooser(timeout=5000) as fc_info:
                            menu_item.click(timeout=5000, force=True)
                        file_chooser = fc_info.value
                        file_chooser.set_files(caminho_imagem_abs)
                        upload_sucesso = True
                        print("✅ Imagem selecionada via menu de anexo (File Chooser).")
                    except Exception as upload_err:
                        print(f"⚠️ Falha ao anexar via File Chooser: {upload_err}. Tentando injeção direta de mídia...")
                        try:
                            # Filtra especificamente os inputs de fotos/vídeos no DOM, descartando o input de figurinhas (webp)
                            all_inputs = self.page.locator('input[type="file"]').all()
                            media_input = None
                            for inp in all_inputs:
                                accept = (inp.get_attribute("accept") or "").lower()
                                if "image" in accept and "webp" not in accept:
                                    media_input = inp
                                    break
                                elif "image/*" in accept or "video/*" in accept:
                                    media_input = inp
                                    break
                            
                            if not media_input and all_inputs:
                                media_input = all_inputs[0]

                            if media_input:
                                media_input.set_input_files(caminho_imagem_abs)
                                upload_sucesso = True
                            else:
                                print("🚨 Nenhum elemento input file encontrado.")
                                return False
                        except Exception as fb_err:
                            print(f"🚨 Falha ao anexar imagem: {fb_err}")
                            return False

                    # 2. Aguarda a tela de preview da imagem carregar e localiza a caixa de legenda
                    print("⏳ Aguardando tela de preview da imagem...")
                    caption_box = None
                    caption_selectors = [
                        'div[data-testid="media-caption-input-container"]',
                        'div[aria-label*="Adicione uma legenda"]',
                        'div[aria-label*="Add a caption"]',
                        'div[aria-label*="legenda"]',
                        'div[aria-label*="caption"]',
                        'div[contenteditable="true"][data-tab="10"]',
                        'div[contenteditable="true"][data-tab="6"]'
                    ]
                    
                    for selector in caption_selectors:
                        try:
                            loc = self.page.locator(selector).first
                            loc.wait_for(state="visible", timeout=3000)
                            if loc.is_visible():
                                caption_box = loc
                                break
                        except Exception:
                            continue

                    # 3. Foca a caixa de legenda da tela de preview e digita a mensagem formatada
                    if caption_box and caption_box.is_visible():
                        caption_box.focus()
                        caption_box.click(force=True)
                        self.page.wait_for_timeout(300)
                        
                        linhas = mensagem.split("\n")
                        for i, linha in enumerate(linhas):
                            if linha:
                                self.page.keyboard.type(linha, delay=15)
                            if i < len(linhas) - 1:
                                self.page.keyboard.press("Shift+Enter")
                        
                        self.page.wait_for_timeout(500)
                    else:
                        print("⚠️ Caixa de legenda não localizada na tela de preview. A imagem será enviada.")

                    # 4. Confirma o envio da foto com legenda
                    send_btn = self.page.locator('span[data-icon="wds-ic-send-filled"], span[data-icon="send"], div[role="button"][aria-label*="Enviar"], button[aria-label*="Enviar"], button[aria-label*="Send"]').first
                    if send_btn.is_visible():
                        print("👉 Clicando no botão de enviar da tela de preview...")
                        send_btn.click(force=True)
                    else:
                        self.page.keyboard.press("Enter")
                    
                    self.page.wait_for_timeout(1500)
                    print(f"✅ Imagem + legenda enviadas com sucesso para '{nome_grupo}'!")
                    return True
                
                else:
                    # Envio tradicional de apenas texto
                    msg_input = self.page.locator('div[contenteditable="true"][data-tab="10"], div[contenteditable="true"][aria-label*="mensagem"], div[contenteditable="true"][aria-label*="message"]').first
                    msg_input.wait_for(state="visible", timeout=5000)
                    msg_input.click(force=True)
                    
                    print("✍️ Digitando a oferta no grupo de forma humanizada...")
                    linhas = mensagem.split("\n")
                    for i, linha in enumerate(linhas):
                        if linha:
                            self.page.keyboard.type(linha, delay=15)
                        if i < len(linhas) - 1:
                            self.page.keyboard.press("Shift+Enter")
                    
                    self.page.wait_for_timeout(500)
                    self.page.keyboard.press("Enter")
                    print(f"✅ Mensagem enviada com sucesso para '{nome_grupo}'!")
                    self.page.wait_for_timeout(1000)
                    return True
            else:
                print(f"❌ Grupo '{nome_grupo}' não foi encontrado nos resultados de busca.")
                return False
                
        except Exception as e:
            print(f"🚨 Erro ao enviar mensagem para o grupo '{nome_grupo}': {e}")
            return False

    def fechar(self):
        """Fecha o navegador e encerra o Playwright"""
        print("🔌 Fechando navegador do WhatsApp...")
        # No launch_persistent_context, fechamos o context diretamente para encerrar o navegador
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
        print("🚪 Finalizado.")

if __name__ == "__main__":
    import os
    
    # Baixa uma imagem de amostra válida para o teste
    caminho_img = "temp_test.jpg"
    try:
        import urllib.request
        import ssl
        url_test = "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=300&q=80"
        req = urllib.request.Request(url_test, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            with open(caminho_img, "wb") as f:
                f.write(resp.read())
    except Exception:
        with open(caminho_img, "wb") as f:
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x60\x00\x60\x00\x00\xFF\xDB\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c\x20\x24\x2e\x27\x20\x22\x2c\x23\x1c\x1c\x28\x37\x29\x2c\x30\x31\x34\x34\x34\x1f\x27\x39\x3d\x38\x32\x3c\x2e\x33\x34\x32\xFF\xC0\x00\x0B\x08\x00\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00\x10\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x03\xFF\xDA\x00\x08\x01\x01\x00\x00\x3F\x00\x37\xFF\xD9')

    sender = WhatsAppSender()
    if sender.iniciar(headless=False):
        sender.enviar_mensagem_grupo(
            "Ofertas - Geral", 
            "🤖 Teste do Bot de Afiliados!\n\nEste é um teste de envio de imagem com legenda formatada!\n🔥 Se você está lendo isso, a correção funcionou!",
            caminho_imagem=caminho_img
        )
        sender.fechar()
        
    if os.path.exists(caminho_img):
        os.remove(caminho_img)

