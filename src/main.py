import paramiko
import os
import re
import json
import shutil
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração de Diretórios Locais
PASTA_TEMP = "./temp"
PASTA_PROCESSADOS = "./processados"
ARQUIVO_ESTADO = "./logs/contador.json"

def garantir_pastas_locais():
    """Garante que as pastas de trabalho existam."""
    os.makedirs(PASTA_TEMP, exist_ok=True)
    os.makedirs(PASTA_PROCESSADOS, exist_ok=True)
    os.makedirs("./logs", exist_ok=True)

def arquivo_ja_processado(cdl, filiada, hash_arquivo):
    """Verifica se o arquivo já consta na memória local para evitar re-downloads."""
    prefixo = f"{cdl}_{filiada}"
    if not os.path.exists(ARQUIVO_ESTADO):
        return False
    
    try:
        with open(ARQUIVO_ESTADO, 'r') as f:
            estado = json.load(f)
        if prefixo in estado and isinstance(estado[prefixo], dict):
            if hash_arquivo in estado[prefixo].get("historico_arquivos", {}):
                return True
    except Exception:
        pass
    return False

def obter_novo_sequencial(cdl, filiada, hash_arquivo):
    """Garante o sequencial correto e registra arquivos novos."""
    prefixo = f"{cdl}_{filiada}"
    
    if os.path.exists(ARQUIVO_ESTADO):
        with open(ARQUIVO_ESTADO, 'r') as f:
            estado = json.load(f)
    else:
        estado = {}
        
    if prefixo not in estado or not isinstance(estado[prefixo], dict):
        estado[prefixo] = {
            "ultimo_sequencial": -1,
            "historico_arquivos": {}
        }
        
    dados_parceira = estado[prefixo]

    if hash_arquivo in dados_parceira["historico_arquivos"]:
        numero_final = dados_parceira["historico_arquivos"][hash_arquivo]
    else:
        dados_parceira["ultimo_sequencial"] += 1
        numero_final = dados_parceira["ultimo_sequencial"]
        dados_parceira["historico_arquivos"][hash_arquivo] = numero_final
        
        with open(ARQUIVO_ESTADO, 'w') as f:
            json.dump(estado, f, indent=4)
            
    return f"{numero_final:04d}"

def fase1_download():
    """Conecta na origem e baixa apenas arquivos que NUNCA foram processados."""
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
            print("⚠️ A pasta remota da origem está vazia.")
        else:
            print(f"📦 Analisando {len(arquivos_no_servidor)} arquivo(s) na Origem...")
            padrao_original = re.compile(r"^(\d+)_(\d+)_(.+$)")
            
            for nome_arquivo in arquivos_no_servidor:
                match = padrao_original.match(nome_arquivo)
                
                # Regra de Pulo: Verifica se já processamos este arquivo
                if match:
                    cdl, filiada, hash_arquivo = match.groups()
                    if arquivo_ja_processado(cdl, filiada, hash_arquivo):
                        print(f"⏩ Ignorado (Já está na base de dados local): {nome_arquivo}")
                        continue
                
                # Download normal para novos arquivos
                remote_path = f"{remote_dir}/{nome_arquivo}"
                local_path = os.path.join(PASTA_TEMP, nome_arquivo)
                
                sftp.get(remote_path, local_path)
                print(f"⬇️ Baixado NOVO arquivo: {nome_arquivo}")
                
        sftp.close()
        transport.close()
        return True
        
    except Exception as e:
        print(f"❌ [ERRO na Fase 1]: {e}")
        return False

def fase2_renomear():
    """Aplica o sequencial aos arquivos recém baixados e salva backup local."""
    arquivos = os.listdir(PASTA_TEMP)
    if not arquivos:
        return

    print(f"\n[FASE 2] Iniciando renomeação e backup local de {len(arquivos)} arquivo(s)...")
    
    padrao_ja_renomeado = re.compile(r"^\d+_\d+_\d{4}_.+$")
    padrao_original = re.compile(r"^(\d+)_(\d+)_(.+$)")
    
    for nome_original in arquivos:
        caminho_antigo = os.path.join(PASTA_TEMP, nome_original)
        
        if not os.path.isfile(caminho_antigo) or padrao_ja_renomeado.match(nome_original):
            continue
            
        match = padrao_original.match(nome_original)
        
        if match:
            cdl, filiada, hash_arquivo = match.groups()
            
            sequencial = obter_novo_sequencial(cdl, filiada, hash_arquivo)
            novo_nome = f"{cdl}_{filiada}_{sequencial}_{hash_arquivo}"
            caminho_novo = os.path.join(PASTA_TEMP, novo_nome)
            
            os.replace(caminho_antigo, caminho_novo)
            print(f"✅ Renomeado: {nome_original} ➔ {novo_nome}")
            
            caminho_backup = os.path.join(PASTA_PROCESSADOS, novo_nome)
            shutil.copy2(caminho_novo, caminho_backup)
            
        else:
            print(f"⚠️ Padrão desconhecido: {nome_original}")

def fase3_upload_e_limpeza():
    """Envia os arquivos usando sobrescrita segura e limpa a pasta local temp."""
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

        padrao_renomeado = re.compile(r"^\d+_\d+_\d{4}_.+$")

        for nome_arquivo in arquivos_temp:
            caminho_local = os.path.join(PASTA_TEMP, nome_arquivo)
            
            if os.path.isfile(caminho_local) and padrao_renomeado.match(nome_arquivo):
                path_remoto_tmp = f"{dir_dest}/{nome_arquivo}.tmp"
                path_remoto_final = f"{dir_dest}/{nome_arquivo}"

                print(f"⬆️ Enviando: {nome_arquivo} (como .tmp)...")
                sftp_dest.put(caminho_local, path_remoto_tmp)

                # Tenta remover o arquivo no destino para evitar o erro 'Failure' ao renomear por cima
                try:
                    sftp_dest.remove(path_remoto_final)
                except IOError:
                    pass # Se não existir, segue o fluxo normalmente

                # Efetiva a entrega atômica
                sftp_dest.rename(path_remoto_tmp, path_remoto_final)
                print(f"🚀 Upload concluído: {nome_arquivo}")

                os.remove(caminho_local)

        sftp_dest.close()
        trans_dest.close()

        print("\n🏁 PIPELINE EXECUTADO COM SUCESSO TOTAL!")

    except Exception as e:
        print(f"❌ [ERRO na Fase 3]: {e}")

if __name__ == "__main__":
    garantir_pastas_locais()
    if fase1_download():
        fase2_renomear()
        fase3_upload_e_limpeza()