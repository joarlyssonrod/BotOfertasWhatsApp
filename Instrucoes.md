
---

### 1. Atalho de "Um Clique" para enviar as ofertas (Resolvido! 🛠️)
Acabei de criar um arquivo chamado [Enviar Ofertas.bat](file:///e:/Apps/BotWhatsapp/Enviar%20Ofertas.bat) dentro da pasta do seu projeto. 
* **O que ele faz:** É um script do Windows. Sempre que você der um **duplo clique** nele, ele abrirá o terminal, ativará o suporte a emojis do Windows, verificará e instalará todas as dependências caso necessário, e rodará o bot de ofertas completo de forma automática.
* **Dica:** Você pode simplesmente copiar ou criar um atalho desse arquivo para a sua **Área de Trabalho (Desktop)**. Assim, sempre que quiser enviar ofertas, basta dar dois cliques no ícone na sua área de trabalho!

---

### 2. Como enviar as ofertas de forma 100% automática?
Para fazer o bot rodar sozinho sem você precisar clicar em nada, a melhor forma no Windows é usar o **Agendador de Tarefas** nativo:

1. Clique no menu Iniciar do Windows, pesquise por **Agendador de Tarefas** (Task Scheduler) e abra-o.
2. No menu lateral direito, clique em **Criar Tarefa Básica...**
3. Dê um nome para a tarefa (ex: `Bot de Ofertas WhatsApp`) e clique em Avançar.
4. Escolha a frequência (ex: **Diariamente**).
5. Defina o horário de início e, em seguida, configure para repetir a tarefa a cada **2 horas** (ou o tempo de intervalo que você desejar).
6. Na tela de Ação, selecione **Iniciar um programa**.
7. No campo *Programa/script*, clique em Procurar e selecione o arquivo **`Enviar Ofertas.bat`** (que criamos na pasta do projeto).
8. Clique em Concluir.

Pronto! O próprio Windows vai rodar o bot de tempos em tempos de forma silenciosa e automática.

---

### 3. Como acessar de outro computador?
Se você precisar rodar o bot a partir de outro computador (como o de casa), o processo é muito mais simples agora:

1. **Copiar os arquivos:** Envie a pasta do projeto para o outro computador (via Google Drive, Pendrive, etc.).
   *(Lembrete: não precisa copiar a pasta `wpp_perfil` nem o arquivo `sessao_ml.json` para evitar conflitos de caminhos).*
2. **Instalar o Python:** Instale o Python (versão 3.10 ou superior) no novo computador. Certifique-se de marcar a opção **"Add Python to PATH"** durante a instalação.
3. **Executar o instalador automático:** Basta dar um duplo clique em [Enviar Ofertas.bat](file:///e:/Apps/BotWhatsapp/Enviar%20Ofertas.bat). Ele detectará que as bibliotecas estão faltando e instalará tudo automaticamente (incluindo o navegador do Playwright)!
4. **Escanear o login uma única vez no novo PC:** Execute os scripts `python salvar_login_whatsapp.py` e `python salvar_login.py` no terminal do novo computador para gerar as sessões válidas para aquela máquina.
5. **Pronto!** A partir daí, o bot e o agendamento funcionarão normalmente.

---

### 4. Como funciona a unificação de grupos?
Por padrão, o bot agora vem configurado para enviar todas as ofertas para um único grupo unificado.
* Para alterar as configurações do grupo, abra o arquivo [motor_integrado.py](file:///e:/Apps/BotWhatsapp/motor_integrado.py) e localize as seguintes linhas:
  ```python
  # Configuração de envio do WhatsApp:
  UNIFICAR_GRUPOS = True  # Mude para False se quiser voltar a separar por categoria
  GRUPO_UNICO_NOME = "Ofertas - Geral"  # Altere para o nome exato do seu grupo no WhatsApp
  ```

*(Nota: Caso você decida no futuro que o bot deve rodar 24 horas por dia sem depender do seu computador de trabalho ou de casa estar ligado, você pode alugar um servidor em nuvem baratinho (VPS Windows) por cerca de R$ 25 a R$ 30 por mês e deixar o bot rodando lá de forma ininterrupta!).*