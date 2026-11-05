import paramiko # Importa o módulo responsável pela conexão de rede SSH/SFTP
import os # Importa o módulo do sistema operacional (necessário para ler as variáveis de ambiente)
from dotenv import load_dotenv # Importa a função específica que injeta o .env no sistema

# Carrega as variáveis do arquivo .env
load_dotenv() # Procura o arquivo .env na mesma pasta e carrega as credenciais para a memória

def test_connection(host, port, user, password, name):
    # Verificação de segurança (Fail-fast):
    # Se alguma variável não for encontrada no .env, ela assume o valor "None". 
    # A linha abaixo impede que o código continue e gere um erro fatal, alertando você antes.
    if None in (host, port, user, password):
         print(f"[ERRO] Falha ao conectar... As credenciais não foram encontradas!")
         return

    try:
        # paramiko.Transport cria o túnel TCP cru (raw socket) até o IP e a porta especificados.
        # Ele precisa que a porta seja um número inteiro, por isso usamos int(port).
        transport = paramiko.Transport((host, int(port)))
        
        # Realiza o handshake (aperto de mão) e a autenticação SSH com as credenciais.
        transport.connect(username=user, password=password)
        
        # O SFTP é um subsistema do SSH. Esta linha abre o canal SFTP por dentro do túnel já autenticado.
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        print(f"[OK] Conectado com sucesso no servidor: {name}")
        
        # Encerra o subsistema SFTP para liberar recursos de rede.
        sftp.close()
        
        # Fecha o túnel TCP principal (Boa prática de infraestrutura de redes).
        transport.close()
        
    except Exception as e: # Caso ocorra queda de rede, senha errada ou timeout, captura a falha sem derrubar o script inteiro.
        print(f"[ERRO] Falha ao conectar no servidor {name}: {e}")

if __name__ == "__main__":
    # Garante que as conexões só sejam feitas se este script for o arquivo principal sendo executado.
    print("Testando conexões...")
    
    # Executa a função passando os valores da ORIGEM lidos da memória do sistema (injetados pelo load_dotenv)
    test_connection(os.getenv("SRC_HOST"), os.getenv("SRC_PORT"), os.getenv("SRC_USER"), os.getenv("SRC_PASS"), "ORIGEM")
    
    # Executa a mesma função usando o reaproveitamento de código, agora para o DESTINO
    test_connection(os.getenv("DEST_HOST"), os.getenv("DEST_PORT"), os.getenv("DEST_USER"), os.getenv("DEST_PASS"), "DESTINO")