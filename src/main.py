import paramiko
import os
import re
import json
import shutil
from datetime import datetime
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

def extrair_sequencial_do_txt(caminho_arquivo):
    """Lê a primeira linha do TXT e extrai o sequencial numérico que vem antes da letra 'E' (ex: 006442E -> 6442)."""
    try:
        with open(caminho_arquivo, 'r', encoding='latin-1') as f:
            primeira_linha = f.readline()
            
        # Procura por números seguidos da letra 'E' na primeira linha
        match = re.search(r'(\d+)[E]', primeira_linha)
        if match:
            codigo_bruto = match.group(1)
            # Remove os zeros à esquerda para limpar (ex: 006442 vira 6442)
            return str(int(codigo_bruto))
    except Exception as e:
        print(f"⚠️ Erro ao ler o conteúdo interno do arquivo para extrair o sequencial: {e}")
    return None

def arquivo_ja_processado(nome_arquivo):
    """Verifica na memória se o arquivo original já foi processado."""
    if not os.path.exists(ARQUIVO_ESTADO):
        return False
    
    try:
        with open(ARQUIVO_ESTADO, 'r', encoding='utf-8') as f:
            estado = json.load(f)
        return nome_arquivo in estado.get("arquivos_processados", [])
    except Exception:
        # Se o arquivo estiver vazio ou corrompido, retorna False para evitar crash
        return False

def registrar_arquivo_processado(nome_arquivo):
    """Salva o arquivo original na memória para evitar reprocessamento (com proteção contra JSON vazio)."""
    estado = {"arquivos_processados": []}
    
    if os.path.exists(ARQUIVO_ESTADO):
        try:
            with open(ARQUIVO_ESTADO, 'r', encoding='utf-8') as f:
                conteudo = json.load(f)
                if isinstance(conteudo, dict):
                    estado = conteudo
        except Exception:
            # Se corrompido/vazio, inicia com a estrutura padrão limpa
            pass
        
    if "arquivos_processados" not in estado:
        estado["arquivos_processados"] = []
        
    if nome_arquivo not in estado["arquivos_processados"]:
        estado["arquivos_processados"].append(nome_arquivo)
        with open(ARQUIVO_ESTADO, 'w', encoding='utf-8') as f:
            json.dump(estado, f, indent=4)

def fase1_download():
    """Conecta na origem e baixa apenas os arquivos modificados HOJE que ainda não foram processados."""
    host = os.getenv("SRC_HOST")
    port = int(os.getenv("SRC_PORT"))
    user = os.getenv("SRC_USER")
    password = os.getenv("SRC_PASS")
    remote_dir = os.getenv("SRC_DIR")
    
    print(f"\n[FASE 1] Conectando ao servidor de ORIGEM ({host}:{port})...")
    hoje = datetime.now().date()
    
    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        arquivos_detalhados = sftp.listdir_attr(remote_dir)
        
        if not arquivos_detalhados:
            print("⚠️ A pasta remota da origem está vazia.")
        else:
            print(f"📦 Analisando {len(arquivos_detalhados)} arquivo(s) na Origem...")
            baixados_contador = 0
            
            for attr in arquivos_detalhados:
                nome_arquivo = attr.filename
                
                # Verifica a data de modificação do arquivo no servidor remoto
                data_modificacao = datetime.fromtimestamp(attr.st_mtime).date()
                
                if data_modificacao != hoje:
                    print(f"⏩ Ignorado (Data anterior a hoje): {nome_arquivo} ({data_modificacao})")
                    continue
                
                if arquivo_ja_processado(nome_arquivo):
                    print(f"⏩ Ignorado (Já processado anteriormente): {nome_arquivo}")
                    continue
                
                remote_path = f"{remote_dir}/{nome_arquivo}"
                local_path = os.path.join(PASTA_TEMP, nome_arquivo)
                
                sftp.get(remote_path, local_path)
                print(f"⬇️ Baixado arquivo de HOJE: {nome_arquivo}")
                baixados_contador += 1
                
            print(f"📥 Total de novos arquivos baixados: {baixados_contador}")
                
        sftp.close()
        transport.close()
        return True
        
    except Exception as e:
        print(f"❌ [ERRO na Fase 1]: {e}")
        return False

def fase2_renomear():
    """Extrai CDL e Filiada do nome, o sequencial de dentro do TXT, e renomeia para CDL_FILIADA_SEQ_HASH."""
    arquivos = os.listdir(PASTA_TEMP)
    if not arquivos:
        return

    print(f"\n[FASE 2] Iniciando renomeação e backup local de {len(arquivos)} arquivo(s)...")
    
    padrao_ja_renomeado = re.compile(r"^\d+_\d+_\d+_.+$")
    padrao_original = re.compile(r"^(\d+)_(\d+)_(.+$)")
    
    for nome_original in arquivos:
        caminho_antigo = os.path.join(PASTA_TEMP, nome_original)
        
        if not os.path.isfile(caminho_antigo) or padrao_ja_renomeado.match(nome_original):
            continue
            
        match = padrao_original.match(nome_original)
        
        if match:
            cdl = match.group(1)          # Ex: 1501
            filiada = match.group(2)      # Ex: 100358
            hash_arquivo = match.group(3) # Ex: 2026091500001
            
            # Extrai o sequencial de dentro do arquivo TXT (ex: 6442)
            sequencial = extrair_sequencial_do_txt(caminho_antigo)
            
            if sequencial:
                # Formato final correto: 1501_100358_6442_2026091500001
                novo_nome = f"{cdl}_{filiada}_{sequencial}_{hash_arquivo}"
                caminho_novo = os.path.join(PASTA_TEMP, novo_nome)
                
                os.replace(caminho_antigo, caminho_novo)
                print(f"✅ Renomeado: {nome_original} ➔ {novo_nome} (Sequencial interno: {sequencial})")
                
                # Salva backup na pasta de controle local
                caminho_backup = os.path.join(PASTA_PROCESSADOS, novo_nome)
                shutil.copy2(caminho_novo, caminho_backup)
                
                # Registra na memória local que este arquivo original foi processado
                registrar_arquivo_processado(nome_original)
            else:
                print(f"⚠️ Falha ao extrair o sequencial interno do arquivo: {nome_original}")
        else:
            print(f"⚠️ O arquivo '{nome_original}' não segue o padrão esperado de nome.")

def fase3_upload_e_limpeza():
    """Envia os arquivos renomeados para o destino e limpa a pasta local temp."""
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

                print(f"⬆️ Enviando: {nome_arquivo} (como .tmp)...")
                sftp_dest.put(caminho_local, path_remoto_tmp)

                try:
                    sftp_dest.remove(path_remoto_final)
                except IOError:
                    pass

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