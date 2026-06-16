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
                args=['--disable-blink-features=AutomationControlled']
            )
            
            # No launch_persistent_context, uma página padrão já é criada.
            # Pegamos ela se existir, senão criamos uma nova.
            if len(self.context.pages) > 0:
                self.page = self.context.pages[0]
            else:
                self.page = self.context.new_page()
            
            print("🔗 Carregando WhatsApp Web...")
            self.page.goto("https://web.whatsapp.com/")
            
            # Aguarda a tela inicial carregar. O input de pesquisa input[data-tab="3"] indica que as conversas carregaram.
            print("⏳ Aguardando sincronização das conversas (isso pode levar alguns segundos)...")
            self.page.locator('input[data-tab="3"]').first.wait_for(state="visible", timeout=45000)
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
            # 1. Localiza a barra de pesquisa
            search_input = self.page.locator('input[data-tab="3"]').first
            search_input.click()
            
            # Limpa qualquer texto anterior
            search_input.fill("")
            # Digita o nome do grupo
            search_input.type(nome_grupo, delay=50)
            self.page.wait_for_timeout(2000) # Aguarda os resultados da pesquisa
            
            # 2. Procura pelo elemento que tem o título exato do grupo na barra lateral
            grupo_locator = self.page.locator(f'span[title="{nome_grupo}"]').first
            
            if not grupo_locator.is_visible():
                # Se não achar o título exato, tenta conter o título
                grupo_locator = self.page.locator(f'span[title*="{nome_grupo}"]').first
            
            if grupo_locator.is_visible():
                print(f"👉 Grupo encontrado! Clicando para abrir o chat...")
                grupo_locator.click()
                self.page.wait_for_timeout(1500) # Espera o chat abrir
                
                # 3. Verifica se tem imagem para enviar com legenda
                if caminho_imagem and os.path.exists(caminho_imagem):
                    print(f"🖼️ Enviando imagem: {caminho_imagem} com legenda...")
                    
                    upload_sucesso = False
                    try:
                        # 1. Abre o menu de anexar (+)
                        plus_btn = self.page.locator('button[aria-label="Anexar"], button[aria-label="Attach"], button[aria-label="Adjuntar"], span[data-icon="plus-rounded"], span[data-icon="plus"], span[data-testid="plus-rounded"]').first
                        plus_btn.click(timeout=5000)
                        self.page.wait_for_timeout(1000)
                        
                        # 2. Clica no item de menu "Fotos e vídeos" via File Chooser
                        menu_item = self.page.locator('button[aria-label="Fotos e vídeos"], button[aria-label="Photos & videos"], button[aria-label="Fotos y videos"], button[aria-label*="Fotos"], button[aria-label*="Photos"]').first
                        with self.page.expect_file_chooser(timeout=5000) as fc_info:
                            menu_item.click(timeout=5000)
                        file_chooser = fc_info.value
                        file_chooser.set_files(caminho_imagem)
                        upload_sucesso = True
                        print("✅ Upload da imagem feito via menu de anexo.")
                    except Exception as upload_err:
                        print(f"⚠️ Falha ao fazer upload pelo menu de anexo ({upload_err}). Tentando fallback direto...")
                        
                    if not upload_sucesso:
                        # Fallback: define diretamente nos inputs de arquivo existentes
                        media_locator = self.page.locator('input[type="file"][accept*="video"]')
                        if media_locator.count() > 0:
                            input_file = media_locator.first
                        else:
                            media_locator_img = self.page.locator('input[type="file"][accept*="image"]')
                            if media_locator_img.count() > 0:
                                input_file = media_locator_img.first
                            else:
                                input_file = self.page.locator('input[type="file"]').first
                        input_file.set_input_files(caminho_imagem)
                    
                    self.page.wait_for_timeout(2500) # Aguarda carregar o preview
                    
                    # Localiza a caixa de texto da legenda (na tela de preview)
                    caption_input = self.page.locator('div[data-testid="media-caption-input-container"], div[contenteditable="true"]:not([data-testid="conversation-compose-box-input"])').first
                    caption_input.focus()
                    caption_input.click(force=True)
                    self.page.wait_for_timeout(500)
                    
                    # Digita a mensagem formatada na legenda
                    linhas = mensagem.split("\n")
                    for i, linha in enumerate(linhas):
                        if linha:
                            self.page.keyboard.type(linha, delay=15)
                        if i < len(linhas) - 1:
                            self.page.keyboard.press("Shift+Enter")
                    
                    self.page.wait_for_timeout(1000)
                    
                    # Pressiona Enter para enviar
                    self.page.keyboard.press("Enter")
                    
                    # Espera um pouco e clica no botão de enviar caso ainda esteja na tela
                    self.page.wait_for_timeout(1500)
                    send_btn = self.page.locator('span[data-icon="wds-ic-send-filled"], span[data-icon="send"], div[role="button"][aria-label*="Enviar"]').first
                    if send_btn.is_visible():
                        print("👉 Clicando no botão de enviar da tela de preview...")
                        send_btn.click()
                        self.page.wait_for_timeout(1000)
                    
                    print(f"✅ Imagem enviada com sucesso para '{nome_grupo}'!")
                    return True
                
                else:
                    # Envio tradicional de apenas texto
                    # Localiza a caixa de texto da mensagem
                    msg_input = self.page.locator('div[contenteditable="true"][data-tab="10"]').first
                    msg_input.wait_for(state="visible", timeout=5000)
                    msg_input.click()
                    
                    # Digita a mensagem pulando linhas de forma humanizada (simula status "digitando...")
                    print("✍️ Digitando a oferta no grupo de forma humanizada...")
                    linhas = mensagem.split("\n")
                    for i, linha in enumerate(linhas):
                        if linha:
                            # delay de 15ms por caractere simula digitação humana no WhatsApp Web
                            self.page.keyboard.type(linha, delay=15)
                        if i < len(linhas) - 1:
                            self.page.keyboard.press("Shift+Enter")
                    
                    self.page.wait_for_timeout(500)
                    
                    # Pressiona Enter para enviar
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
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        print("🚪 Finalizado.")

if __name__ == "__main__":
    import os
    
    # Cria uma imagem temporária de teste
    caminho_img = "temp_test.jpg"
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
