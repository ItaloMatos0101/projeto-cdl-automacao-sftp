import paramiko
import os
from dotenv import load_dotenv
from state_manager import PASTA_TEMP, arquivo_ja_processado

load_dotenv()

def fase1_download():
    """Conecta na origem e baixa todos os arquivos que ainda NÃO foram processados (sem filtro por data)."""
    host = os.getenv("SRC_HOST")
    port = int(os.getenv("SRC_PORT"))
    user = os.getenv("SRC_USER")
    password = os.getenv("SRC_PASS")
    remote_dir = os.getenv("SRC_DIR")
    
    print(f"\n[FASE 1] Conectando ao servidor de ORIGEM ({host}:{port})...")
    
    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        arquivos_no_servidor = sftp.listdir(remote_dir)
        
        if not arquivos_no_servidor:
            print("A pasta remota da origem está vazia.")
        else:
            print(f"Analisando {len(arquivos_no_servidor)} arquivo(s) na Origem...")
            baixados_contador = 0
            
            for nome_arquivo in arquivos_no_servidor:
                # Regra de Pulo: Ignora se o arquivo já estiver registrado no contador.json
                if arquivo_ja_processado(nome_arquivo):
                    print(f"Ignorado (Já processado anteriormente): {nome_arquivo}")
                    continue
                
                remote_path = f"{remote_dir}/{nome_arquivo}"
                local_path = os.path.join(PASTA_TEMP, nome_arquivo)
                
                sftp.get(remote_path, local_path)
                print(f"⬇Baixado arquivo pendente: {nome_arquivo}")
                baixados_contador += 1
                
            print(f"Total de novos arquivos baixados: {baixados_contador}")
                
        sftp.close()
        transport.close()
        return True
        
    except Exception as e:
        print(f"[ERRO na Fase 1]: {e}")
        return False