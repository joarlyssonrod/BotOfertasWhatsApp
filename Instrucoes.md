
---

### 1. Atalho de "Um Clique" para enviar as ofertas (Resolvido! 🛠️)
Acabei de criar um arquivo chamado [Enviar Ofertas.bat](file:///E:/Apps/BotOfertasWhatsApp/Enviar%20Ofertas.bat) dentro da pasta do seu projeto. 
* **O que ele faz:** É um script do Windows. Sempre que você der um **duplo clique** nele, ele abrirá o terminal, ativará o suporte a emojis do Windows, verificará e instalará todas as dependências caso necessário, e rodará o bot de ofertas completo de forma automática.
* **Dica:** Você pode simplesmente copiar ou criar um atalho desse arquivo para a sua **Área de Trabalho (Desktop)**. Assim, sempre que quiser enviar ofertas, basta dar dois cliques no ícone na sua área de trabalho!

---

### 2. Como enviar as ofertas de forma 100% automática? (Modo Silencioso / Background)
Para fazer o bot rodar sozinho sem você precisar clicar em nada e sem abrir nenhuma janela na sua frente enquanto você trabalha:

1. Clique no menu Iniciar do Windows, pesquise por **Agendador de Tarefas** (Task Scheduler) e abra-o.
2. No menu lateral direito, clique em **Criar Tarefa Básica...**
3. Dê um nome para a tarefa (ex: `Bot de Ofertas WhatsApp`) e clique em Avançar.
4. Escolha a frequência (ex: **Diariamente**).
5. Defina o horário de início e, em seguida, configure para repetir a tarefa a cada **2 horas** ou **3 horas** (ou o tempo de intervalo que você desejar).
6. Na tela de Ação, selecione **Iniciar um programa**.
7. No campo *Programa/script*, clique em Procurar e selecione o arquivo **`Enviar Ofertas.bat`** (localizado em `E:\Apps\BotOfertasWhatsApp\Enviar Ofertas.bat`).
8. No campo **Adicionar argumentos (opcional)**, digite exatamente: `--headless`
   *(Isso fará o bot rodar de forma invisível em segundo plano sem incomodar você!).*
9. No campo **Iniciar em (opcional)**, digite o diretório do projeto: `E:\Apps\BotOfertasWhatsApp`
10. Clique em Concluir.

---

### 3. Como configurar no Computador do Trabalho? (Segundo PC)
Como o computador do seu trabalho já executa o bat agendado a cada 3 horas, você precisa apenas atualizar os arquivos e fazer o login de sessão lá. Siga estes passos:

1. **Baixar as atualizações do GitHub:**
   No computador do trabalho, abra o terminal na pasta do projeto e rode:
   ```bash
   git pull
   ```
2. **Atualizar o Agendamento de Tarefas:**
   Edite a tarefa que já está configurada no Agendador de Tarefas do trabalho para:
   * Adicionar o argumento `--headless` na ação da tarefa (conforme passo 8 do item anterior).
   * Definir a pasta de início em "Iniciar em (opcional)" como `E:\Apps\BotOfertasWhatsApp`.
3. **Escanear o WhatsApp uma única vez:**
   No terminal da pasta do projeto no trabalho, execute:
   ```bash
   python salvar_login_whatsapp.py
   ```
   Isso abrirá uma janela do navegador. Escaneie o QR Code com o celular do grupo de ofertas e feche a janela do navegador após carregar as conversas. O login ficará salvo permanentemente no arquivo de sessão.
4. **Gerar cookies do Mercado Livre:**
   Se pedir CAPTCHA ou login no Mercado Livre no PC do trabalho:
   * Abra o Chrome no seu perfil pessoal logado do Mercado Livre.
   * Pressione `F12`, vá na aba **Console**, cole o código para extrair cookies (conforme instruções de `gerar_sessao_cookies.py`), copie o resultado.
   * No PC do trabalho, cole esse resultado no arquivo `.env` na variável `MERCADO_LIVRE_COOKIES`.
   * Rode: `python gerar_sessao_cookies.py` para gerar a sessão sem precisar passar pelo CAPTCHA.

---

### 4. Como funciona a unificação de grupos?
Por padrão, o bot agora vem configurado para enviar todas as ofertas para um único grupo unificado.
* Para alterar as configurações do grupo, abra o arquivo [motor_integrado.py](file:///E:/Apps/BotOfertasWhatsApp/motor_integrado.py) e localize as seguintes linhas:
  ```python
  # Configuração de envio do WhatsApp:
  UNIFICAR_GRUPOS = True  # Mude para False se quiser voltar a separar por categoria
  GRUPO_UNICO_NOME = "Ofertas - Geral"  # Altere para o nome exato do seu grupo no WhatsApp
  ```

*(Nota: Caso você decida no futuro que o bot deve rodar 24 horas por dia sem depender do seu computador de trabalho ou de casa estar ligado, você pode alugar um servidor em nuvem baratinho (VPS Windows) por cerca de R$ 25 a R$ 30 por mês e deixar o bot rodando lá de forma ininterrupta!).*