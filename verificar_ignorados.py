import os
import re
import json
import paramiko
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Caminho do arquivo de controle
ARQUIVO_ESTADO = "./logs/contador.json"

def carregar_memoria_processados():
    """Carrega a lista do JSON para a memória RAM."""
    if not os.path.exists(ARQUIVO_ESTADO):
        return set()
    try:
        with open(ARQUIVO_ESTADO, 'r', encoding='utf-8') as f:
            estado = json.load(f)
            return set(estado.get("arquivos_processados", []))
    except Exception:
        return set()

def inspecionar_origem():
    host = os.getenv("SRC_HOST")
    port = int(os.getenv("SRC_PORT"))
    user = os.getenv("SRC_USER")
    password = os.getenv("SRC_PASS")
    remote_dir = os.getenv("SRC_DIR")

    print(f"\n🔍 [AUDITORIA] Conectando ao servidor de ORIGEM ({host}:{port}) para inspecionar arquivos...")

    padrao_ja_renomeado = re.compile(r"^(\d+)_(\d+)_(\d+)_(.+)$")
    padrao_bruto_valido = re.compile(r"^(\d+)_(\d+)_([^_]+)$")

    arquivos_ja_processados = carregar_memoria_processados()

    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        arquivos_no_servidor = sftp.listdir(remote_dir)

        if not arquivos_no_servidor:
            print("⚠️ A pasta remota da origem está vazia.")
        else:
            print(f"📦 Total de arquivos encontrados na Origem: {len(arquivos_no_servidor)}\n")
            print("=" * 80)
            print(f"{'ARQUIVO':<45} | {'STATUS / MOTIVO'}")
            print("=" * 80)

            contadores = {
                "renomeado": 0,
                "antigo": 0,
                "historico": 0,
                "pendentes": 0
            }

            for nome_arquivo in sorted(arquivos_no_servidor):
                if padrao_ja_renomeado.match(nome_arquivo):
                    status = "⏩ Ignorado (Já renomeado na origem)"
                    contadores["renomeado"] += 1
                elif not padrao_bruto_valido.match(nome_arquivo):
                    status = "⏩ Ignorado (Nomenclatura antiga)"
                    contadores["antigo"] += 1
                elif nome_arquivo in arquivos_ja_processados:
                    status = "⏩ Ignorado (Já registrado no historico.json)"
                    contadores["historico"] += 1
                else:
                    status = "📥 PENDENTE (Seria baixado pelo script principal)"
                    contadores["pendentes"] += 1

                print(f"{nome_arquivo:<45} | {status}")

            print("=" * 80)
            print("\n📊 RESUMO DA INSPEÇÃO:")
            print(f"   • Total de arquivos na origem : {len(arquivos_no_servidor)}")
            print(f"   • Já renomeados na origem    : {contadores['renomeado']}")
            print(f"   • Com nomenclatura antiga    : {contadores['antigo']}")
            print(f"   • Já processados (Histórico) : {contadores['historico']}")
            print(f"   • Novos / Pendentes de envio : {contadores['pendentes']}")
            print("=" * 80)

        sftp.close()
        transport.close()

    except Exception as e:
        print(f"❌ [ERRO na Auditoria]: {e}")

if __name__ == "__main__":
    inspecionar_origem()    