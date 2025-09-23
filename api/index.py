import sys
import os
from fastapi import FastAPI, Query, Depends, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid

# Adiciona o diretório raiz ao Python path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import dos módulos do backend
from backend.models import BolsaComProjeto, Projeto, Edital, BolsasResponse
from backend.database import SupabaseManager
from backend.tasks import run_scraping_task

app = FastAPI(
    title="UENF Scraper API",
    description="API para acessar dados de editais e bolsas da UENF, coletados por um scraper com IA.",
    version="1.0.0"
)

# --- Configuração do CORS ---
cors_origins_str = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [origin.strip() for origin in cors_origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependência para o SupabaseManager ---
def get_db_manager():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("Variáveis de ambiente do Supabase não configuradas.")
    return SupabaseManager(supabase_url=supabase_url, supabase_key=supabase_key)

# --- Dependência de Segurança ---
def verify_api_key(x_api_key: str = Header(...)):
    """Verifica se a chave de API enviada no header é válida."""
    scraper_api_key = os.environ.get("SCRAPER_API_KEY")
    if not scraper_api_key:
        raise HTTPException(status_code=500, detail="Chave de API do servidor não configurada.")
    if x_api_key != scraper_api_key:
        raise HTTPException(status_code=401, detail="Chave de API inválida ou ausente.")
    return True

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bem-vindo à API do Scraper UENF!"}

@app.get("/api/metadata", tags=["Metadata"])
def get_metadata_endpoint(db: SupabaseManager = Depends(get_db_manager)):
    """
    Retorna metadados da aplicação, como a data da última atualização dos dados
    e a versão mínima do frontend compatível.
    """
    metadata = db.get_metadata()
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadados não encontrados.")
    return metadata

@app.get("/api/bolsas", response_model=BolsasResponse, tags=["Bolsas"])
def get_bolsas_endpoint(
    db: SupabaseManager = Depends(get_db_manager),
    page: int = 1,
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filtra por status da bolsa (ex: 'disponivel', 'preenchida')"),
    centro: Optional[str] = Query(None, description="Filtra por centro da UENF (ex: 'ccta', 'cct')"),
    tipo: Optional[str] = Query(None, description="Filtra por tipo de bolsa (ex: 'extensao', 'UA Superior')"),
    q: Optional[str] = Query(None, description="Busca por nome do projeto ou orientador"),
    sort: str = 'created_at',
    order: str = 'desc'
):
    """
    Lista as bolsas com filtros e paginação.
    """
    bolsas_data = db.get_bolsas_paginated(
        page=page, 
        page_size=page_size, 
        status=status, 
        centro=centro,
        tipo=tipo,
        q=q, 
        sort=sort, 
        order=order
    )
    return bolsas_data

@app.get("/api/bolsas/{bolsa_id}", response_model=BolsaComProjeto, tags=["Bolsas"])
def get_bolsa_endpoint(
    bolsa_id: uuid.UUID, 
    background_tasks: BackgroundTasks,
    db: SupabaseManager = Depends(get_db_manager)
):
    """
    Busca uma bolsa específica pelo seu ID e incrementa o contador de visualizações.
    """
    background_tasks.add_task(db.increment_view_count, str(bolsa_id))
    bolsa = db.get_bolsa(str(bolsa_id))
    if not bolsa:
        raise HTTPException(status_code=404, detail="Bolsa não encontrada")
    return bolsa

@app.get("/api/projetos", response_model=List[Projeto], tags=["Projetos"])
def get_projetos_endpoint(
    db: SupabaseManager = Depends(get_db_manager),
    page: int = 1,
    page_size: int = Query(10, ge=1, le=100)
):
    """
    Lista os projetos com paginação.
    """
    return db.get_projetos(page=page, page_size=page_size)

@app.get("/api/projetos/{projeto_id}", response_model=Projeto, tags=["Projetos"])
def get_projeto_endpoint(projeto_id: uuid.UUID, db: SupabaseManager = Depends(get_db_manager)):
    """
    Busca um projeto específico pelo seu ID.
    """
    projeto = db.get_projeto(str(projeto_id))
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return projeto

@app.get("/api/editais", response_model=List[Edital], tags=["Editais"])
def get_editais_endpoint(
    db: SupabaseManager = Depends(get_db_manager),
    page: int = 1,
    page_size: int = Query(10, ge=1, le=100)
):
    """
    Lista os editais com paginação.
    """
    return db.get_editais(page=page, page_size=page_size)

@app.get("/api/editais/{edital_id}", response_model=Edital, tags=["Editais"])
def get_edital_endpoint(edital_id: uuid.UUID, db: SupabaseManager = Depends(get_db_manager)):
    """
    Busca um edital específico pelo seu ID.
    """
    edital = db.get_edital(str(edital_id))
    if not edital:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return edital

@app.get("/api/ranking", response_model=List[BolsaComProjeto], tags=["Ranking"])
def get_ranking_endpoint(
    db: SupabaseManager = Depends(get_db_manager),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Retorna as bolsas mais visualizadas.
    """
    return db.get_ranking_bolsas(limit=limit)

@app.post("/api/scrape/start", status_code=202, tags=["Scraper"])
def start_scraper_endpoint(
    background_tasks: BackgroundTasks,
    is_authorized: bool = Depends(verify_api_key)
):
    """
    Inicia o processo de scraping em segundo plano.
    A API retorna uma resposta imediata enquanto a tarefa é executada.
    """
    print(">>> Endpoint de scraping acionado. Adicionando tarefa em segundo plano...")
    background_tasks.add_task(run_scraping_task)
    return {"message": "Processo de scraping iniciado em segundo plano."}
