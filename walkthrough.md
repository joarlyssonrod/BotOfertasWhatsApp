# Resolução do Erro no Envio de Imagens com Legenda e Novas Funcionalidades

Corrigimos com sucesso o bug onde as imagens das ofertas estavam sendo enviadas sem legenda ou gerando erros de timeout no WhatsApp Web, e implementamos todas as melhorias acordadas.

## Alterações Realizadas

### [whatsapp_sender.py](file:///E:/Apps/BotOfertasWhatsApp/whatsapp_sender.py)
Alteramos o fluxo de upload de arquivos para simular a interação real do usuário no WhatsApp Web:
- **Abertura do Menu de Anexo**: Clicamos de forma resiliente no botão de anexo (`+`) identificando-o pelo atributo `aria-label="Anexar"` ou classe `plus-rounded`.
- **Upload com Seletor de Arquivos Nativo**: Clicamos na opção **"Fotos e vídeos"** e capturamos o manipulador de arquivos nativo do navegador via `expect_file_chooser()`. Isso impede que o WhatsApp trate o arquivo como uma nova figurinha (sticker), ativando a interface correta de envio de mídia com legenda.
- **Seletor de Legenda**: Atualizamos o seletor da caixa de entrada da legenda para `div[data-testid="media-caption-input-container"]`.
- **Seletor de Envio**: Atualizamos o seletor do botão de enviar na tela de preview de mídia para `span[data-icon="wds-ic-send-filled"]`.

---

## Novas Funcionalidades e Correções de Sessão

### 1. Desvio de CAPTCHA via Cookies Portáteis (`gerar_sessao_cookies.py`)
Para evitar travamentos de CAPTCHA no login automatizado (uma proteção de bot do Mercado Livre), atualizamos o gerador de sessão:
- **Caminhos Relativos**: Alteramos `gerar_sessao_cookies.py` para usar `.env` e `sessao_ml.json` locais do projeto, tornando-o portátil para qualquer máquina.
- **Fluxo sem CAPTCHA**: O usuário copia os cookies de seu navegador pessoal logado e os insere no `.env` sob a chave `MERCADO_LIVRE_COOKIES`, rodando o gerador para criar a sessão silenciosamente.

### 2. Captura Automática de Cupons de Desconto
Adicionamos inteligência para capturar e divulgar cupons ativos:
- **Mercado Livre**: O script `garimpeiro.py` agora pesquisa por classes ou textos de cupons (`coupon`, `cupom`) e armazena o código/descrição.
- **Amazon**: Aprimoramos `amazon_scraper.py` para associar cupons extraídos via Regex da listagem e ofertas do dia.
- **Mensagem Formatada**: Atualizamos o gerador de mensagens em `motor_integrado.py` para exibir a tag `🏷️ Cupom ativo: CÓDIGO` de forma destacada se houver um cupom associado à oferta.

### 3. Integração com Promobit (`promobit_scraper.py`)
- **Nova Fonte de Ofertas**: Criamos o scraper `promobit_scraper.py` que puxa as melhores ofertas aprovadas do Promobit.
- **Resolução de Links**: O scraper navega silenciosamente (usando Playwright em segundo plano) para clicar no botão "Ir à loja" e seguir os redirecionamentos de afiliados até descobrir a URL final (Amazon, Mercado Livre, Magalu ou Shopee).
- **Integração no Motor**: Quando o bot roda no modo `OFERTAS_DO_DIA`, ele consulta as ofertas do Promobit, converte-as para seus links de afiliado e as posta no WhatsApp.

### 4. Verificador de "Ofertas Encerradas"
- **Histórico Estruturado**: Upgrade de `historico_envios.json` para salvar objetos JSON detalhados contendo ID, URL, título, preço de envio, data e estado de expiração.
- **Checagem Automática**: Antes de enviar novas ofertas, o bot varre as ofertas enviadas nas últimas 12 horas e abre uma nova página em segundo plano para verificar se o produto esgotou, pausou ou se o preço subiu mais de 5%.
- **Alerta de Encerramento**: Se a oferta expirou, o bot envia uma mensagem informando que a oferta encerrou ou que o preço mudou.

### 5. Histórico e Tag de "Menor Preço"
- **Comparação de Preços**: O bot pesquisa todo o histórico de envios para ver se já registrou aquele produto (por ID ou similaridade de título >= 60%).
- **Alerta Visual**: Se o preço atual for o menor já registrado no histórico, o bot insere no topo da mensagem: `📉 *MENOR PREÇO HISTÓRICO REGISTRADO!*`.

### 6. Execução Silenciosa e Agendador (`Enviar Ofertas.bat`)
- **Modo Headless**: Modificamos o arquivo `Enviar Ofertas.bat` para aceitar o argumento `--headless`. Se invocado como `Enviar Ofertas.bat --headless`, o bot roda de forma invisível em segundo plano (Playwright sem abrir telas) e encerra o script sem aguardar a tecla `pause`.
- **Agendamento no Windows**: Isso permite criar uma tarefa agendada no Windows para executar o script a cada 2 horas sem interferir no seu trabalho.

