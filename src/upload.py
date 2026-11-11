import paramiko
import os
import re
from dotenv import load_dotenv
from state_manager import PASTA_TEMP

load_dotenv()

def fase3_upload_e_limpeza():
    """Envia os arquivos para o destino (.tmp -> rename) e limpa a pasta temp local."""
    host_dest = os.getenv("DEST_HOST")
    port_dest = int(os.getenv("DEST_PORT"))
    user_dest = os.getenv("DEST_USER")
    pass_dest = os.getenv("DEST_PASS")
    dir_dest = os.getenv("DEST_DIR")

    arquivos_temp = os.listdir(PASTA_TEMP)
    if not arquivos_temp:
        print("\n[FASE 3] Nenhum arquivo pendente em temp/ para enviar.")
        return

    print(f"\n[FASE 3] Conectando ao servidor de DESTINO ({host_dest}:{port_dest}) para upload...")

    try:
        trans_dest = paramiko.Transport((host_dest, port_dest))
        trans_dest.connect(username=user_dest, password=pass_dest)
        sftp_dest = paramiko.SFTPClient.from_transport(trans_dest)

        padrao_renomeado = re.compile(r"^\d+_\d+_\d+_.+$")

        for nome_arquivo in arquivos_temp:
            caminho_local = os.path.join(PASTA_TEMP, nome_arquivo)
            
            if os.path.isfile(caminho_local) and padrao_renomeado.match(nome_arquivo):
                path_remoto_tmp = f"{dir_dest}/{nome_arquivo}.tmp"
                path_remoto_final = f"{dir_dest}/{nome_arquivo}"

                print(f"⬆Enviando: {nome_arquivo} (como .tmp)...")
                sftp_dest.put(caminho_local, path_remoto_tmp)

                try:
                    sftp_dest.remove(path_remoto_final)
                except IOError:
                    pass

                sftp_dest.rename(path_remoto_tmp, path_remoto_final)
                print(f"Upload concluído: {nome_arquivo}")

                os.remove(caminho_local)

        sftp_dest.close()
        trans_dest.close()

        print("\nPIPELINE EXECUTADO COM SUCESSO TOTAL!")

    except Exception as e:
        print(f"[ERRO na Fase 3]: {e}")