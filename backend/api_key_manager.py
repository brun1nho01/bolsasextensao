"""
Gerenciador Seguro de API Keys
Implementa práticas de segurança para proteção de chaves sensíveis
"""
import os
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIKeyManager:
    """Gerenciador seguro de API keys com monitoramento de uso"""
    
    def __init__(self):
        self.usage_tracker = defaultdict(int)
        self.last_rotation_check = datetime.now()
        self.alert_threshold = 100  # Alertar após 100 requisições em 1 hora
        
    def get_gemini_keys(self) -> list:
        """
        Obtém chaves do Gemini de forma segura
        Retorna lista de chaves válidas
        """
        keys_str = os.getenv("GEMINI_API_KEYS")
        
        if not keys_str:
            logger.critical("🚨 GEMINI_API_KEYS não configurada!")
            raise ValueError("GEMINI_API_KEYS não encontrada no ambiente")
        
        # Parse e validação
        keys = [key.strip() for key in keys_str.split(',') if key.strip()]
        
        if not keys:
            logger.critical("🚨 Nenhuma chave válida encontrada em GEMINI_API_KEYS")
            raise ValueError("GEMINI_API_KEYS está vazia")
        
        logger.info(f"✅ {len(keys)} chave(s) do Gemini carregada(s) com sucesso")
        return keys
    
    def track_usage(self, key_index: int):
        """
        Rastreia uso de cada chave
        Alerta sobre uso anormal
        """
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        tracking_key = f"{current_hour}:{key_index}"
        
        self.usage_tracker[tracking_key] += 1
        
        # Verifica se atingiu threshold de alerta
        if self.usage_tracker[tracking_key] >= self.alert_threshold:
            logger.warning(
                f"⚠️ ALERTA: Chave #{key_index} atingiu {self.usage_tracker[tracking_key]} "
                f"requisições na última hora (threshold: {self.alert_threshold})"
            )
    
    def verify_scraper_key_secure(self, provided_key: str) -> bool:
        """
        Verifica API key do scraper de forma segura contra timing attacks
        
        Args:
            provided_key: Chave fornecida pelo cliente
            
        Returns:
            bool: True se válida, False caso contrário
        """
        scraper_api_key = os.getenv("SCRAPER_API_KEY")
        
        if not scraper_api_key:
            logger.critical("🚨 SCRAPER_API_KEY não configurada no servidor!")
            raise RuntimeError("SCRAPER_API_KEY não configurada")
        
        # Comparação segura contra timing attacks
        is_valid = hmac.compare_digest(provided_key, scraper_api_key)
        
        if not is_valid:
            logger.warning(
                f"⚠️ Tentativa de acesso não autorizado ao scraping | "
                f"Timestamp: {datetime.now().isoformat()}"
            )
        
        return is_valid
    
    def check_rotation_needed(self) -> bool:
        """
        Verifica se as chaves precisam de rotação
        (Placeholder para implementação futura com secret manager)
        """
        days_since_rotation = (datetime.now() - self.last_rotation_check).days
        
        if days_since_rotation >= 30:
            logger.warning(
                f"⚠️ ROTAÇÃO RECOMENDADA: Chaves não foram rotacionadas há {days_since_rotation} dias"
            )
            return True
        
        return False
    
    def get_usage_stats(self) -> dict:
        """Retorna estatísticas de uso das chaves"""
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        
        stats = {
            "current_hour": current_hour,
            "total_requests": sum(self.usage_tracker.values()),
            "by_key": {}
        }
        
        for tracking_key, count in self.usage_tracker.items():
            if tracking_key.startswith(current_hour):
                key_index = tracking_key.split(':')[1]
                stats["by_key"][f"key_{key_index}"] = count
        
        return stats


# Instância global do gerenciador
key_manager = APIKeyManager()

