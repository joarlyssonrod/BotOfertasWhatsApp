import os
import sys
import json
import time
import datetime
import html

# Configura o stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

LINK_GRUPO_WHATSAPP = "https://chat.whatsapp.com/ESwoDxf8R0rK36wuIsjqHz"
VITRINE_HTML_FILE = "index.html"
VITRINE_JSON_FILE = "vitrine_ofertas.json"

def identificar_loja(item):
    """Identifica o nome da loja e a cor de destaque com base no link ou ID"""
    loja = item.get("loja", "")
    if loja:
        return loja
    link = (item.get("link_afiliado") or item.get("link_bruto") or "").lower()
    item_id = (item.get("id") or "").upper()
    if "shopee" in link or item_id.startswith("SHOPEE"):
        return "Shopee"
    elif "amazon" in link or item_id.startswith("AMAZON"):
        return "Amazon"
    elif "mercadoli" in link or item_id.startswith("ML"):
        return "Mercado Livre"
    elif "magazin" in link or item_id.startswith("MAGALU"):
        return "Magalu"
    elif "aliexpress" in link or item_id.startswith("ALIEXPRESS"):
        return "AliExpress"
    return "Oferta"

def carregar_vitrine_cache():
    if os.path.exists(VITRINE_JSON_FILE):
        try:
            with open(VITRINE_JSON_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, list):
                    return dados
        except Exception:
            pass
    return []

