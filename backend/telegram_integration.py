"""
Integração com o Sistema de Notificações Telegram Existente
Ponte entre backend/scraper e api/index.py (sistema existente)
"""

def call_telegram_notifications(titulo: str, link: str, tipo: str):
    """
    Chama o sistema de notificações existente no api/index.py
    
    Esta função serve como ponte entre:
    - backend/ (scraper, parser, database) 
    - api/index.py (sistema de notificações funcionando)
    """
    try:
        # Importa as funções do sistema existente
        import sys
        import os
        
        # Adiciona o diretório api/ ao path
        api_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api')
        if api_path not in sys.path:
            sys.path.append(api_path)
        
        # Importa a função de notificação do sistema existente
        from index import notify_new_edital
        
        # Chama a função usando a infraestrutura já funcionando
        result = notify_new_edital(
            edital_titulo=titulo,
            edital_link=link, 
            edital_type=tipo
        )
        
        print(f"📱 Resultado da notificação: {result}")
        return result
        
    except Exception as e:
        print(f"⚠️ Erro ao chamar sistema de notificações: {e}")
        # Fallback - pelo menos logga que deveria notificar
        print(f"📱 FALLBACK - Dados para notificação manual:")
        print(f"   Título: {titulo}")
        print(f"   Tipo: {tipo}")
        print(f"   Link: {link}")
        
        return {
            "status": "fallback",
            "message": "Sistema de notificação funcionará via API"
        }

# Exemplo de como usar:
if __name__ == "__main__":
    # Teste de integração
    result = call_telegram_notifications(
        titulo="PROEX - Edital de Extensão Teste 2025",
        link="https://uenf.br/editais/teste",
        tipo="extensao"
    )
    print(f"Resultado do teste: {result}")
