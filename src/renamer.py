import os
import re
import shutil
from state_manager import (
    PASTA_TEMP, 
    PASTA_PROCESSADOS, 
    extrair_sequencial_do_txt, 
    registrar_arquivo_processado
)

def fase2_renomear():
    """Lê o arquivo baixado, extrai os códigos e renomeia para CDL_FILIADA_SEQ_HASH."""
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
            
            sequencial = extrair_sequencial_do_txt(caminho_antigo)
            
            if sequencial:
                novo_nome = f"{cdl}_{filiada}_{sequencial}_{hash_arquivo}"
                caminho_novo = os.path.join(PASTA_TEMP, novo_nome)
                
                os.replace(caminho_antigo, caminho_novo)
                print(f"Renomeado: {nome_original} ➔ {novo_nome} (Sequencial interno: {sequencial})")
                
                caminho_backup = os.path.join(PASTA_PROCESSADOS, novo_nome)
                shutil.copy2(caminho_novo, caminho_backup)
                
                registrar_arquivo_processado(nome_original)
            else:
                print(f"Falha ao extrair o sequencial interno do arquivo: {nome_original}")
        else:
            print(f"O arquivo '{nome_original}' não segue o padrão esperado.")