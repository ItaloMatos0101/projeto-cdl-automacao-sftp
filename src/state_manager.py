import os
import json
import re

# Diretórios e Arquivos Globais
PASTA_TEMP = "./temp"
PASTA_PROCESSADOS = "./processados"
ARQUIVO_ESTADO = "./logs/contador.json"

def garantir_pastas_locais():
    """Garante a existência das pastas de trabalho."""
    os.makedirs(PASTA_TEMP, exist_ok=True)
    os.makedirs(PASTA_PROCESSADOS, exist_ok=True)
    os.makedirs("./logs", exist_ok=True)

def extrair_sequencial_do_txt(caminho_arquivo):
    """Lê a primeira linha do TXT e extrai o sequencial que vem antes da letra 'E' (ex: 006442E -> 6442)."""
    try:
        with open(caminho_arquivo, 'r', encoding='latin-1') as f:
            primeira_linha = f.readline()
            
        match = re.search(r'(\d+)[E]', primeira_linha)
        if match:
            return str(int(match.group(1)))
    except Exception as e:
        print(f"Erro ao ler o conteúdo interno do arquivo: {e}")
    return None

def arquivo_ja_processado(nome_arquivo):
    """Verifica se o arquivo já consta no histórico."""
    if not os.path.exists(ARQUIVO_ESTADO):
        return False
    
    try:
        with open(ARQUIVO_ESTADO, 'r', encoding='utf-8') as f:
            estado = json.load(f)
        return nome_arquivo in estado.get("arquivos_processados", [])
    except Exception:
        return False

def registrar_arquivo_processado(nome_arquivo):
    """Registra o arquivo no histórico de controle."""
    estado = {"arquivos_processados": []}
    
    if os.path.exists(ARQUIVO_ESTADO):
        try:
            with open(ARQUIVO_ESTADO, 'r', encoding='utf-8') as f:
                conteudo = json.load(f)
                if isinstance(conteudo, dict):
                    estado = conteudo
        except Exception:
            pass
        
    if "arquivos_processados" not in estado:
        estado["arquivos_processados"] = []
        
    if nome_arquivo not in estado["arquivos_processados"]:
        estado["arquivos_processados"].append(nome_arquivo)
        with open(ARQUIVO_ESTADO, 'w', encoding='utf-8') as f:
            json.dump(estado, f, indent=4)