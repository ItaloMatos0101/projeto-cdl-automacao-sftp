import os
import re
import json
from ftplib import FTP
from dotenv import load_dotenv

load_dotenv()

ARQUIVO_ESTADO = "./logs/historico.json"

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
    host = os.getenv("EQUA_HOST")
    port = int(os.getenv("EQUA_PORT", "21"))
    user = os.getenv("EQUA_USER")
    password = os.getenv("EQUA_PASS")
    remote_dir = os.getenv("EQUA-MA_DIR")

    print(f"\n🔍 [AUDITORIA] Conectando ao servidor de ORIGEM via FTP ({host}:{port}) para inspecionar arquivos...")

    padrao_ja_renomeado = re.compile(r"^(\d+)_(\d+)_(\d+)_(.+)$")
    padrao_bruto_valido = re.compile(r"^(\d+)_(\d+)_([^_]+)$")

    arquivos_ja_processados = carregar_memoria_processados()

    try:
        ftp = FTP()
        ftp.connect(host, port, timeout=30)
        ftp.login(user=user, passwd=password)
        ftp.set_pasv(False)  # Mantém o mesmo modo ativo configurado no download.py
        ftp.cwd(remote_dir)

        arquivos_no_servidor = [
            os.path.basename(item)
            for item in ftp.nlst()
            if os.path.basename(item) not in (".", "..")
        ]

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

        try:
            ftp.quit()
        except Exception:
            ftp.close()

    except Exception as e:
        print(f"❌ [ERRO na Auditoria]: {e}")

if __name__ == "__main__":
    inspecionar_origem()