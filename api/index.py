from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import os

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
            response = {
                "message": "Endpoint /api/bolsas em desenvolvimento",
                "status": "coming_soon",
                "bolsas": []
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
            response = {
                "message": "Endpoint /api/metadata em desenvolvimento",
                "status": "coming_soon",
                "last_data_update": "2024-09-23T15:00:00Z",
                "minimum_frontend_version": "1.0.0"
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