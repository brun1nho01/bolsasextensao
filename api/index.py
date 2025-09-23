from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Aplicação FastAPI simples para testar na Vercel
app = FastAPI(
    title="UENF Scraper API",
    description="API para acessar dados de editais e bolsas da UENF",
    version="1.0.0"
)

# Configuração de CORS
cors_origins_str = os.environ.get("CORS_ORIGINS", "*")
origins = [origin.strip() for origin in cors_origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints básicos para testar
@app.get("/")
def read_root():
    return {
        "message": "Bem-vindo à API do Scraper UENF!",
        "status": "funcionando",
        "version": "1.0.0"
    }

@app.get("/api/")
def api_root():
    return {
        "message": "API do Scraper UENF funcionando!",
        "endpoints": ["/api/health", "/api/test"],
        "status": "ok"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Backend funcionando na Vercel!"
    }

@app.get("/api/test")
def test_endpoint():
    return {
        "status": "success",
        "message": "Endpoint de teste funcionando",
        "environment": "vercel-serverless"
    }

# Endpoint simples para testar Supabase
@app.get("/api/config-test")
def config_test():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    gemini_keys = os.environ.get("GEMINI_API_KEYS")
    
    return {
        "supabase_configured": bool(supabase_url and supabase_key),
        "gemini_configured": bool(gemini_keys),
        "cors_origins": origins
    }

# Exportação para Vercel
handler = app