---

### 7. Resolução de Bloqueio de Sessão do Mercado Livre
- **Fallback Automático para Modo Visitante**: Modificamos [garimpeiro.py](file:///E:/Apps/BotOfertasWhatsApp/garimpeiro.py) para que, se a sessão em `sessao_ml.json` estiver expirada ou se o Mercado Livre exigir verificação (CAPTCHA), ele feche o contexto de cookies e tente novamente sem login (como visitante anônimo). Como as páginas de Ofertas do Dia e busca pública funcionam para visitantes, isso permite que o bot continue extraindo dados de forma estável.
- **Detecção de Bloqueio no Verificador**: Corrigimos `checar_pagina_produto` em [motor_integrado.py](file:///E:/Apps/BotOfertasWhatsApp/motor_integrado.py). Anteriormente, se a página do produto redirecionasse para verificação/CAPTCHA (devido a cookies de sessão expirados injetados no contexto do Playwright), a função interpretava erroneamente como "fora de estoque/anúncio pausado" e disparava falsos alertas de "OFERTA ENCERRADA" no WhatsApp. Agora, o bot reconhece o redirecionamento de verificação como `"bloqueio_verificacao"`.
- **Limpeza Dinâmica de Cookies e Re-checagem**: Se o verificador detectar `"bloqueio_verificacao"`, ele limpa os cookies do Mercado Livre do contexto compartilhado do WhatsApp Web (sem afetar a sessão do WhatsApp), abre uma nova aba limpa, e refaz a checagem como visitante.
- **Herança de Headless/Headful**: Propagamos o parâmetro `headless=headless_mode` de [motor_integrado.py](file:///E:/Apps/BotOfertasWhatsApp/motor_integrado.py) para [garimpeiro.py](file:///E:/Apps/BotOfertasWhatsApp/garimpeiro.py). Quando o bot é executado de forma manual e visível (sem o parâmetro `--headless`), ele roda a navegação do Mercado Livre também no modo visível utilizando o Chrome local e cabeçalhos avançados, o que naturalmente evita as barreiras de Captcha e verificação de robôs do Mercado Livre.

### 8. Resolução de Ofertas Duplicadas (Shopee & Magalu)
- **Extração de itemId na Shopee**: Atualizamos o [shopee_api.py](file:///E:/Apps/BotOfertasWhatsApp/shopee_api.py) para incluir a chave `"itemId"` nos itens retornados pela API (tanto no scraper de termos quanto de ofertas do dia).
- **Normalização de IDs no Motor**: Atualizamos `obter_id_unico` no [motor_integrado.py](file:///E:/Apps/BotOfertasWhatsApp/motor_integrado.py) para aceitar o dicionário do produto diretamente e, se for Shopee, utilizar o `itemId` real do banco de dados (ex: `SHOPEE_23927230198`).
- **Resolução de Links Curtos de Shopee**: Adicionamos um fallback no regex para capturar a hash única de links curtos do tipo `s.shopee.com.br/hash` (ex: `SHOPEE_8KnIkEqCxF`) caso o `itemId` não esteja disponível. Isso garante consistência mesmo que diferentes consultas retornem formatos distintos do mesmo link de afiliado.
- **Suporte Dinâmico para Magazine Voce**: Atualizamos o [bot_afiliado.py](file:///E:/Apps/BotOfertasWhatsApp/bot_afiliado.py) para reconhecer links que contêm `magazinevoce.com.br` e usar dinamicamente a propriedade `MAGALU_STORE_NAME` do `.env` (ex: `magazinejoarlysson`), evitando que links do divulgador passem em branco ou bypassassem a checagem de ID.

---

## Verificação e Resultados

1. **Testes de Comparação**: Criamos e executamos com sucesso `test_integracoes.py` que validou a normalização de dados e o match por similaridade de títulos.
2. **Testes do Verificador**: Criamos e executamos com sucesso `test_checking.py` que simulou checagens de preços em links reais, confirmando a detecção perfeita de ofertas expiradas (Mercado Livre) e ativas (Amazon).
3. **Resolução de Erro de Sessão**: Testamos a execução de `garimpeiro.py` com cookies inválidos. O bot identificou o bloqueio, ativou o fallback silencioso para visitante sem login, e executou o scraping com sucesso.
4. **Resolução de Duplicidades**: Criamos o script de testes `test_duplicate_detection.py` que valida a correta extração de IDs únicos de links e dicionários da Shopee, Amazon, Magalu, Mercado Livre e AliExpress. Todos os testes de duplicidade passaram com sucesso!
5. **Compilação**: Verificamos que todos os arquivos compilam e executam sem erros.
