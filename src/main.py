from src.state_manager import garantir_pastas_locais
from src.download import fase1_download
from src.renamer import fase2_renomear
from src.upload import fase3_upload

if __name__ == "__main__":
    garantir_pastas_locais()
    
    # Esteira de Execução
    if fase1_download():
        fase2_renomear()
        fase3_upload()