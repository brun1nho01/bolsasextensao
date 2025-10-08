"""
Rate Limiter para Vercel Serverless
Implementação otimizada para ambiente serverless
"""
import os
import json
import time
from typing import Dict, Tuple, Optional

# Para produção, usar Vercel KV ou Edge Config
# Por enquanto, usando implementação em memória (reset a cada cold start)

class VercelRateLimiter:
    """
    Rate Limiter adaptado para Vercel Serverless
    
    NOTA: Esta implementação em memória é resetada a cada cold start.
    Para produção, migre para Vercel KV (Redis) ou Edge Config.
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
        self.limits = {
            # Limites por endpoint
            "/api/bolsas": (200, 60),      # 200 req/min
            "/api/bolsas/": (200, 60),     # 200 req/min (com ID)
            "/api/ranking": (50, 60),       # 50 req/min
            "/api/editais": (100, 60),      # 100 req/min
            "/api/metadata": (100, 60),     # 100 req/min
            "/api/analytics": (50, 60),     # 50 req/min
            "/api/scrape": (5, 3600),       # 5 req/hora (CRÍTICO)
            "/api/alertas": (20, 3600),     # 20 req/hora
            "default": (100, 60)            # 100 req/min (padrão)
        }
    
    def get_client_ip(self, request_headers: dict) -> str:
        """
        Extrai IP do cliente dos headers da Vercel
        """
        # Vercel passa o IP real em headers específicos
        ip = (
            request_headers.get('x-forwarded-for', '').split(',')[0].strip() or
            request_headers.get('x-real-ip', '') or
            request_headers.get('cf-connecting-ip', '') or  # Cloudflare
            'unknown'
        )
        return ip
    
    def get_limit(self, path: str) -> Tuple[int, int]:
        """
        Retorna (max_requests, window_seconds) para o path
        """
        # Match exato
        if path in self.limits:
            return self.limits[path]
        
        # Match por prefixo (para paths com ID)
        for limit_path, (max_req, window) in self.limits.items():
            if path.startswith(limit_path):
                return max_req, window
        
        # Default
        return self.limits["default"]
    
    def check_limit(self, ip: str, path: str) -> Tuple[bool, dict]:
        """
        Verifica se request é permitida
        
        Returns:
            (is_allowed, rate_limit_info)
        """
        current_time = time.time()
        max_requests, window = self.get_limit(path)
        
        # Inicializa tracking para este IP se necessário
        if ip not in self.requests:
            self.requests[ip] = []
        
        # Remove requests fora da janela
        window_start = current_time - window
        self.requests[ip] = [
            ts for ts in self.requests[ip] 
            if ts > window_start
        ]
        
        # Conta requests na janela
        request_count = len(self.requests[ip])
        
        # Verifica limite
        if request_count >= max_requests:
            retry_after = int(window - (current_time - self.requests[ip][0])) + 1
            
            return False, {
                "allowed": False,
                "limit": max_requests,
                "remaining": 0,
                "window": window,
                "retry_after": retry_after,
                "reset": int(current_time + retry_after)
            }
        
        # Adiciona request atual
        self.requests[ip].append(current_time)
        
        return True, {
            "allowed": True,
            "limit": max_requests,
            "remaining": max_requests - request_count - 1,
            "window": window,
            "reset": int(current_time + window)
        }


# Instância global (será resetada a cada cold start)
vercel_limiter = VercelRateLimiter()


def apply_rate_limit(request_headers: dict, request_path: str) -> Optional[dict]:
    """
    Aplica rate limiting e retorna None se OK, ou dict com erro se bloqueado
    
    Args:
        request_headers: Headers da requisição
        request_path: Caminho da requisição
        
    Returns:
        None se permitido, dict com erro se bloqueado
    """
    ip = vercel_limiter.get_client_ip(request_headers)
    is_allowed, info = vercel_limiter.check_limit(ip, request_path)
    
    if not is_allowed:
        return {
            "error": "Rate limit exceeded",
            "message": f"Você excedeu o limite de {info['limit']} requisições por {info['window']} segundos",
            "limit": info['limit'],
            "retry_after": info['retry_after'],
            "window": info['window']
        }
    
    return None  # Permitido

