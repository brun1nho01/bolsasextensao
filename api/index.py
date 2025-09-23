from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import os

# Importar Supabase apenas se disponível (para não quebrar outros endpoints)
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Supabase não disponível - usando mocks")

def get_supabase_client():
    """Conecta ao Supabase se as variáveis estiverem configuradas"""
    if not SUPABASE_AVAILABLE:
        return None
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        return None
    
    try:
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Erro ao conectar Supabase: {e}")
        return None

def get_metadata_from_supabase():
    """Busca metadados do Supabase"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        response = supabase.table('metadata').select('key, value').execute()
        if response.data:
            # Transforma lista em dicionário
            metadata = {item['key']: item['value'] for item in response.data}
            return metadata
        return None
    except Exception as e:
        print(f"Erro ao buscar metadados: {e}")
        return None

def get_bolsas_from_supabase(params):
    """Busca bolsas do Supabase com filtros e paginação"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        # Parâmetros de paginação
        page = int(params.get('page', ['1'])[0])
        page_size = int(params.get('page_size', ['10'])[0])
        page_size = min(page_size, 100)  # Limita a 100
        offset = (page - 1) * page_size
        
        # Query base com contagem total
        query = supabase.table('bolsas_view').select('*', count='exact')
        
        # Filtros
        status = params.get('status', [None])[0]
        if status and status != 'all':
            query = query.eq('status', status)
            
        centro = params.get('centro', [None])[0]
        if centro and centro != 'all':
            query = query.eq('centro', centro)
            
        tipo = params.get('tipo', [None])[0]
        if tipo and tipo != 'all':
            if tipo == 'extensao':
                query = query.or_('tipo.ilike.%Extensão%,tipo.ilike.%Discente%')
            elif tipo == 'UA Superior':
                query = query.or_('tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%').ilike('tipo', '%Superior%')
            elif tipo == 'UA Médio':
                # Filtra por UA E Médio
                query = query.filter('and', 'or(tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%),or(tipo.ilike.%Médio%,tipo.ilike.%Nível Médio%)')
            elif tipo == 'UA Fundamental':
                query = query.or_('tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%').ilike('tipo', '%Fundamental%')
        
        # Busca textual
        q = params.get('q', [None])[0]
        if q:
            # Busca simples usando ilike (não temos FTS no handler simples)
            search_term = f"%{q}%"
            query = query.or_(f'nome_projeto.ilike.{search_term},orientador.ilike.{search_term}')
            
        # Ordenação
        sort = params.get('sort', ['created_at'])[0]
        order = params.get('order', ['desc'])[0]
        
        # Ordenação primária por status
        query = query.order('status_order', desc=False)
        
        # Ordenação secundária
        if sort and order:
            is_desc = order.lower() == 'desc'
            query = query.order(sort, desc=is_desc)
        
        # Paginação
        query = query.range(offset, offset + page_size - 1)
        
        response = query.execute()
        
        if response.data is not None:
            total_count = response.count if response.count is not None else 0
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                "bolsas": response.data,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        
        return None
        
    except Exception as e:
        print(f"Erro ao buscar bolsas: {e}")
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse da URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Headers básicos
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Roteamento simples
        if path == '/api/' or path == '/api':
            response = {
                "message": "API do Scraper UENF funcionando!",
                "endpoints": ["/api/health", "/api/test", "/api/config-test"],
                "status": "ok"
            }
        elif path == '/api/health':
            response = {
                "status": "healthy",
                "message": "Backend funcionando na Vercel!",
                "timestamp": "2024-09-23"
            }
        elif path == '/api/test':
            response = {
                "status": "success",
                "message": "Endpoint de teste funcionando",
                "environment": "vercel-serverless"
            }
        elif path == '/api/config-test':
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY")
            gemini_keys = os.environ.get("GEMINI_API_KEYS")
            
            response = {
                "supabase_configured": bool(supabase_url and supabase_key),
                "gemini_configured": bool(gemini_keys),
                "cors_origins": "*"
            }
        elif path == '/api/bolsas':
            # Parse dos parâmetros da query string
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # Tentar buscar dados reais do Supabase
            bolsas_data = get_bolsas_from_supabase(query_params)
            
            if bolsas_data:
                # Dados reais do Supabase
                response = bolsas_data
            else:
                # Fallback para dados mock
                response = {
                    "bolsas": [],
                    "total": 0,
                    "page": 1,
                    "page_size": 10,
                    "total_pages": 0,
                    "status": "mock_data",
                    "message": "Usando dados mock - Supabase não conectado"
                }
        elif path == '/api/ranking':
            response = {
                "message": "Endpoint /api/ranking em desenvolvimento", 
                "status": "coming_soon",
                "ranking": []
            }
        elif path == '/api/editais':
            response = {
                "message": "Endpoint /api/editais em desenvolvimento",
                "status": "coming_soon", 
                "editais": []
            }
        elif path == '/api/metadata':
            # Tentar buscar dados reais do Supabase
            metadata = get_metadata_from_supabase()
            
            if metadata:
                # Dados reais do Supabase
                response = metadata
            else:
                # Fallback para dados mock se Supabase não estiver disponível
                response = {
                    "last_data_update": "2024-09-23T15:00:00Z",
                    "minimum_frontend_version": "1.0.0",
                    "status": "mock_data",
                    "message": "Usando dados mock - Supabase não conectado"
                }
        else:
            response = {
                "error": "Endpoint não encontrado",
                "path": path,
                "available_endpoints": ["/api/", "/api/health", "/api/test", "/api/config-test"]
            }
        
        # Retorna a resposta JSON
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        # Para requisições CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()