import os
import re
import json
import paramiko
from dotenv import load_dotenv
from state_manager import PASTA_TEMP, ARQUIVO_ESTADO

load_dotenv()

def carregar_memoria_processados():
    """Carrega a lista do JSON para a memória RAM usando 'set' para buscas instantâneas."""
    if not os.path.exists(ARQUIVO_ESTADO):
        return set()
    try:
        with open(ARQUIVO_ESTADO, 'r', encoding='utf-8') as f:
            estado = json.load(f)
            # O 'set' (conjunto) faz buscas em O(1), sendo milhares de vezes mais rápido que uma lista normal
            return set(estado.get("arquivos_processados", []))
    except Exception:
        return set()

def fase1_download():
    """Conecta na origem, filtra na RAM e baixa apenas arquivos brutos inéditos de forma silenciosa."""
    host = os.getenv("SRC_HOST")
    port = int(os.getenv("SRC_PORT"))
    user = os.getenv("SRC_USER")
    password = os.getenv("SRC_PASS")
    remote_dir = os.getenv("SRC_DIR")

    print(f"\n[FASE 1] Conectando ao servidor de ORIGEM ({host}:{port})...")

    padrao_ja_renomeado = re.compile(r"^(\d+)_(\d+)_(\d+)_(.+)$")
    padrao_bruto_valido = re.compile(r"^(\d+)_(\d+)_([^_]+)$")

    # Carrega a memória apenas UMA VEZ antes do loop
    arquivos_ja_processados = carregar_memoria_processados()

    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        arquivos_no_servidor = sftp.listdir(remote_dir)

        if not arquivos_no_servidor:
            print("⚠️ A pasta remota da origem está vazia.")
        else:
            print(f"📦 Analisando {len(arquivos_no_servidor)} arquivo(s) na Origem...")

            # Contadores para o sumário silencioso
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

                # Busca instantânea na RAM, sem ler o disco rígido
                if nome_arquivo in arquivos_ja_processados:
                    ign_historico += 1
                    continue

                # Se é novo, faz o download e avisa na tela
                remote_path = f"{remote_dir}/{nome_arquivo}"
                local_path = os.path.join(PASTA_TEMP, nome_arquivo)

                sftp.get(remote_path, local_path)
                print(f"⬇️ Baixado NOVO arquivo: {nome_arquivo}")
                baixados += 1

            # Sumário final limpo no terminal
            ignorados_total = ign_renomeado + ign_antigo + ign_historico
            if ignorados_total > 0:
                print(f"🧹 Resumo da Origem: {ignorados_total} arquivo(s) ignorado(s) silenciosamente:")
                print(f"   ↳ {ign_historico} já registrados no histórico local.")
                print(f"   ↳ {ign_antigo} com nomenclatura antiga.")
                print(f"   ↳ {ign_renomeado} já renomeados na origem.")
            
            if baixados == 0:
                print("✅ Nenhum arquivo novo pendente de download.")

        sftp.close()
        transport.close()
        return True

    except Exception as e:
        print(f"❌ [ERRO na Fase 1]: {e}")
        return False