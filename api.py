from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Importa as funções dos seus módulos atuais
from src.download import fase1_download
from src.renamer import fase2_renomear
from src.upload import fase3_upload
from src.state_manager import garantir_pastas_locais

app = FastAPI(title="API de Automação SFTP - CDL")

# Libera o CORS para o seu frontend JavaScript conseguir conversar com a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/executar-pipeline")
def disparar_pipeline():
    try:
        garantir_pastas_locais()
        
        # Executa a esteira passo a passo
        sucesso_download = fase1_download()
        if not sucesso_download:
            raise HTTPException(status_code=500, detail="Erro na Fase 1 (Download)")
            
        fase2_renomear()
        fase3_upload()
        
        return {
            "status": "sucesso", 
            "mensagem": "Pipeline SFTP executado e sincronizado com sucesso!"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))