def salvar_vitrine_cache(ofertas):
    try:
        with open(VITRINE_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(ofertas[:80], f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ [Vitrine] Erro ao salvar cache da vitrine: {e}")

def atualizar_vitrine_html(novas_ofertas=None, historico=None):
    """
    Atualiza o cache de ofertas ricas (com foto, desconto, link afiliado) e
    gera um index.html moderno estilo 'Sho IA / Linktree de Achadinhos' pronto para GitHub Pages.
    """
    cache = carregar_vitrine_cache()
    ids_existentes = {c.get("id") for c in cache if c.get("id")}

    if novas_ofertas:
        for item in reversed(novas_ofertas):
            item_id = item.get("id") or item.get("link_bruto")
            if item_id and item_id not in ids_existentes:
                registro = {
                    "id": item_id,
                    "titulo": item.get("titulo", "Produto em Oferta"),
                    "preco_atual": float(item.get("preco_atual") or item.get("preco") or 0.0),
                    "preco_original": float(item.get("preco_original") or 0.0),
                    "desconto": int(float(item.get("desconto") or 0)),
                    "link_afiliado": item.get("link_afiliado") or item.get("link_bruto") or "#",
                    "link_imagem": item.get("link_imagem") or "",
                    "cupom": item.get("cupom") or "",
                    "vendas": int(item.get("vendas") or 0),
                    "loja": identificar_loja(item),
                    "timestamp": time.time()
                }
                cache.insert(0, registro)
                ids_existentes.add(item_id)

    # Se o cache estiver pequeno, completa apenas com itens do histórico que tenham foto real (link_imagem)
    if len(cache) < 24 and historico:
        from bot_afiliado import gerar_link_bot
        ultimos_hist = [
            h for h in reversed(historico)
            if isinstance(h, dict) and h.get("titulo") and h.get("preco", 0) > 0 and h.get("link_imagem")
        ]
        for h in ultimos_hist[:30]:
            h_id = h.get("id")
            if h_id and h_id not in ids_existentes:
                link_af = h.get("link_afiliado")
                if not link_af:
                    # Converte link rápido sem travar
                    link_bruto = h.get("link_bruto", "")
                    if "s.shopee.com.br" in link_bruto or "magazinevoce" in link_bruto:
                        link_af = link_bruto
                    else:
                        link_af = gerar_link_bot(link_bruto) or link_bruto
                preco_at = float(h.get("preco", 0.0))
                preco_orig = float(h.get("preco_original") or round(preco_at * 1.25, 2))
                desc = int(h.get("desconto") or round(((preco_orig - preco_at) / preco_orig) * 100))
                cache.append({
                    "id": h_id,
                    "titulo": h.get("titulo"),
                    "preco_atual": preco_at,
                    "preco_original": preco_orig,
                    "desconto": desc,
                    "link_afiliado": link_af,
                    "link_imagem": h.get("link_imagem") or "",
                    "cupom": h.get("cupom") or "",
                    "vendas": int(h.get("vendas") or 0),
                    "loja": identificar_loja(h),
                    "timestamp": h.get("timestamp", time.time())
                })
                ids_existentes.add(h_id)
            if len(cache) >= 48:
                break

    salvar_vitrine_cache(cache)

    agora_str = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")

    # Monta os cards HTML
    cards_html = []
    for prod in cache[:48]:
        titulo_safe = html.escape(prod.get("titulo", "Achadinho em Oferta"))
        preco_atual = prod.get("preco_atual", 0.0)
        preco_orig = prod.get("preco_original", 0.0)
        desconto = prod.get("desconto", 0)
        link_af = html.escape(prod.get("link_afiliado", "#"))
        img_url = html.escape(prod.get("link_imagem") or "https://placehold.co/400x400/1e293b/f8fafc?text=Oferta+VIP")
        loja = prod.get("loja", "Oferta")
        cupom = html.escape(prod.get("cupom") or "")
        vendas = prod.get("vendas", 0)

        badge_cor = {
            "Shopee": "#ee4d2d",
            "Amazon": "#ff9900",
            "Mercado Livre": "#ffe600; color: #111",
            "Magalu": "#0086ff",
            "AliExpress": "#e62e04"
        }.get(loja, "#10b981")

        preco_orig_html = f'<span class="old-price">R$ {preco_orig:,.2f}</span>'.replace(",", "X").replace(".", ",").replace("X", ".") if preco_orig > preco_atual else ""
        preco_atual_fmt = f"R$ {preco_atual:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        cupom_html = f'<div class="coupon-tag">🏷️ Cupom: <strong>{cupom}</strong></div>' if cupom else ""
        vendas_html = f'<span class="sales-badge">🔥 +{vendas} vendidos</span>' if vendas >= 50 else ""

        card = f"""
        <div class="card" data-store="{loja.lower()}" data-title="{titulo_safe.lower()}">
            <div class="card-img-wrap">
                <span class="store-badge" style="background: {badge_cor};">{loja}</span>
                {f'<span class="discount-badge">-{desconto}%</span>' if desconto > 0 else ''}
                <img src="{img_url}" alt="{titulo_safe}" loading="lazy" onerror="this.src='https://placehold.co/400x400/1e293b/f8fafc?text={loja}'">
            </div>
            <div class="card-body">
                {vendas_html}
                <h3 class="card-title">{titulo_safe}</h3>
                {cupom_html}
                <div class="price-box">
                    {preco_orig_html}
                    <span class="current-price">{preco_atual_fmt}</span>
                </div>
                <a href="{link_af}" target="_blank" rel="noopener noreferrer" class="buy-btn">
                    🛒 Pegar Promoção
                </a>
            </div>
        </div>
        """
        cards_html.append(card)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Achadinhos & Ofertas VIP 🔥 | Descontos em Tempo Real</title>
    <meta name="description" content="As melhores ofertas, bugs e achadinhos da Shopee, Amazon, Mercado Livre e Magalu monitorados por Inteligência Artificial.">
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text: #f8fafc;
            --muted: #94a3b8;
            --accent: #22c55e;
            --shopee: #ee4d2d;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }}
        body {{ background: var(--bg); color: var(--text); padding-bottom: 60px; }}
        .hero {{
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #31102f 100%);
            padding: 28px 16px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .hero-badge {{
            display: inline-block;
            background: rgba(238, 77, 45, 0.2);
            color: #ff785a;
            border: 1px solid rgba(238, 77, 45, 0.4);
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        .hero h1 {{ font-size: 1.6rem; margin-bottom: 8px; line-height: 1.2; }}
        .hero p {{ color: var(--muted); font-size: 0.95rem; max-width: 520px; margin: 0 auto 18px; }}
        .wpp-cta {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: #fff;
            text-decoration: none;
            font-weight: 800;
            font-size: 1.05rem;
            padding: 15px 26px;
            border-radius: 14px;
            box-shadow: 0 0 25px rgba(34, 197, 94, 0.5);
            animation: pulse 2s infinite;
            transition: transform 0.2s;
            max-width: 95%;
        }}
        .wpp-cta:hover {{ transform: scale(1.03); }}
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.6); }}
            70% {{ box-shadow: 0 0 0 14px rgba(34, 197, 94, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
        }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 18px 14px; }}
        .controls {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 20px;
        }}
        .search-input {{
            width: 100%;
            padding: 13px 16px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.15);
            background: var(--card-bg);
            color: #fff;
            font-size: 0.95rem;
            outline: none;
        }}
        .search-input:focus {{ border-color: #38bdf8; }}
        .filters {{
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 4px;
        }}
        .filter-btn {{
            background: var(--card-bg);
            color: var(--muted);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 8px 14px;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
        }}
        .filter-btn.active {{
            background: #ee4d2d;
            color: #fff;
            border-color: #ee4d2d;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(165px, 1fr));
            gap: 14px;
        }}
        @media (min-width: 640px) {{
            .grid {{ grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 18px; }}
            .hero h1 {{ font-size: 2.1rem; }}
        }}
        .card {{
            background: var(--card-bg);
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.07);
            display: flex;
            flex-direction: column;
            transition: transform 0.2s;
        }}
        .card:hover {{ transform: translateY(-4px); }}
        .card-img-wrap {{
            position: relative;
            width: 100%;
            padding-top: 90%;
            background: #fff;
        }}
        .card-img-wrap img {{
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            object-fit: contain;
            padding: 8px;
        }}
        .store-badge {{
            position: absolute;
            top: 8px; left: 8px;
            z-index: 2;
            color: #fff;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
        }}
        .discount-badge {{
            position: absolute;
            top: 8px; right: 8px;
            z-index: 2;
            background: #dc2626;
            color: #fff;
            font-size: 0.75rem;
            font-weight: 800;
            padding: 3px 7px;
            border-radius: 6px;
        }}
        .card-body {{
            padding: 12px;
            display: flex;
            flex-direction: column;
            flex: 1;
            justify-content: space-between;
        }}
        .sales-badge {{
            font-size: 0.72rem;
            color: #fb923c;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .card-title {{
            font-size: 0.86rem;
            font-weight: 600;
            line-height: 1.35;
            margin-bottom: 8px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        .coupon-tag {{
            background: rgba(234, 179, 8, 0.15);
            border: 1px dashed #eab308;
            color: #fde047;
            font-size: 0.75rem;
            padding: 4px 6px;
            border-radius: 6px;
            margin-bottom: 8px;
        }}
        .price-box {{ margin-bottom: 10px; }}
        .old-price {{
            display: block;
            font-size: 0.75rem;
            color: var(--muted);
            text-decoration: line-through;
        }}
        .current-price {{
            font-size: 1.15rem;
            font-weight: 800;
            color: #4ade80;
        }}
        .buy-btn {{
            display: block;
            text-align: center;
            background: #ee4d2d;
            color: #fff;
            text-decoration: none;
            font-weight: 700;
            font-size: 0.85rem;
            padding: 10px;
            border-radius: 9px;
            transition: opacity 0.2s;
        }}
        .buy-btn:hover {{ opacity: 0.9; }}
        .footer {{
            text-align: center;
            color: var(--muted);
            font-size: 0.8rem;
            margin-top: 32px;
            padding: 0 16px;
        }}
        .floating-wpp {{
            position: fixed;
            bottom: 16px;
            right: 16px;
            background: #22c55e;
            color: #fff;
            text-decoration: none;
            font-weight: 700;
            font-size: 0.9rem;
            padding: 12px 18px;
            border-radius: 999px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            z-index: 50;
        }}
    </style>
</head>
<body>
    <header class="hero">
        <span class="hero-badge">⚡ MONITORADO POR IA 24H</span>
        <h1>Achadinhos & Ofertas VIP 🔥</h1>
        <p>As melhores promoções da Shopee, Amazon, Mercado Livre e Magalu antes de acabarem! Entre no grupo para receber no celular:</p>
        <a href="{LINK_GRUPO_WHATSAPP}" target="_blank" class="wpp-cta">
            📲 ENTRAR NO GRUPO VIP DO WHATSAPP (GRÁTIS)
        </a>
    </header>

    <main class="container">
        <div class="controls">
            <input type="text" id="searchInput" class="search-input" placeholder="🔍 Buscar achadinho (ex: fone, airfryer, creatina, celular)...">
            <div class="filters">
                <button class="filter-btn active" onclick="filterStore('all', this)">🔥 Todas</button>
                <button class="filter-btn" onclick="filterStore('shopee', this)">🟠 Shopee</button>
                <button class="filter-btn" onclick="filterStore('amazon', this)">🟡 Amazon</button>
                <button class="filter-btn" onclick="filterStore('mercado livre', this)">🤝 Mercado Livre</button>
                <button class="filter-btn" onclick="filterStore('magalu', this)">🔵 Magalu</button>
            </div>
        </div>

        <div class="grid" id="offersGrid">
            {''.join(cards_html)}
        </div>
    </main>

    <footer class="footer">
        <p>Última atualização automática: {agora_str}</p>
        <p style="margin-top:6px;">Como afiliado, ganhamos com compras qualificadas. Preços e estoques sujeitos a alteração pelas lojas.</p>
    </footer>

    <a href="{LINK_GRUPO_WHATSAPP}" target="_blank" class="floating-wpp">
        🟢 Entrar no Grupo VIP
    </a>

    <script>
        let currentStore = 'all';
        const searchInput = document.getElementById('searchInput');
        const cards = document.querySelectorAll('.card');

        function applyFilters() {{
            const q = searchInput.value.toLowerCase().trim();
            cards.forEach(card => {{
                const store = card.getAttribute('data-store');
                const title = card.getAttribute('data-title');
                const matchStore = (currentStore === 'all') || (store === currentStore);
                const matchText = !q || title.includes(q);
                card.style.display = (matchStore && matchText) ? 'flex' : 'none';
            }});
        }}

        function filterStore(store, btn) {{
            currentStore = store;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            applyFilters();
        }}

        searchInput.addEventListener('input', applyFilters);
    </script>
</body>
</html>
"""
    try:
        with open(VITRINE_HTML_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"🌐 [Vitrine Web] Página '{VITRINE_HTML_FILE}' atualizada com {len(cards_html)} ofertas!")
        return True
    except Exception as e:
        print(f"⚠️ [Vitrine Web] Erro ao gerar '{VITRINE_HTML_FILE}': {e}")
        return False

if __name__ == "__main__":
    print("🧪 Gerando Vitrine Web a partir do histórico local...")
    hist = []
    if os.path.exists("historico_envios.json"):
        with open("historico_envios.json", "r", encoding="utf-8") as f:
            hist = json.load(f)
    atualizar_vitrine_html(historico=hist)
