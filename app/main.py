from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.router import router
from contextlib import asynccontextmanager
from app.database import db
from app.firebase_setup import scheduler, initialize_firebase # 🟢 ADICIONADO: Importar a função de inicialização
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código aqui roda na inicialização
    print("Aplicação iniciando...")
    
    # 🟢 CORREÇÃO: Inicializa o Firebase ANTES de tudo
    try:
        initialize_firebase()
    except Exception as e:
        print(f"Erro ao inicializar Firebase: {e}")

    # Inicia o agendador de notificações
    if not scheduler.running:
        scheduler.start() 
        
    yield
    
    # Código aqui roda na finalização (quando você usa Ctrl+C)
    print("Aplicação desligando, fechando conexão com o banco...")
    db.close()
    
    # Desliga o agendador
    if scheduler.running:
        scheduler.shutdown()
    print("Conexão com o banco fechada.")

app = FastAPI(
    title="MVP Saúde do Homem - CheckMen",
    description="API para aplicativo de saúde preventiva masculina",
    version="1.0.0",
    lifespan=lifespan
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir todas as rotas
app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "CheckMen API - MVP Saúde do Homem",
        "status": "online",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "message": "API funcionando!",
        "backend": "FastAPI + Oracle NoSQL"
    }