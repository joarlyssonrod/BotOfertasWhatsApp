import sys

# Configura o stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

# Dicionário de mapeamento de categorias e suas respectivas palavras-chave
MAPEAMENTO_CATEGORIAS = {
    "Ofertas - Informática": [
        "notebook", "laptop", "macbook", "computador", "desktop", "processador", 
        "memoria ram", "memória ram", "ssd", "teclado", "mouse", "monitor", 
        "placa de video", "placa de vídeo", "pc", "roteador", "impressora", 
        "filtro de linha", "pendrive", "hd externo", "intel", "amd", "ryzen", "core i"
    ],
    "Ofertas - Games": [
        "ps5", "playstation", "xbox", "nintendo", "console", "game", "gamer", 
        "jogo", "controle sem fio", "headset gamer", "cadeira gamer", "geforce", 
        "rtx", "gta", "fifa", "dualshock", "dualsense"
    ],
    "Ofertas - Moda": [
        "camiseta", "tênis", "tenis", "calça", "vestido", "moletom", "jaqueta", 
        "sapato", "bolsa", "relógio", "relogio", "meia", "cueca", "boné", "bone",
        "camisa", "blusa", "short", "bermuda", "mochila"
    ],
    "Ofertas - Fitness": [
        "whey", "creatina", "suplemento", "haltere", "dumbbell", "esteira", 
        "bicicleta ergometrica", "bicicleta ergométrica", "treino", "academia", 
        "albumina", "hipercalorico", "hipercalórico", "bcaa", "termogenico", 
        "termogênico", "coqueteleira", "colchonete", "caneleira"
    ]
}

def categorizar_produto(titulo):
    """
    Classifica um produto com base em palavras-chave no seu título.
    Se nenhuma categoria for encontrada, retorna 'Ofertas - Geral'.
    """
    titulo_limpo = titulo.lower()
    
    # Percorre cada categoria e suas palavras-chave
    for grupo, palavras_chave in MAPEAMENTO_CATEGORIAS.items():
        for kw in palavras_chave:
            if kw in titulo_limpo:
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
    ]
    
    print("🧪 Testando categorizador:")
    for t in testes:
        cat = categorizar_produto(t)
        print(f"📦 Produto: {t[:40]}... -> Categoria: {cat}")
