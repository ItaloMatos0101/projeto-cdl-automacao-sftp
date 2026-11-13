import os
import json
import re

PASTA_PROCESSADOS = "./processados"
ARQUIVO_ESTADO = "./logs/historico.json"

def reconstruir_memoria():
    print("🔄 Iniciando varredura da pasta de processados para reconstruir memória...")
    os.makedirs("./logs", exist_ok=True)
    
    # O state_manager.py atual precisa apenas desta lista limpa
    estado = {
        "arquivos_processados": []
    }
    
    # Padrão: 1501_100358_6442_2026091500001.txt
    padrao_processado = re.compile(r"^(\d+)_(\d+)_(\d+)_(.+)$")
    
    arquivos = os.listdir(PASTA_PROCESSADOS)
    sucesso = 0
    ignorados = 0

    for nome_arquivo in arquivos:
        match = padrao_processado.match(nome_arquivo)
        if match:
            cdl = match.group(1)
            filiada = match.group(2)
            # O sequencial (group 3) é extraído aqui, mas não precisamos salvá-lo no JSON 
            # pois o seu renamer.py agora usa o extrair_sequencial_do_txt() diretamente do conteúdo.
            hash_arquivo = match.group(4)
            
            # Reconstrói o nome original bruto que fica na origem (ex: 1501_100358_2026091000001.txt)
            nome_original = f"{cdl}_{filiada}_{hash_arquivo}"
            
            if nome_original not in estado["arquivos_processados"]:
                estado["arquivos_processados"].append(nome_original)
                sucesso += 1
        else:
            ignorados += 1
            
    # Salva o arquivo JSON (usando utf-8 para manter o padrão do seu state_manager)
    with open(ARQUIVO_ESTADO, 'w', encoding='utf-8') as f:
        json.dump(estado, f, indent=4)
        
    print(f"✅ Memória reconstruída com sucesso em {ARQUIVO_ESTADO}!")
    print(f"📦 Arquivos adicionados à lista de ignorados: {sucesso}")

if __name__ == "__main__":
    reconstruir_memoria()