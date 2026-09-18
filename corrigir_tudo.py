import re
import os

# 1. Ajusta o motor_integrado.py para usar nomes únicos de imagem por produto (ex: temp_img_12345.jpg)
# e nunca mais reutilizar foto antiga!
caminho_motor = "/home/ubuntu/BotOfertasWhatsApp/motor_integrado.py"
with open(caminho_motor, "r", encoding="utf-8") as f:
    cod_motor = f.read()

cod_motor = cod_motor.replace(
    'caminho_imagem = "temp_oferta.jpg"',
    'caminho_imagem = f"temp_{idx}_{int(time.time())}.jpg"'
)

with open(caminho_motor, "w", encoding="utf-8") as f:
    f.write(cod_motor)
print("✅ motor_integrado.py atualizado para fotos únicas!")

# 2. Atualiza o whatsapp_sender.py com colagem instantânea segura (sem cortar nem misturar texto)
caminho_wpp = "/home/ubuntu/BotOfertasWhatsApp/whatsapp_sender.py"
with open(caminho_wpp, "r", encoding="utf-8") as f:
    cod_wpp = f.read()

novo_bloco = """                    # 3. Foca a caixa de legenda e insere o texto completo de forma atômica
                    if not caption_box or not caption_box.is_visible():
                        print("🚨 Caixa de legenda NÃO encontrada na tela de preview. Abortando envio para evitar foto sem texto.")
                        self.page.keyboard.press("Escape")
                        self.page.wait_for_timeout(1000)
                        return False

                    caption_box.focus()
                    caption_box.click(force=True)
                    self.page.wait_for_timeout(400)
                    
                    try:
                        self.page.evaluate('''text => {
                            const dt = new DataTransfer();
                            dt.setData('text/plain', text);
                            const ev = new ClipboardEvent('paste', {
                                clipboardData: dt,
                                bubbles: true,
                                cancelable: true
                            });
                            document.activeElement.dispatchEvent(ev);
                        }''', mensagem)
                    except Exception:
                        linhas = mensagem.split("\\n")
                        for i, linha in enumerate(linhas):
                            if linha:
                                self.page.keyboard.insert_text(linha)
                            if i < len(linhas) - 1:
                                self.page.keyboard.press("Shift+Enter")

                    self.page.wait_for_timeout(1000)

                    # 4. Confirma o envio da foto com legenda
                    send_btn = self.page.locator('span[data-icon="wds-ic-send-filled"], span[data-icon="send"], div[role="button"][aria-label*="Enviar"], button[aria-label*="Enviar"], button[aria-label*="Send"]').first
                    if send_btn.is_visible():
                        send_btn.click(force=True)
                    else:
                        self.page.keyboard.press("Enter")
                    
                    try:
                        self.page.wait_for_selector('div[data-testid="media-caption-input-container"]', state="detached", timeout=15000)
                    except Exception:
                        self.page.wait_for_timeout(3000)

                    print(f"✅ Imagem + legenda enviadas com sucesso para '{nome_grupo}'!")
                    return True"""

padrao = r"# 3\. Foca a caixa de legenda.*?(?=else:\s*# Envio tradicional)"
cod_wpp_novo = re.sub(padrao, novo_bloco + "\n                \n                ", cod_wpp, flags=re.DOTALL)

with open(caminho_wpp, "w", encoding="utf-8") as f:
    f.write(cod_wpp_novo)
print("✅ whatsapp_sender.py corrigido com sucesso!")
