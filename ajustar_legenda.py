caminho = "/home/ubuntu/BotOfertasWhatsApp/whatsapp_sender.py"

with open(caminho, "r", encoding="utf-8") as f:
    codigo = f.read()

bloco_antigo = """                    for selector in caption_selectors:
                        try:
                            loc = self.page.locator(selector).first
                            loc.wait_for(state="visible", timeout=3000)
                            if loc.is_visible():
                                caption_box = loc
                                break
                        except Exception:
                            continue"""

bloco_novo = """                    for tentativa in range(6):
                        for selector in caption_selectors:
                            try:
                                loc = self.page.locator(selector).first
                                if loc.is_visible():
                                    caption_box = loc
                                    break
                            except Exception:
                                continue
                        if caption_box:
                            break
                        self.page.wait_for_timeout(1000)"""

if bloco_antigo in codigo:
    codigo = codigo.replace(bloco_antigo, bloco_novo)
    print("✅ Bloco de espera da legenda atualizado!")
else:
    print("⚠️ Bloco antigo não bateu 100%, aumentando timeout geral...")
    codigo = codigo.replace('timeout=3000', 'timeout=8000')

with open(caminho, "w", encoding="utf-8") as f:
    f.write(codigo)

print("🚀 Ajuste de legenda finalizado!")
