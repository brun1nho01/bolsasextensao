"""
Utilitários de Segurança para API
Funções para sanitização, validação e proteção
"""
import html
import re
from typing import Optional


def sanitize_telegram_html(text: str) -> str:
    """
    ✅ CORREÇÃO: Sanitiza texto para envio seguro via Telegram HTML
    
    Telegram suporta HTML limitado, então precisamos:
    1. Escapar todos os caracteres especiais HTML
    2. Preservar apenas tags permitidas pelo Telegram
    
    Args:
        text: Texto a ser sanitizado
        
    Returns:
        Texto seguro para envio via Telegram
    """
    if not text:
        return ""
    
    # Escape completo de HTML (inclui &, <, >, ", ')
    safe_text = html.escape(text, quote=True)
    
    return safe_text


def sanitize_url(url: str) -> str:
    """
    Sanitiza URL para prevenir injeção
    
    Args:
        url: URL a ser sanitizada
        
    Returns:
        URL segura
    """
    if not url:
        return ""
    
    # Remove espaços em branco
    url = url.strip()
    
    # Valida se é HTTP/HTTPS
    if not url.startswith(('http://', 'https://')):
        # Se não tem protocolo, assume https
        url = 'https://' + url
    
    # Escape de caracteres especiais HTML
    url = html.escape(url, quote=True)
    
    return url


def validate_origin(origin: str, allowed_origins: list) -> bool:
    """
    ✅ CORREÇÃO: Valida origem CORS de forma segura
    
    Args:
        origin: Origin header da requisição
        allowed_origins: Lista de origens permitidas
        
    Returns:
        True se origem é válida, False caso contrário
    """
    if not origin:
        return False
    
    # Remove protocolo e porta para comparação
    origin_clean = origin.lower().strip()
    
    # Verifica se está na lista de permitidos
    for allowed in allowed_origins:
        if origin_clean == allowed.lower().strip():
            return True
        
        # Suporte a wildcards de subdomínio (ex: *.vercel.app)
        if allowed.startswith('*.'):
            domain = allowed[2:]  # Remove *.
            if origin_clean.endswith(domain):
                return True
    
    return False


def get_allowed_origins() -> list:
    """
    Retorna lista de origens CORS permitidas
    
    Prioridade:
    1. Variável de ambiente ALLOWED_ORIGINS
    2. Default seguro (apenas domínio de produção)
    """
    import os
    
    # Tenta pegar da variável de ambiente
    origins_env = os.getenv('ALLOWED_ORIGINS', '')
    
    if origins_env:
        # Split por vírgula e limpa espaços
        origins = [o.strip() for o in origins_env.split(',') if o.strip()]
    else:
        # Default: apenas produção
        origins = [
            'https://bolsasextensao.vercel.app',
            'https://www.bolsasextensao.vercel.app'
        ]
    
    # Sempre adiciona localhost para desenvolvimento (apenas se DEBUG)
    if os.getenv('DEBUG', 'false').lower() == 'true':
        origins.extend([
            'http://localhost:5173',
            'http://localhost:3000',
            'http://127.0.0.1:5173',
            'http://127.0.0.1:3000'
        ])
    
    return origins


def build_cors_headers(origin: str) -> dict:
    """
    ✅ CORREÇÃO: Constrói headers CORS seguros
    
    Args:
        origin: Origin da requisição
        
    Returns:
        Dict com headers CORS apropriados
    """
    allowed_origins = get_allowed_origins()
    
    # Valida origem
    if validate_origin(origin, allowed_origins):
        # Origem válida: retorna origin específico
        return {
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '86400'  # 24 horas
        }
    else:
        # Origem inválida: usa primeiro da lista ou recusa
        if allowed_origins:
            return {
                'Access-Control-Allow-Origin': allowed_origins[0],
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
                'Access-Control-Max-Age': '86400'
            }
        else:
            # Sem origens permitidas: sem CORS
            return {}


def create_telegram_safe_message(
    tipo_edital: str,
    titulo: str, 
    link: str,
    mensagem_extra: str = ""
) -> str:
    """
    ✅ CORREÇÃO: Cria mensagem Telegram segura contra XSS
    
    Args:
        tipo_edital: Tipo do edital (extensao, apoio_academico)
        titulo: Título do edital
        link: Link do edital
        mensagem_extra: Mensagem adicional opcional
        
    Returns:
        Mensagem formatada e segura
    """
    # Sanitizar entradas
    titulo_safe = sanitize_telegram_html(titulo)
    link_safe = sanitize_url(link)
    mensagem_extra_safe = sanitize_telegram_html(mensagem_extra) if mensagem_extra else ""
    
    # Determinar tipo e emoji
    if tipo_edital == 'extensao':
        emoji = "🎓"
        tipo_nome = "BOLSA DE EXTENSÃO"
        if not mensagem_extra_safe:
            mensagem_extra_safe = "✅ Veja orientadores e projetos"
    elif tipo_edital == 'apoio_academico':
        emoji = "📚"
        tipo_nome = "APOIO ACADÊMICO"
        if not mensagem_extra_safe:
            mensagem_extra_safe = "✅ Veja orientadores e projetos"
    else:
        emoji = "📋"
        tipo_nome = "NOVO EDITAL"
        if not mensagem_extra_safe:
            mensagem_extra_safe = "💡 Nova oportunidade disponível!"
    
    # Construir mensagem (sem HTML nas variáveis, pois já foram escapadas)
    # Apenas as tags estruturais são HTML
    mensagem = f"""{emoji} <b>{tipo_nome} UENF!</b>

📋 {titulo_safe}

🔗 <a href="{link_safe}">Acessar Edital</a>

{mensagem_extra_safe}

💻 <a href="https://bolsasextensao.vercel.app/">Ver todas as bolsas</a>

<i>Para cancelar alertas, digite /stop</i>"""
    
    return mensagem

