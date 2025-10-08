"""
Sistema de Rate Limiting para API
Previne abuso e ataques DDoS
"""
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate Limiter simples baseado em memória
    Para produção, considere usar Redis ou Vercel Edge Config
    """
    
    def __init__(self):
        # Armazena: {ip: [(timestamp, count)]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 300  # Limpar a cada 5 minutos
        self.last_cleanup = time.time()
        
        # Configurações de limite
        self.limits = {
            # Endpoints públicos
            "default": {"requests": 100, "window": 60},  # 100 req/min
            
            # Endpoints de leitura
            "/api/bolsas": {"requests": 200, "window": 60},  # 200 req/min
            "/api/ranking": {"requests": 50, "window": 60},   # 50 req/min
            "/api/editais": {"requests": 100, "window": 60},  # 100 req/min
            
            # Endpoints sensíveis
            "/api/scrape": {"requests": 5, "window": 3600},   # 5 req/hora
            "/api/alertas": {"requests": 20, "window": 3600}, # 20 req/hora
        }
    
    def _cleanup_old_requests(self):
        """Remove requisições antigas para economizar memória"""
        current_time = time.time()
        
        # Só limpa a cada 5 minutos
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # Remove tudo mais antigo que 1 hora
        
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                (ts, count) for ts, count in self.requests[ip] 
                if ts > cutoff_time
            ]
            
            # Remove IP se não tem mais requisições
            if not self.requests[ip]:
                del self.requests[ip]
        
        self.last_cleanup = current_time
        logger.info(f"🧹 Rate limiter cleanup: {len(self.requests)} IPs rastreados")
    
    def get_limit_for_endpoint(self, endpoint: str) -> Tuple[int, int]:
        """
        Retorna (requests, window) para o endpoint
        
        Args:
            endpoint: Caminho do endpoint (ex: /api/bolsas)
            
        Returns:
            Tupla (número de requests permitidas, janela em segundos)
        """
        # Tenta match exato primeiro
        if endpoint in self.limits:
            limit = self.limits[endpoint]
            return limit["requests"], limit["window"]
        
        # Tenta match por prefixo
        for path, limit in self.limits.items():
            if endpoint.startswith(path):
                return limit["requests"], limit["window"]
        
        # Default
        default = self.limits["default"]
        return default["requests"], default["window"]
    
    def is_allowed(self, ip: str, endpoint: str = "/api/default") -> Tuple[bool, dict]:
        """
        Verifica se requisição é permitida
        
        Args:
            ip: Endereço IP do cliente
            endpoint: Endpoint sendo acessado
            
        Returns:
            Tupla (permitido: bool, info: dict)
        """
        self._cleanup_old_requests()
        
        current_time = time.time()
        max_requests, window = self.get_limit_for_endpoint(endpoint)
        
        # Filtra requisições dentro da janela de tempo
        window_start = current_time - window
        requests_in_window = [
            (ts, count) for ts, count in self.requests[ip]
            if ts > window_start
        ]
        
        # Conta total de requisições na janela
        total_requests = sum(count for _, count in requests_in_window)
        
        # Verifica se excedeu o limite
        if total_requests >= max_requests:
            logger.warning(
                f"⚠️ RATE LIMIT EXCEEDED | IP: {ip} | Endpoint: {endpoint} | "
                f"Requests: {total_requests}/{max_requests} em {window}s"
            )
            
            return False, {
                "allowed": False,
                "limit": max_requests,
                "window": window,
                "current": total_requests,
                "retry_after": window
            }
        
        # Adiciona nova requisição
        self.requests[ip].append((current_time, 1))
        
        # Remove requisições antigas deste IP
        self.requests[ip] = [
            (ts, count) for ts, count in self.requests[ip]
            if ts > window_start
        ]
        
        remaining = max_requests - total_requests - 1
        
        return True, {
            "allowed": True,
            "limit": max_requests,
            "window": window,
            "current": total_requests + 1,
            "remaining": remaining
        }
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do rate limiter"""
        return {
            "total_ips_tracked": len(self.requests),
            "total_requests_tracked": sum(
                len(reqs) for reqs in self.requests.values()
            ),
            "limits_configured": len(self.limits)
        }


# Instância global do rate limiter
rate_limiter = RateLimiter()

