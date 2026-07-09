import sys
import re

# Configura o stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

# Dicionário de mapeamento de categorias e suas respectivas palavras-chave
MAPEAMENTO_CATEGORIAS = {
    "Ofertas - Informática": [
        "notebook", "notebooks", "laptop", "laptops", "macbook", "macbooks", 
        "computador", "computadores", "desktop", "desktops", "processador", "processadores",
        "memoria ram", "memória ram", "ssd", "ssds", "teclado", "teclados", "mouse", "mouses", 
        "mousepad", "mousepads", "monitor", "monitores", 
        "placa de video", "placa de vídeo", "placas de vídeo", "placas de video", 
        "pc", "pcs", "roteador", "roteadores", "impressora", "impressoras", 
        "filtro de linha", "filtros de linha", "pendrive", "pendrives", 
        "hd externo", "hds externos", "intel", "amd", "ryzen", "core i",
        "placa mãe", "placa-mãe", "placa mae", "placas mãe", "placas-mãe", 
        "lga1700", "am4", "lga", "fonte 80 plus", "fonte atx", "fontes 80 plus",
        "water cooler", "watercooler", "water coolers", "watercoolers",
        "air cooler", "air coolers", "fan argb", "fans argb", "cooler rgb", "coolers rgb", 
        "gabinete", "gabinetes", "tablet", "tablets",
        "cadeira ergonômica", "cadeira ergonomica", "cadeiras ergonômicas", "cadeiras ergonomicas",
        "cadeira de escritório", "cadeira de escritorio", "cadeiras de escritório", "cadeiras de escritorio",
        "cadeira presidente", "cadeiras presidente",
        "mesa para pc", "mesas para pc", "suporte para notebook", "suporte para monitor", 
        "usb-c", "power bank", "carregador portátil", "carregador portatil"
    ],
    "Ofertas - Games": [
        "ps5", "playstation", "playstations", "xbox", "xboxes", "nintendo", 
        "console", "consoles", "game", "games", "gamer", "gamers", 
        "jogo", "jogos", "controle sem fio", "controles sem fio", 
        "headset gamer", "headsets gamer", "cadeira gamer", "cadeiras gamer", 
        "geforce", "rtx", "gta", "fifa", "dualshock", "dualsense", 
        "switch oled", "switch lite"
    ],
    "Ofertas - Moda": [
        "camiseta", "camisetas", "tênis", "tenis", "calça", "calças", "vestido", "vestidos", 
        "moletom", "moletons", "jaqueta", "jaquetas", "sapato", "sapatos", 
        "bolsa", "bolsas", "relógio", "relógios", "relogio", "relogios", 
        "meia", "meias", "cueca", "cuecas", "boné", "bonés", "bone", "bones",
        "camisa", "camisas", "blusa", "blusas", "short", "shorts", "bermuda", "bermudas", 
        "mochila", "mochilas", "chinelo", "chinelos", "sandália", "sandálias", 
        "sandalia", "sandalias", "bota", "botas", "carteira", "carteiras", 
        "cinto", "cintos", "copo térmico", "copo termico", "copos térmicos", "copos termicos"
    ],
    "Ofertas - Fitness": [
        "whey", "creatina", "suplemento", "suplementos", "haltere", "halteres", 
        "dumbbell", "esteira", "esteiras", "bicicleta ergometrica", "bicicleta ergométrica", 
        "bicicletas ergométricas", "bicicletas ergometricas", "treino", "treinos", 
        "academia", "academias", "albumina", "hipercalorico", "hipercalórico", 
        "bcaa", "termogenico", "termogênico", "coqueteleira", "coqueteleiras", 
        "colchonete", "colchonetes", "caneleira", "caneleiras",
        "pré treino", "pré-treino", "pre-treino", "pre treino", "beta alanina",
        "multivitamínico", "multivitaminico", "magnésio", "magnesio", "complexo b",
        "garrafa academia", "roupa de academia"
    ]
}

def categorizar_produto(titulo):
    """
    Classifica um produto com base em palavras-chave no seu título.
    Se nenhuma categoria for encontrada, retorna 'Ofertas - Geral'.
    """
    titulo_limpo = titulo.lower()
    
    # Lista de exclusões para a palavra "jogo" na categoria Games
    exclusoes_games = [
        "jogo de panelas", "jogo de cama", "jogo de lençol", 
        "jogo de copos", "jogo de banho", "jogo de toalhas", "jogo de jantar", 
        "jogo de chaves", "jogo de ferramentas", "jogo de brocas", "jogo de pratos", 
        "jogo de xícaras", "jogo americano"
    ]
    
    # Percorre cada categoria e suas palavras-chave
    for grupo, palavras_chave in MAPEAMENTO_CATEGORIAS.items():
        for kw in palavras_chave:
            # Se for a palavra "jogo", verifica exclusões primeiro
            if kw == "jogo" or kw == "jogos":
                tem_exclusao = False
                for exc in exclusoes_games:
                    if exc in titulo_limpo:
                        tem_exclusao = True
                        break
                if tem_exclusao:
                    continue
                    
            # Usa \b para corresponder apenas a palavras completas (evita correspondência parcial ex: sabonete -> bone)
            padrao = rf"\b{re.escape(kw.lower())}\b"
            if re.search(padrao, titulo_limpo):
                return grupo
                
    # Categoria padrão se não bater com nenhuma
    return "Ofertas - Geral"

if __name__ == "__main__":
    # Testes rápidos de categorização
    testes = [
        "Notebook Samsung Galaxy Book4 Intel Core i5 8GB 512GB SSD",
        "Console PlayStation 5 Slim 1TB + Jogo Returnal",
        "Tênis Nike Revolution 6 Next Nature Masculino",
        "100% Pure Whey Protein 900g Probiótica - Baunilha",
        "Cafeteira Elétrica Mondial Pratic 20 Xícaras",
        "Jogo de panelas Tramontina Turim 7 Peças",
        "Sabonete Líquido Facial Neutrogena Purifying Boost",
        "Relógio Inteligente Smartwatch Xiaomi Redmi Watch 3 Active"
    ]
    
    print("🧪 Testando categorizador:")
    for t in testes:
        cat = categorizar_produto(t)
        print(f"📦 Produto: {t[:40]}... -> Categoria: {cat}")
