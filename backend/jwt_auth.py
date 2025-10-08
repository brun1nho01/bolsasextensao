"""
Sistema de Autenticação JWT Robusto
Substitui autenticação simples por API key por tokens com expiração
"""
import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Depends, Header
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TokenData(BaseModel):
    """Modelo de dados do token"""
    sub: str  # Subject (geralmente user_id ou service_name)
    exp: datetime  # Expiration
    iat: datetime  # Issued at
    type: str  # Tipo de token (api, scraper, admin)
    scope: list  # Permissões


class JWTAuthManager:
    """Gerenciador de autenticação JWT"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60  # 1 hora
        self.refresh_token_expire_days = 30  # 30 dias
        
        if not self.secret_key:
            logger.warning(
                "⚠️ JWT_SECRET_KEY não configurada. "
                "Usando fallback para SCRAPER_API_KEY (não recomendado para produção)"
            )
            self.secret_key = os.getenv("SCRAPER_API_KEY", "default-secret-key-CHANGE-ME")
    
    def create_access_token(
        self, 
        subject: str, 
        token_type: str = "api",
        scopes: list = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Cria token JWT de acesso
        
        Args:
            subject: Identificador do usuário/serviço
            token_type: Tipo do token (api, scraper, admin)
            scopes: Lista de permissões
            expires_delta: Tempo customizado de expiração
            
        Returns:
            Token JWT assinado
        """
        if scopes is None:
            scopes = []
        
        # Define expiração
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # Payload do token
        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": token_type,
            "scope": scopes
        }
        
        # Codifica token
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        logger.info(f"✅ Token JWT criado para '{subject}' (tipo: {token_type}, expira em: {expire})")
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """
        Verifica e decodifica token JWT
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            TokenData com dados decodificados
            
        Raises:
            HTTPException: Se token inválido ou expirado
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            # Valida campos obrigatórios
            if not payload.get("sub"):
                raise HTTPException(status_code=401, detail="Token inválido: subject ausente")
            
            # Cria TokenData
            token_data = TokenData(
                sub=payload.get("sub"),
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat")),
                type=payload.get("type", "api"),
                scope=payload.get("scope", [])
            )
            
            logger.info(f"✅ Token JWT verificado com sucesso para '{token_data.sub}'")
            
            return token_data
            
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Token JWT expirado")
            raise HTTPException(
                status_code=401, 
                detail="Token expirado. Por favor, autentique novamente."
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"⚠️ Token JWT inválido: {e}")
            raise HTTPException(
                status_code=401, 
                detail="Token inválido"
            )
        except Exception as e:
            logger.error(f"❌ Erro ao verificar token: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Erro ao processar autenticação"
            )
    
    def verify_scope(self, token_data: TokenData, required_scope: str) -> bool:
        """
        Verifica se token tem permissão necessária
        
        Args:
            token_data: Dados do token
            required_scope: Permissão necessária
            
        Returns:
            True se tem permissão, False caso contrário
        """
        return required_scope in token_data.scope or "*" in token_data.scope


# Instância global
jwt_manager = JWTAuthManager()


def get_current_token(authorization: str = Header(None)) -> TokenData:
    """
    ✅ CORREÇÃO: Dependência para verificar token JWT em endpoints protegidos
    
    Uso:
        @app.get("/protected")
        def protected_route(token: TokenData = Depends(get_current_token)):
            return {"user": token.sub}
    """
    if not authorization:
        raise HTTPException(
            status_code=401, 
            detail="Token de autenticação ausente"
        )
    
    # Valida formato "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401, 
            detail="Formato de token inválido. Use: Bearer <token>"
        )
    
    token = parts[1]
    
    # Verifica token
    token_data = jwt_manager.verify_token(token)
    
    return token_data


def require_scope(required_scope: str):
    """
    Decorator para exigir permissão específica
    
    Uso:
        @app.post("/api/scrape")
        @require_scope("scraper:run")
        def run_scraper(token: TokenData = Depends(get_current_token)):
            ...
    """
    def scope_checker(token: TokenData = Depends(get_current_token)):
        if not jwt_manager.verify_scope(token, required_scope):
            logger.warning(
                f"⚠️ Acesso negado: '{token.sub}' tentou acessar "
                f"'{required_scope}' mas tem apenas {token.scope}"
            )
            raise HTTPException(
                status_code=403, 
                detail=f"Permissão '{required_scope}' necessária"
            )
        return token
    
    return scope_checker


# Função auxiliar para compatibilidade com sistema antigo
def verify_api_key_or_jwt(
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
) -> bool:
    """
    ✅ CORREÇÃO: Aceita tanto API Key antiga quanto JWT novo (transição suave)
    
    Prioridade:
    1. JWT (se presente)
    2. API Key (fallback para compatibilidade)
    """
    # Tenta JWT primeiro
    if authorization:
        try:
            token_data = get_current_token(authorization)
            # Verifica se tem permissão de scraper
            if jwt_manager.verify_scope(token_data, "scraper:run"):
                return True
        except HTTPException:
            pass  # Tenta API key
    
    # Fallback para API Key antiga
    if x_api_key:
        from api_key_manager import key_manager
        try:
            return key_manager.verify_scraper_key_secure(x_api_key)
        except:
            pass
    
    # Nenhum método válido
    raise HTTPException(
        status_code=401,
        detail="Autenticação necessária (JWT Bearer token ou X-API-Key)"
    )

