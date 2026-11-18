import os
import sys
import io
import json
import asyncio
import subprocess
import urllib.request
import ssl
import urllib3
from PIL import Image, ImageDraw, ImageFont
from shopee_api import buscar_ofertas_do_dia_shopee

# Suprime avisos SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configura stdout UTF-8
sys.stdout.reconfigure(encoding='utf-8')

PASTA_POSTS = "posts_sho_ia"

def carregar_fonte(tamanho, negrito=False):
    """Carrega fonte do Windows (Arial/Segoe UI) ou padrão do PIL"""
    caminhos = [
        "C:/Windows/Fonts/segoeuib.ttf" if negrito else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if negrito else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if negrito else "C:/Windows/Fonts/calibri.ttf"
    ]
    for c in caminhos:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, tamanho)
            except Exception:
                pass
    return ImageFont.load_default()

def quebrar_texto(texto, fonte, largura_max, draw):
    """Quebra o título em múltiplas linhas para caber no card vertical"""
    palavras = texto.split()
    linhas = []
    linha_atual = ""
    for p in palavras:
        teste = (linha_atual + " " + p).strip()
        bbox = draw.textbbox((0, 0), teste, font=fonte)
        if (bbox[2] - bbox[0]) <= largura_max:
            linha_atual = teste
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = p
    if linha_atual:
        linhas.append(linha_atual)
    return linhas[:3]

def baixar_imagem_pil(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGB")

def criar_card_vertical_achadinho(oferta, idx, pasta_saida):
    """
    Cria uma imagem vertical 1080x1920 (formato Reels / TikTok / Stories)
    com a foto do produto, selo de desconto, preço e chamada para o Link da Bio.
    """
    W, H = 1080, 1920
    card = Image.new("RGB", (W, H), (15, 23, 42))
    draw = ImageDraw.Draw(card)

    # Topo Laranja Shopee
    draw.rectangle([(0, 0), (W, 240)], fill=(238, 77, 45))
    fonte_topo = carregar_fonte(54, negrito=True)
    fonte_sub = carregar_fonte(34, negrito=False)

    texto_topo = "ACHADINHO VIRAL DA SHOPEE"
    bbox = draw.textbbox((0, 0), texto_topo, font=fonte_topo)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, 55), texto_topo, fill=(255, 255, 255), font=fonte_topo)

    vendas = oferta.get("vendas", 0)
    sub_topo = f"Nota {oferta.get('nota', 4.9)} / 5.0  |  +{vendas} Vendidos!" if vendas > 0 else "Oferta Relampago Selecionada"
    bbox_sub = draw.textbbox((0, 0), sub_topo, font=fonte_sub)
    draw.text(((W - (bbox_sub[2] - bbox_sub[0])) / 2, 140), sub_topo, fill=(255, 240, 220), font=fonte_sub)

    # Caixa branca central para a foto do produto
    draw.rounded_rectangle([(70, 290), (W - 70, 1180)], radius=35, fill=(255, 255, 255))

    try:
        img_prod = baixar_imagem_pil(oferta["link_imagem"])
        img_prod.thumbnail((840, 800), Image.Resampling.LANCZOS)
        pos_x = (W - img_prod.width) // 2
        pos_y = 290 + (890 - img_prod.height) // 2
        card.paste(img_prod, (pos_x, pos_y))
    except Exception as e:
        print(f"⚠️ Erro ao baixar foto para o card: {e}")

    # Badge de Desconto no canto da foto
    desconto = oferta.get("desconto", 0)
    if desconto > 0:
        draw.rounded_rectangle([(W - 310, 320), (W - 100, 420)], radius=20, fill=(220, 38, 38))
        fonte_desc = carregar_fonte(46, negrito=True)
        txt_desc = f"-{desconto}%"
        b_d = draw.textbbox((0, 0), txt_desc, font=fonte_desc)
        draw.text((W - 310 + (210 - (b_d[2] - b_d[0])) / 2, 340), txt_desc, fill=(255, 255, 255), font=fonte_desc)

    # Título do Produto
    fonte_titulo = carregar_fonte(44, negrito=True)
    linhas_titulo = quebrar_texto(oferta["titulo"], fonte_titulo, W - 160, draw)
    y_texto = 1230
    for linha in linhas_titulo:
        b_l = draw.textbbox((0, 0), linha, font=fonte_titulo)
        draw.text(((W - (b_l[2] - b_l[0])) / 2, y_texto), linha, fill=(248, 250, 252), font=fonte_titulo)
        y_texto += 58

    # Caixa de Preço
    preco_orig = oferta.get("preco_original", 0.0)
    preco_atual = oferta.get("preco_atual", 0.0)

    if preco_orig > preco_atual:
        fonte_old = carregar_fonte(38, negrito=False)
        txt_old = f"De: R$ {preco_orig:.2f}".replace(".", ",")
        b_o = draw.textbbox((0, 0), txt_old, font=fonte_old)
        draw.text(((W - (b_o[2] - b_o[0])) / 2, 1440), txt_old, fill=(148, 163, 184), font=fonte_old)

    draw.rounded_rectangle([(140, 1505), (W - 140, 1645)], radius=28, fill=(34, 197, 94))
    fonte_preco = carregar_fonte(68, negrito=True)
    txt_preco = f"POR R$ {preco_atual:.2f}".replace(".", ",")
    b_p = draw.textbbox((0, 0), txt_preco, font=fonte_preco)
    draw.text(((W - (b_p[2] - b_p[0])) / 2, 1532), txt_preco, fill=(255, 255, 255), font=fonte_preco)

    # Rodapé CTA (Link na Bio / Grupo VIP)
    draw.rounded_rectangle([(90, 1695), (W - 90, 1850)], radius=25, fill=(30, 41, 59), outline=(238, 77, 45), width=4)
    fonte_cta = carregar_fonte(40, negrito=True)
    txt_cta1 = "LINK DO PRODUTO E GRUPO VIP"
    txt_cta2 = ">> CLIQUE NO LINK DA NOSSA BIO! <<"
    b_c1 = draw.textbbox((0, 0), txt_cta1, font=fonte_cta)
    b_c2 = draw.textbbox((0, 0), txt_cta2, font=fonte_cta)
    draw.text(((W - (b_c1[2] - b_c1[0])) / 2, 1718), txt_cta1, fill=(251, 146, 60), font=fonte_cta)
    draw.text(((W - (b_c2[2] - b_c2[0])) / 2, 1775), txt_cta2, fill=(255, 255, 255), font=fonte_cta)

    caminho_img = os.path.join(pasta_saida, f"story_achadinho_{idx}.jpg")
    card.save(caminho_img, format="JPEG", quality=95)
    return caminho_img

