# Automação de Pipeline SFTP (Intermediado)

## 📌 Sobre o Projeto
Este projeto tem como objetivo automatizar a transferência de arquivos entre dois servidores (Origem e Destino) via protocolo seguro SFTP. O pipeline realiza a intermediação local para baixar, processar/renomear os arquivos e enviá-los ao servidor de destino de forma atômica (substituindo o processo manual feito via WinSCP).

Atualmente, o projeto conta com uma infraestrutura de **Laboratório de Testes** conteinerizada via Docker, permitindo a simulação segura dos servidores remotos durante o desenvolvimento.

## 🚀 Tecnologias Utilizadas
* **Python 3.11+**: Linguagem principal da automação.
* **Paramiko**: Biblioteca nativa para conexões SSHv2 e túneis SFTP.
* **Python-dotenv**: Gerenciamento seguro de variáveis de ambiente.
* **Docker & Docker Compose**: Laboratório local simulando os servidores remotos.

---

## 📁 Estrutura do Projeto

```text
sftp-pipeline/
├── docker/
│   └── docker-compose.yml       # Ambiente local com 2 servidores SFTP
├── src/
│   └── main.py                  # Orquestrador do fluxo e testes de conexão
├── temp/                        # Diretório local temporário para processamento
├── logs/                        # Arquivos de log de execução
├── .env                         # Credenciais de ambiente (NÃO VERSIONAR)
├── .env.example                 # Modelo das variáveis de ambiente
├── .gitignore                   # Arquivos ignorados pelo repositório
└── requirements.txt             # Dependências Python do projeto
````

## 🛠️ Instalação e Configuração


**1. Clone o repositório ou navegue até a pasta do projeto:**

```Bash
cd projeto-cdl-automacao-sftp
````

**2. Crie e ative o Ambiente Virtual Python:**

```Bash
python -m venv venv

# Ativação no Windows (CMD/PowerShell)
venv\Scripts\activate

# Ativação no Linux/WSL
source venv/bin/activate
````

**3. Instale as dependências:**

```Bash
pip install -r requirements.txt

(Caso o arquivo requirements.txt ainda não possua as dependências, utilize pip install paramiko python-dotenv)
````

**4. Configure as Variáveis de Ambiente:**

Crie um arquivo chamado .env na raiz do projeto. Ele não será rastreado pelo Git por questões de segurança. Utilize o modelo abaixo, que reflete as configurações do laboratório Docker:

```Snippet de código

SRC_HOST=localhost
SRC_PORT=2221
SRC_USER=user_src
SRC_PASS=pass_src
SRC_DIR=/upload

DEST_HOST=localhost
DEST_PORT=2222
DEST_USER=user_dest
DEST_PASS=pass_dest
DEST_DIR=/incoming
````

## 🧪 Laboratório de Testes (Docker)

Para evitar testes diretos em servidores de produção, o projeto inclui um ambiente conteinerizado. Ele inicia duas instâncias do atmoz/sftp simulando as máquinas Origem e Destino.

Para iniciar os servidores de teste:

```Bash
cd docker
docker compose up -d
cd ..

    Servidor Origem: Responderá localmente na porta 2221.

    Servidor Destino: Responderá localmente na porta 2222.

````
Para parar e remover os servidores de teste:

```Bash
cd docker
docker compose down
````

## 🏃 Como Executar (Testes de Conexão)

Com o laboratório Docker em execução e o ambiente virtual (venv) ativado, teste a comunicação entre o script Python e os servidores utilizando o comando abaixo:

```Bash
python src\main.py
````
Saída Esperada:

```Plaintext
Testando conexões...
[OK] Conectado com sucesso no servidor: ORIGEM
[OK] Conectado com sucesso no servidor: DESTINO
````

Nota: Este projeto está em desenvolvimento ativo. As lógicas de download, expressão regular para renomeação e upload atômico serão integradas nas próximas versões.