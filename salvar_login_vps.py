import sys
import os
import time
import http.server
import socketserver
import threading
from playwright.sync_api import sync_playwright

PERFIL_DIR = "wpp_perfil"
PORT = 8080

def iniciar_servidor_qrcode():
    class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            super().end_headers()

    with socketserver.TCPServer(("", PORT), NoCacheHTTPRequestHandler) as httpd:
        print(f"\n🌐 Servidor ativo! Atualize a página se precisar:")
        print(f"👉 http://localhost:{PORT}/qrcode.png\n")
        httpd.serve_forever()

def salvar_sessao():
    thread_servidor = threading.Thread(target=iniciar_servidor_qrcode, daemon=True)
    thread_servidor.start()

    with sync_playwright() as p:
        print("🚀 Abrindo navegador Playwright...")
        contexto = p.chromium.launch_persistent_context(
            user_data_dir=PERFIL_DIR,
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ],
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        pagina = contexto.new_page()

        print("🔗 Acessando o WhatsApp Web...")
        pagina.goto("https://web.whatsapp.com/", timeout=90000)

        print("⏳ Aguardando o QR Code aparecer na tela...")
        # Espera o seletor do QR Code aparecer de verdade
        try:
            pagina.wait_for_selector("canvas", timeout=45000)
            print("✨ Canvas do QR Code detectado!")
        except Exception:
            print("⚠️ Demorou um pouco, capturando screenshot do estado atual...")

        # Aguarda 3 segundos para renderizar completamente os pixels do QR
        time.sleep(3)
        pagina.screenshot(path="qrcode.png")
        print("📸 QR Code gerado! Atualize a página: http://localhost:8080/qrcode.png")
        print("📲 Aponte a câmera do WhatsApp para escanear agora...")

        # Loop aguardando o login
        logado = False
        for i in range(80):  # Aguarda até 4 minutos
            time.sleep(3)

            # Atualiza o screenshot a cada 10 segundos caso mude
            if i % 3 == 0:
                try:
                    pagina.screenshot(path="qrcode.png")
                except:
                    pass

            try:
                # Se aparecer a lista de conversas, o usuário logou!
                if pagina.locator("#side, [data-testid='chat-list'], [aria-label='Chat list']").count() > 0:
                    logado = True
                    break
            except:
                pass

        if logado:
            print("\n🎉🎉 LOGIN REALIZADO COM SUCESSO! 🎉🎉")
            print("⏳ Aguardando 12 segundos para baixar conversas e sincronizar tokens...")
            time.sleep(12)
        else:
            print("\n⚠️ Tempo limite atingido. Salvando sessão atual...")

        print("💾 Gravando dados persistentes em 'wpp_perfil'...")
        contexto.close()
        print("\n✅ Pronto! Perfil do WhatsApp salvo com sucesso.")

if __name__ == "__main__":
    salvar_sessao()