async def _gerar_audio_edge_tts(texto, caminho_mp3):
    import edge_tts
    # Voz neural brasileira muito natural e animada (Francisca ou Antonio)
    communicate = edge_tts.Communicate(texto, voice="pt-BR-FranciscaNeural", rate="+12%")
    await communicate.save(caminho_mp3)

def gerar_narracao_ia(texto, caminho_mp3):
    """
    Gera o áudio MP3 da locução com IA em português.
    Tenta usar a voz neural Microsoft Edge-TTS primeiro; se a rede corporativa bloquear WebSocket,
    faz fallback automático para Google TTS (gTTS) com bypass SSL.
    """
    try:
        asyncio.run(_gerar_audio_edge_tts(texto, caminho_mp3))
        if os.path.exists(caminho_mp3) and os.path.getsize(caminho_mp3) > 500:
            return True
    except Exception:
        pass

    # Fallback gTTS (funciona mesmo em redes com proxy SSL corporativo)
    try:
        import requests
        from gtts import gTTS
        old_request = requests.Session.request
        def patched_request(self, *args, **kwargs):
            kwargs['verify'] = False
            return old_request(self, *args, **kwargs)
        requests.Session.request = patched_request
        tts = gTTS(text=texto, lang='pt', tld='com.br', slow=False)
        tts.save(caminho_mp3)
        requests.Session.request = old_request
        return os.path.exists(caminho_mp3) and os.path.getsize(caminho_mp3) > 500
    except Exception as e:
        print(f"⚠️ Erro ao gerar áudio de narração: {e}")
        return False

def criar_video_mp4_reels(caminho_img, caminho_mp3, caminho_mp4):
    """
    Combina o Card 1080x1920 + Áudio da Narração IA em um vídeo MP4 (H.264 + AAC)
    pronto para postar no Instagram Reels, TikTok, YouTube Shorts e Status do WhatsApp.
    """
    try:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", caminho_img,
            "-i", caminho_mp3,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1080:1920",
            "-shortest",
            caminho_mp4
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
        return res.returncode == 0 and os.path.exists(caminho_mp4)
    except Exception as e:
        print(f"⚠️ Erro ao renderizar vídeo MP4 via FFmpeg: {e}")
        return False

def formatar_preco_fala(valor):
    """Converte 39.90 em '39 reais e 90 centavos' para a voz de IA falar naturalmente"""
    reais = int(valor)
    centavos = int(round((valor - reais) * 100))
    if centavos > 0:
        return f"{reais} reais e {centavos} centavos"
    return f"{reais} reais"

def limpar_titulo_para_fala(titulo):
    """Pega apenas as primeiras 6 a 8 palavras principais do produto para a voz não ler códigos técnicos"""
    palavras = [p for p in titulo.replace("/", " ").replace("-", " ").split() if len(p) > 1]
    return " ".join(palavras[:7])

