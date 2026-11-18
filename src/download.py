import os
import re
import json
from ftplib import FTP
from dotenv import load_dotenv
from src.state_manager import PASTA_TEMP, ARQUIVO_ESTADO

load_dotenv()

def carregar_memoria_processados():
    """Carrega a lista do JSON para a memória RAM usando 'set' para buscas instantâneas."""
    if not os.path.exists(ARQUIVO_ESTADO):
        return set()
    try:
        with open(ARQUIVO_ESTADO, 'r', encoding='utf-8') as f:
            estado = json.load(f)
            return set(estado.get("arquivos_processados", []))
    except Exception:
        return set()

def fase1_download():
    """Conecta na origem via FTP, filtra na RAM e baixa apenas arquivos brutos inéditos."""
    host = os.getenv("EQUA_HOST")
    port = int(os.getenv("EQUA_PORT", "21"))
    user = os.getenv("EQUA_USER")
    password = os.getenv("EQUA_PASS")
    remote_dir = os.getenv("EQUA-MA_DIR")

    print(f"\n[FASE 1] Conectando ao servidor de ORIGEM ({host}:{port})...")

    padrao_ja_renomeado = re.compile(r"^(\d+)_(\d+)_(\d+)_(.+)$")
    padrao_bruto_valido = re.compile(r"^(\d+)_(\d+)_([^_]+)$")

    arquivos_ja_processados = carregar_memoria_processados()

    try:
        ftp = FTP()
        #ftp.set_debuglevel(2)  # Exibe cada comando e resposta do servidor no terminal
        ftp.connect(host, port, timeout=30)
        ftp.login(user=user, passwd=password)
        ftp.set_pasv(False)    # Força o Modo Ativo caso as portas passivas estejam bloqueadas
        ftp.cwd(remote_dir)

        arquivos_no_servidor = [
            os.path.basename(item)
            for item in ftp.nlst()
            if os.path.basename(item) not in (".", "..")
        ]

        if not arquivos_no_servidor:
            print("⚠️ A pasta remota da origem está vazia.")
        else:
            print(f"📦 Analisando {len(arquivos_no_servidor)} arquivo(s) na Origem...")

            ign_renomeado = 0
            ign_antigo = 0
            ign_historico = 0
            baixados = 0

            for nome_arquivo in arquivos_no_servidor:
                if padrao_ja_renomeado.match(nome_arquivo):
                    ign_renomeado += 1
                    continue

                if not padrao_bruto_valido.match(nome_arquivo):
                    ign_antigo += 1
                    continue

                if nome_arquivo in arquivos_ja_processados:
                    ign_historico += 1
                    continue

                local_path = os.path.join(PASTA_TEMP, nome_arquivo)

                with open(local_path, "wb") as arquivo_local:
                    ftp.retrbinary(f"RETR {nome_arquivo}", arquivo_local.write)

                print(f"⬇️ Baixado NOVO arquivo: {nome_arquivo}")
                baixados += 1

            ignorados_total = ign_renomeado + ign_antigo + ign_historico
            if ignorados_total > 0:
                print(f"🧹 Resumo da Origem: {ignorados_total} arquivo(s) ignorado(s) silenciosamente:")
                print(f"   ↳ {ign_historico} já registrados no histórico local.")
                print(f"   ↳ {ign_antigo} com nomenclatura antiga.")
                print(f"   ↳ {ign_renomeado} já renomeados na origem.")

            if baixados == 0:
                print("✅ Nenhum arquivo novo pendente de download.")

        try:
            ftp.quit()
        except Exception:
            ftp.close()

        return True

    except Exception as e:
        print(f"❌ [ERRO na Fase 1]: {e}")
        return False