def gerar_kit_achadinhos_sho_ia(quantidade=5):
    """
    Busca os melhores achadinhos da Shopee, gera:
    1. Cards 9:16 em JPG (para Stories / Feed)
    2. Narração com Voz de IA em MP3
    3. Vídeos MP4 completos (Imagem + Voz de IA) prontos para Reels, TikTok e Shorts!
    4. Arquivo de texto com as legendas e hashtags prontas para copiar e colar.
    """
    os.makedirs(PASTA_POSTS, exist_ok=True)
    print(f"🚀 [Sho IA] Buscando os {quantidade} Achadinhos mais virais da Shopee agora...")
    ofertas = buscar_ofertas_do_dia_shopee(desconto_minimo=25, limite=quantidade)

    if not ofertas:
        print("⚠️ Nenhuma oferta retornada pela API da Shopee.")
        return

    roteiros_txt = []
    roteiros_txt.append("=========================================================")
    roteiros_txt.append("🤖 KIT DIÁRIO SHO IA - VÍDEOS REELS / TIKTOK / STORIES PRONTOS")
    roteiros_txt.append("=========================================================\n")

    for i, item in enumerate(ofertas, start=1):
        caminho_card = criar_card_vertical_achadinho(item, i, PASTA_POSTS)
        print(f"🖼️ [{i}/{len(ofertas)}] Card vertical gerado: {caminho_card}")

        nome_curto = limpar_titulo_para_fala(item["titulo"])
        preco_fala = formatar_preco_fala(item["preco_atual"])
        roteiro_voz = (
            f"Olha esse achadinho viral da Shopee com {item['desconto']} por cento de desconto! "
            f"{nome_curto}, saindo por apenas {preco_fala}! "
            f"Comente EU QUERO ou clique agora no link da nossa bio para pegar essa promoção e entrar no nosso Grupo VIP de Ofertas no WhatsApp!"
        )

        caminho_mp3 = os.path.join(PASTA_POSTS, f"narracao_{i}.mp3")
        caminho_mp4 = os.path.join(PASTA_POSTS, f"video_reels_tiktok_{i}.mp4")

        print(f"🎙️ [{i}/{len(ofertas)}] Gerando narração com voz de IA...")
        if gerar_narracao_ia(roteiro_voz, caminho_mp3):
            print(f"🎬 [{i}/{len(ofertas)}] Montando vídeo MP4 para Reels/TikTok...")
            if criar_video_mp4_reels(caminho_card, caminho_mp3, caminho_mp4):
                print(f"✅ [{i}/{len(ofertas)}] Vídeo MP4 pronto: {caminho_mp4}")
                # Remove o mp3 temporário para deixar a pasta limpa só com o JPG e o MP4
                try:
                    os.remove(caminho_mp3)
                except Exception:
                    pass

        legenda = (
            f"😱 Olha esse achadinho da Shopee com {item['desconto']}% de desconto!\n\n"
            f"🛍️ {item['titulo']}\n"
            f"❌ De: R$ {item['preco_original']:.2f}\n"
            f"💰 Por apenas: R$ {item['preco_atual']:.2f} 🔥\n\n"
            f"👉 Comente 'EU QUERO' ou clique no LINK DA BIO para pegar o link direto e entrar no nosso Grupo VIP de Ofertas no WhatsApp!\n\n"
            f"#achadinhos #achadinhosdashopee #shopee #shopeebrasil #ofertas #promocao #desconto"
        )

        roteiros_txt.append(f"--- POST #{i} ---")
        roteiros_txt.append(f"🎬 Vídeo Reels/TikTok (com voz IA): {caminho_mp4}")
        roteiros_txt.append(f"🖼️ Imagem Story: {caminho_card}")
        roteiros_txt.append(f"🔗 Seu Link Afiliado Direto: {item['link_bruto']}")
        roteiros_txt.append(f"\n📝 LEGENDA PARA COPIAR E COLAR NO INSTAGRAM / TIKTOK:\n{legenda}\n")
        roteiros_txt.append("---------------------------------------------------------\n")

    caminho_roteiro = os.path.join(PASTA_POSTS, "LEGENDAS_E_LINKS.txt")
    with open(caminho_roteiro, "w", encoding="utf-8") as f:
        f.write("\n".join(roteiros_txt))

    print(f"\n🎉 Pronto! {len(ofertas)} VÍDEOS MP4 + ARTES JPG + LEGENDAS salvos na pasta '{PASTA_POSTS}'!")
    print(f"📄 Abra '{caminho_roteiro}' para copiar as legendas.")

if __name__ == "__main__":
    gerar_kit_achadinhos_sho_ia(quantidade=5)
