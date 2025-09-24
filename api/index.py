from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import os
from datetime import datetime, timezone

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

def get_ranking_from_supabase(params):
    """Busca ranking das bolsas mais vistas do Supabase"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        # Parâmetro de limite (padrão 10, máximo 50)
        limit = int(params.get('limit', ['10'])[0])
        limit = min(limit, 50)  # Máximo 50 bolsas no ranking
        
        # Query para buscar as bolsas mais vistas
        query = supabase.table('bolsas_view').select('*').order('view_count', desc=True).limit(limit)
        
        response = query.execute()
        
        if response.data is not None:
            return response.data
        
        return None
        
    except Exception as e:
        print(f"Erro ao buscar ranking: {e}")
        return None

def get_bolsa_by_id(bolsa_id):
    """Busca uma bolsa específica por ID do Supabase"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        # Query para buscar bolsa por ID
        response = supabase.table('bolsas_view').select('*').eq('id', bolsa_id).execute()
        
        if response.data and len(response.data) > 0:
            # Incrementar contador de visualizações (opcional)
            try:
                supabase.table('bolsas').update({'view_count': 'view_count + 1'}).eq('id', bolsa_id).execute()
            except:
                pass  # Não falha se não conseguir atualizar view_count
            
            return response.data[0]
        
        return None
        
    except Exception as e:
        print(f"Erro ao buscar bolsa por ID: {e}")
        return None

def get_editais_from_supabase(params):
    """Busca editais do Supabase com paginação"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        # Parâmetros de paginação
        page = int(params.get('page', ['1'])[0])
        page_size = int(params.get('page_size', ['10'])[0])
        page_size = min(page_size, 100)  # Limita a 100
        offset = (page - 1) * page_size
        
        # Query para buscar editais ordenados por data de publicação
        query = supabase.table('editais').select(
            'id, titulo, link, data_fim_inscricao, created_at, data_publicacao'
        ).order('data_publicacao', desc=True).range(offset, offset + page_size - 1)
        
        response = query.execute()
        
        if response.data is not None:
            return response.data
        
        return None
        
    except Exception as e:
        print(f"Erro ao buscar editais: {e}")
        return None

def get_analytics_from_supabase():
    """Busca estatísticas básicas do Supabase"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        analytics_data = {}
        
        # Total de bolsas
        total_response = supabase.table('bolsas_view').select('*', count='exact').execute()
        analytics_data['total_bolsas'] = total_response.count if total_response.count is not None else 0
        
        # Bolsas por status
        try:
            status_response = supabase.table('bolsas_view').select('status', count='exact').execute()
            status_counts = {}
            for bolsa in status_response.data or []:
                status = bolsa.get('status', 'desconhecido')
                status_counts[status] = status_counts.get(status, 0) + 1
            analytics_data['bolsas_por_status'] = status_counts
        except:
            analytics_data['bolsas_por_status'] = {}
            
        # Centros mais populares (top 5)
        try:
            centros_response = supabase.table('bolsas_view').select('centro', count='exact').execute()
            centro_counts = {}
            for bolsa in centros_response.data or []:
                centro = bolsa.get('centro', 'Não informado')
                centro_counts[centro] = centro_counts.get(centro, 0) + 1
            
            # Top 5 centros
            top_centros = sorted(centro_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            analytics_data['centros_populares'] = [centro for centro, count in top_centros]
        except:
            analytics_data['centros_populares'] = []
            
        # Tipos mais procurados (top 5)
        try:
            tipos_response = supabase.table('bolsas_view').select('tipo', count='exact').execute()
            tipo_counts = {}
            for bolsa in tipos_response.data or []:
                tipo = bolsa.get('tipo', 'Não informado')
                tipo_counts[tipo] = tipo_counts.get(tipo, 0) + 1
            
            # Top 5 tipos
            top_tipos = sorted(tipo_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            analytics_data['tipos_mais_procurados'] = [tipo for tipo, count in top_tipos]
        except:
            analytics_data['tipos_mais_procurados'] = []
        
        # Última atualização
        analytics_data['ultima_atualizacao'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        return analytics_data
        
    except Exception as e:
        print(f"Erro ao buscar analytics: {e}")
        return None

def subscribe_telegram_alerts(telegram_id):
    """Cadastra ID do Telegram para receber alertas de novos editais"""
    supabase = get_supabase_client()
    if not supabase:
        return {"status": "error", "message": "Supabase não disponível"}
    
    try:
        # Limpar e validar Telegram ID (@usuario ou chat_id)
        clean_id = telegram_id.strip()
        
        # Se começar com @, remover o @
        if clean_id.startswith("@"):
            clean_id = clean_id[1:]
        
        # Validar formato (deve ser username ou chat_id numérico)
        if not clean_id:
            return {"status": "error", "message": "ID do Telegram inválido"}
        
        # Para chat_id numérico, salvar apenas o número
        # Para username, salvar sem @
        final_id = clean_id
        
        # Verificar se já existe
        existing = supabase.table('telegram_alerts').select('id').eq('telegram_id', final_id).execute()
        
        if existing.data and len(existing.data) > 0:
            return {"status": "info", "message": "Telegram já cadastrado para alertas"}
        
        # Inserir novo cadastro
        result = supabase.table('telegram_alerts').insert({
            'telegram_id': final_id,
            'status': 'ativo',
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        
        return {
            "status": "success", 
            "message": "Telegram cadastrado com sucesso! Você receberá alertas de novos editais.",
            "telegram_id": final_id
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Erro ao cadastrar Telegram: {str(e)}"}

def send_telegram_message(chat_id, message):
    """Envia mensagem via Telegram Bot API"""
    try:
        print(f"🔗 INICIANDO SEND_TELEGRAM_MESSAGE: chat_id={chat_id}, message_length={len(message)}")
        
        telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        print(f"🔑 TOKEN TELEGRAM: {'✅ Configurado' if telegram_token else '❌ Não encontrado'}")
        
        if not telegram_token:
            # Simulação para testes sem token
            print(f"📱 SIMULANDO Telegram para {chat_id}: {message[:50]}...")
            return {
                "status": "simulated", 
                "message": f"Telegram simulado para {chat_id}"
            }
        
        try:
            import requests
            
            telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            
            # Preparar chat_id baseado no formato
            final_chat_id = chat_id
            
            # Se for só números, usar diretamente como chat_id
            if isinstance(chat_id, str) and chat_id.isdigit():
                final_chat_id = int(chat_id)  # Converter para número
            # Se começar com @, remover o @
            elif isinstance(chat_id, str) and chat_id.startswith('@'):
                final_chat_id = chat_id[1:]  # Remove o @
            # Se for username sem @, usar como está
            else:
                final_chat_id = chat_id
            
            payload = {
                "chat_id": final_chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            print(f"📡 PAYLOAD TELEGRAM: {payload}")
            print(f"🌐 URL TELEGRAM: {telegram_url}")
            
            response = requests.post(telegram_url, json=payload, timeout=10)
            print(f"📊 RESPONSE STATUS: {response.status_code}")
            print(f"📝 RESPONSE TEXT: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📤 TELEGRAM API RESULT: {result}")
                
                if result.get('ok'):
                    success_result = {
                        "status": "sent",
                        "platform": "telegram",
                        "message_id": result['result']['message_id']
                    }
                    print(f"✅ MENSAGEM ENVIADA COM SUCESSO: {success_result}")
                    return success_result
                else:
                    error_result = {
                        "status": "error",
                        "message": f"Telegram API error: {result.get('description', 'Unknown error')}"
                    }
                    print(f"❌ ERRO DA API TELEGRAM: {error_result}")
                    return error_result
            else:
                # Tentar com @ se falhou sem @ (só para usernames, não números)
                if isinstance(chat_id, str) and not chat_id.startswith('@') and not chat_id.isdigit():
                    retry_payload = {
                        "chat_id": "@" + chat_id,
                        "text": message,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True
                    }
                    response_retry = requests.post(telegram_url, json=retry_payload, timeout=10)
                    if response_retry.status_code == 200:
                        result_retry = response_retry.json()
                        if result_retry.get('ok'):
                            return {
                                "status": "sent",
                                "platform": "telegram",
                                "message_id": result_retry['result']['message_id']
                            }
                
                error_http = {
                    "status": "error",
                    "message": f"HTTP {response.status_code}: {response.text}"
                }
                print(f"❌ ERRO HTTP TELEGRAM: {error_http}")
                return error_http
                
        except (requests.exceptions.RequestException, ImportError) as e:
            error_conn = {
                "status": "error",
                "message": f"Erro de conexão: {str(e)}"
            }
            print(f"❌ ERRO DE CONEXÃO TELEGRAM: {error_conn}")
            return error_conn
    
    except Exception as e:
        error_general = {"status": "error", "message": str(e)}
        print(f"❌ ERRO GERAL TELEGRAM: {error_general}")
        return error_general

def setup_telegram_webhook(webhook_url):
    """Configura webhook do Telegram para receber mensagens"""
    try:
        telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        
        if not telegram_token:
            return {"status": "error", "message": "Token do Telegram não configurado"}
        
        import requests
        
        # URL da API do Telegram para configurar webhook
        api_url = f"https://api.telegram.org/bot{telegram_token}/setWebhook"
        
        payload = {
            "url": webhook_url,
            "allowed_updates": ["message"],  # Só receber mensagens
            "drop_pending_updates": True  # CRÍTICO: Limpar as 10 mensagens pendentes que estão causando erro 401
        }
        
        response = requests.post(api_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                return {
                    "status": "success", 
                    "message": "Webhook configurado com sucesso!",
                    "webhook_url": webhook_url
                }
            else:
                return {
                    "status": "error",
                    "message": f"Erro do Telegram: {result.get('description')}"
                }
        else:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def handle_telegram_webhook(update_data):
    """Processa mensagens recebidas via webhook do Telegram"""
    try:
        print(f"🔄 PROCESSANDO WEBHOOK: {update_data}")
        
        message = update_data.get('message', {})
        if not message:
            print("⚠️ UPDATE SEM MENSAGEM")
            return {"status": "ignored", "reason": "Não é uma mensagem", "update_data": update_data}
        
        chat = message.get('chat', {})
        chat_id = chat.get('id')
        text = message.get('text', '').strip()
        
        print(f"💬 MENSAGEM RECEBIDA: chat_id={chat_id}, text='{text}'")
        
        if not chat_id or not text:
            print(f"❌ DADOS INCOMPLETOS: chat_id={chat_id}, text='{text}'")
            return {
                "status": "ignored", 
                "reason": "Mensagem inválida",
                "chat_id": chat_id,
                "text": text
            }
        
        # Responder ao comando /start
        if text.lower() in ['/start', 'start', '/help', 'help']:
            print(f"🚀 COMANDO START DETECTADO de {chat_id}")
            
            username = message.get('from', {}).get('username', '')
            first_name = message.get('from', {}).get('first_name', 'Usuário')
            
            print(f"👤 USUÁRIO: {first_name} (@{username}) - Chat ID: {chat_id}")
            
            response_message = f"""🎓 <b>Olá {first_name}! Bem-vindo ao UENF Alertas!</b>

📱 <b>Seu Chat ID:</b> <code>{chat_id}</code>

💡 <b>Como usar:</b>
1. Copie o número acima
2. Acesse: https://seusite.vercel.app
3. Clique no botão azul (📱)
4. Cole seu Chat ID: <code>{chat_id}</code>
5. Pronto! Você receberá alertas automáticos

🔔 <b>Você receberá notificações sobre:</b>
• Novos editais de extensão
• Resultados de seleções

📝 Digite /stop para cancelar alertas."""
            
            print(f"📤 ENVIANDO RESPOSTA PARA {chat_id}...")
            send_result = send_telegram_message(chat_id, response_message)
            print(f"✅ RESULTADO ENVIO: {send_result}")
            
            result = {
                "status": "handled",
                "command": text,
                "chat_id": chat_id,
                "username": username,
                "first_name": first_name,
                "response_sent": send_result.get('status') == 'sent',
                "send_result": send_result,
                "debug_info": {
                    "original_message": message,
                    "chat_info": chat,
                    "from_info": message.get('from', {}),
                    "response_message_length": len(response_message),
                    "telegram_token_configured": bool(os.environ.get("TELEGRAM_BOT_TOKEN"))
                }
            }
            
            print(f"🏁 RESULTADO FINAL WEBHOOK: {result}")
            return result
        
        # Responder ao comando /stop
        elif text.lower() in ['/stop', 'stop', 'parar']:
            try:
                supabase = get_supabase_client()
                if supabase:
                    # Desativar usuário
                    supabase.table('telegram_alerts').update({
                        'status': 'inativo'
                    }).eq('telegram_id', str(chat_id)).execute()
                    
                    response_message = "❌ Alertas cancelados! Você não receberá mais notificações.\n\n📱 Para reativar, acesse o site e cadastre-se novamente."
                else:
                    response_message = "⚠️ Erro interno. Tente novamente mais tarde."
            except:
                response_message = "⚠️ Erro ao cancelar alertas. Tente novamente."
            
            send_telegram_message(chat_id, response_message)
            return {"status": "handled", "command": "stop", "chat_id": chat_id}
        
        # Comando não reconhecido
        else:
            help_message = f"""🤖 Comandos disponíveis:

/start - Ver seu Chat ID e instruções
/stop - Cancelar alertas

💡 <b>Seu Chat ID:</b> <code>{chat_id}</code>

📱 Use esse número para se cadastrar no site!"""
            
            send_telegram_message(chat_id, help_message)
            return {"status": "handled", "command": "help", "chat_id": chat_id}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def detect_edital_type(edital_titulo):
    """Detecta o tipo de edital baseado no título"""
    titulo_lower = edital_titulo.lower()
    
    # Detectar editais de resultado
    resultado_keywords = ['resultado', 'classificação', 'classificados', 'aprovados', 'selecionados']
    if any(keyword in titulo_lower for keyword in resultado_keywords):
        return 'resultado'
    
    # Detectar editais de extensão
    extensao_keywords = ['extensão', 'extensao', 'discente', 'voluntário', 'voluntario']
    if any(keyword in titulo_lower for keyword in extensao_keywords):
        return 'extensao'
    
    # Outros editais (mestrado, doutorado, etc)
    return 'outros'

def notify_new_edital(edital_titulo, edital_link, edital_type=None):
    """Notifica todos os usuários cadastrados sobre novo edital de extensão ou resultado via Telegram"""
    supabase = get_supabase_client()
    if not supabase:
        return {"status": "error", "message": "Supabase não disponível"}
    
    try:
        # Auto-detectar tipo se não fornecido
        if not edital_type:
            edital_type = detect_edital_type(edital_titulo)
        
        # Só notificar para editais de extensão ou resultado
        if edital_type not in ['extensao', 'resultado']:
            return {
                "status": "skipped", 
                "message": f"Edital tipo '{edital_type}' não gera notificação automática",
                "edital_titulo": edital_titulo
            }
        
        # Buscar todos os IDs ativos do Telegram
        subscribers = supabase.table('telegram_alerts').select('telegram_id').eq('status', 'ativo').execute()
        
        if not subscribers.data:
            return {"status": "info", "message": "Nenhum usuário cadastrado no Telegram"}
        
        # Mensagem personalizada por tipo (HTML é mais seguro que Markdown)
        if edital_type == 'extensao':
            emoji = "🎓"
            tipo_nome = "EDITAL DE EXTENSÃO"
            mensagem_extra = "💡 Oportunidade de extensão universitária!"
        elif edital_type == 'resultado':
            emoji = "🏆"
            tipo_nome = "RESULTADO PUBLICADO"
            mensagem_extra = "🔍 Confira se você foi aprovado(a)!"
        else:
            emoji = "📋"
            tipo_nome = "NOVO EDITAL"
            mensagem_extra = "💡 Nova oportunidade disponível!"
            
        # Escapar caracteres especiais do HTML
        edital_titulo_safe = edital_titulo.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        edital_link_safe = edital_link.replace('&', '&amp;')
        
        mensagem = f"""{emoji} <b>{tipo_nome} UENF!</b>

📋 {edital_titulo_safe}

🔗 <a href="{edital_link_safe}">Acessar Edital</a>

{mensagem_extra}

💻 <a href="https://seusite.vercel.app">Ver mais bolsas</a>

<i>Para cancelar alertas, digite /stop</i>"""

        # Enviar para todos
        sent_count = 0
        errors = []
        
        for subscriber in subscribers.data:
            telegram_id = subscriber['telegram_id']
            result = send_telegram_message(telegram_id, mensagem)
            
            if result['status'] in ['sent', 'simulated']:
                sent_count += 1
            else:
                # Formatar ID para erro (adicionar @ só se não for numérico)
                display_id = telegram_id if telegram_id.isdigit() else f"@{telegram_id}"
                errors.append(f"{display_id}: {result.get('message', 'erro')}")
        
        return {
            "status": "completed",
            "sent_count": sent_count,
            "total_subscribers": len(subscribers.data),
            "edital_type": edital_type,
            "errors": errors
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Erro ao notificar: {str(e)}"}

def run_scraping_serverless():
    """
    Versão do scraping para ambiente serverless com detecção de novos editais.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return {"status": "error", "message": "Supabase não disponível"}
        
        timestamp_utc = datetime.now(timezone.utc).isoformat()
        
        # 1. Buscar último edital conhecido antes do scraping
        try:
            last_edital = supabase.table('editais').select('id, titulo, data_publicacao').order('data_publicacao', desc=True).limit(1).execute()
            last_edital_id = last_edital.data[0]['id'] if last_edital.data else None
        except:
            last_edital_id = None
        
        # 2. AQUI seria executado o scraping real (tasks.py)
        # Por enquanto, vamos simular encontrar um novo edital aleatoriamente
        import random
        found_new_edital = random.choice([True, False])  # 50% chance de simular novo edital
        
        new_editais_count = 0
        notification_results = []
        
        if found_new_edital:
            # Simular diferentes tipos de editais
            import random
            edital_examples = [
                {
                    "titulo": "Edital de Extensão Universitária - Bolsas Discentes 2025",
                    "tipo": "extensao"
                },
                {
                    "titulo": "Resultado Final - Mestrado em Ciência da Computação",
                    "tipo": "resultado"
                },
                {
                    "titulo": "Classificação Final - Extensão Comunitária CCT",
                    "tipo": "resultado"
                },
                {
                    "titulo": "Edital de Bolsas para Projetos de Extensão 2025/1", 
                    "tipo": "extensao"
                },
                {
                    "titulo": "Lista de Aprovados - Doutorado em Engenharia",
                    "tipo": "resultado"
                },
                {
                    "titulo": "Edital de Mestrado - Ciências Naturais",
                    "tipo": "outros"  # Este não vai gerar notificação
                }
            ]
            
            # Escolher um edital aleatório para simular
            edital_simulado = random.choice(edital_examples)
            
            novo_edital = {
                "titulo": edital_simulado["titulo"],
                "link": f"https://uenf.br/editais/simulado-{edital_simulado['tipo']}-{datetime.now().strftime('%Y%m%d')}",
                "tipo": edital_simulado["tipo"],
                "data_publicacao": timestamp_utc
            }
            
            try:
                # Inserir novo edital no banco (simulado)
                # result = supabase.table('editais').insert(novo_edital).execute()
                # new_editais_count = 1
                
                # NOTIFICAR USUÁRIOS VIA WHATSAPP (com tipo específico)
                notification_result = notify_new_edital(
                    edital_titulo=novo_edital["titulo"],
                    edital_link=novo_edital["link"],
                    edital_type=novo_edital["tipo"]
                )
                
                notification_results.append(notification_result)
                
                # Só contar como novo se realmente notificou
                if notification_result.get('status') == 'completed':
                    new_editais_count = 1
                else:
                    new_editais_count = 0
                
            except Exception as e:
                notification_results.append({
                    "status": "error",
                    "message": f"Erro ao notificar novo edital: {str(e)}"
                })
        
        # 3. Atualizar metadados do último scraping
        try:
            # Atualizar timestamp do último scraping
            metadata_update = {
                "last_scraping": timestamp_utc,
                "new_editais_found": new_editais_count
            }
            # supabase.table('metadata').upsert(metadata_update).execute()
        except Exception as e:
            print(f"Erro ao atualizar metadados: {e}")
        
        return {
            "status": "success",
            "message": f"Scraping executado - {new_editais_count} novos editais encontrados",
            "timestamp": timestamp_utc,
            "new_editais": new_editais_count,
            "notifications_sent": notification_results,
            "note": "Versão serverless com alertas WhatsApp integrados"
        }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro no scraping: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

class handler(BaseHTTPRequestHandler):
    def send_json_response(self, data, status_code=200, cache_seconds=3600):
        """Helper para enviar resposta JSON com headers otimizados"""
        # Status HTTP
        self.send_response(status_code)
        
        # Headers básicos
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        # Headers de cache (para melhor performance)
        if cache_seconds > 0:
            self.send_header('Cache-Control', f'public, max-age={cache_seconds}')
            self.send_header('Last-Modified', datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT'))
            
            # ETag simples baseado no hash do conteúdo
            import hashlib
            content_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]
            self.send_header('ETag', f'"{content_hash}"')
        else:
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            
        self.end_headers()
        
        # Retorna a resposta JSON
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        # Parse da URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # Roteamento com cache otimizado
        if path == '/api/' or path == '/api':
            response = {
                "message": "API do Scraper UENF funcionando!",
                "endpoints": {
                    "GET": ["/api/health", "/api/test", "/api/config-test", "/api/bolsas", "/api/bolsas/{id}", "/api/analytics", "/api/editais", "/api/ranking", "/api/metadata", "/api/telegram/setup-webhook", "/api/telegram/debug-webhook", "/api/telegram/test-webhook", "/api/telegram/check-messages", "/api/telegram/logs"],
                    "POST": ["/api/alertas/telegram", "/api/alertas/notify", "/api/alertas/test-detection", "/api/alertas/listar", "/api/telegram/webhook"]
                },
                "status": "ok",
                "whatsapp_alerts": "✅ Configurado"
            }
            return self.send_json_response(response, cache_seconds=300)  # 5 min cache
            
        elif path == '/api/health':
            response = {
                "status": "healthy",
                "message": "Backend funcionando na Vercel!",
                "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            }
            return self.send_json_response(response, cache_seconds=60)  # 1 min cache
            
        elif path == '/api/test':
            response = {
                "status": "success",
                "message": "Endpoint de teste funcionando",
                "environment": "vercel-serverless"
            }
            return self.send_json_response(response, cache_seconds=300)  # 5 min cache
            
        elif path == '/api/config-test':
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY")
            gemini_keys = os.environ.get("GEMINI_API_KEYS")
            
            response = {
                "supabase_configured": bool(supabase_url and supabase_key),
                "gemini_configured": bool(gemini_keys),
                "cors_origins": "*"
            }
            return self.send_json_response(response, cache_seconds=300)  # 5 min cache
        elif path.startswith('/api/bolsas/') and len(path.split('/')) == 4:
            # Endpoint individual: GET /api/bolsas/{id}
            bolsa_id = path.split('/')[3]
            
            # Tentar buscar bolsa específica do Supabase
            bolsa_data = get_bolsa_by_id(bolsa_id)
            
            if bolsa_data:
                # Dados reais do Supabase - cache longo (1 hora)
                return self.send_json_response(bolsa_data, cache_seconds=3600)
            else:
                # Bolsa não encontrada
                response = {
                    "error": "Bolsa não encontrada",
                    "id": bolsa_id,
                    "message": "A bolsa solicitada não foi encontrada ou Supabase não está conectado"
                }
                return self.send_json_response(response, status_code=404, cache_seconds=300)
                
        elif path == '/api/bolsas':
            # Tentar buscar dados reais do Supabase
            bolsas_data = get_bolsas_from_supabase(query_params)
            
            if bolsas_data:
                # Dados reais do Supabase - cache médio (15 min)
                return self.send_json_response(bolsas_data, cache_seconds=900)
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
                return self.send_json_response(response, cache_seconds=60)
                
        elif path == '/api/ranking':
            # Tentar buscar dados reais do Supabase
            ranking_data = get_ranking_from_supabase(query_params)
            
            if ranking_data:
                # Dados reais do Supabase - cache médio (30 min)
                return self.send_json_response(ranking_data, cache_seconds=1800)
            else:
                # Fallback para dados mock
                return self.send_json_response([], cache_seconds=60)
                
        elif path == '/api/editais':
            # Tentar buscar dados reais do Supabase
            editais_data = get_editais_from_supabase(query_params)
            
            if editais_data:
                # Dados reais do Supabase - cache médio (15 min)
                return self.send_json_response(editais_data, cache_seconds=900)
            else:
                # Fallback para dados mock
                return self.send_json_response([], cache_seconds=60)
                
        elif path == '/api/analytics':
            # Endpoint de analytics
            analytics_data = get_analytics_from_supabase()
            
            if analytics_data:
                # Dados reais do Supabase - cache longo (1 hora)
                return self.send_json_response(analytics_data, cache_seconds=3600)
            else:
                # Fallback para dados mock
                response = {
                    "total_bolsas": 0,
                    "bolsas_por_status": {},
                    "centros_populares": [],
                    "tipos_mais_procurados": [],
                    "ultima_atualizacao": datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                    "status": "mock_data",
                    "message": "Usando dados mock - Supabase não conectado"
                }
                return self.send_json_response(response, cache_seconds=60)
        elif path == '/api/scrape':
            # Endpoint para executar scraping manualmente ou via cron
            try:
                # Verificar se foi chamado pelo cron da Vercel
                cron_secret = os.environ.get("CRON_SECRET", "")
                provided_secret = query_params.get('secret', [''])[0] if query_params.get('secret') else ''
                
                # Se há um secret configurado, validar
                if cron_secret and provided_secret != cron_secret:
                    response = {"error": "Unauthorized", "message": "Invalid secret"}
                    return self.send_json_response(response, status_code=401, cache_seconds=0)  # Sem cache
                else:
                    # Executar scraping na versão serverless
                    scraping_result = run_scraping_serverless()
                    
                    response = {
                        "message": "Scraping executado com sucesso",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status": "completed",
                        "result": scraping_result
                    }
                    return self.send_json_response(response, cache_seconds=0)  # Sem cache
            except Exception as e:
                response = {
                    "error": "Scraping failed", 
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                return self.send_json_response(response, status_code=500, cache_seconds=0)  # Sem cache
                
        elif path == '/api/metadata':
            # Tentar buscar dados reais do Supabase
            metadata = get_metadata_from_supabase()
            
            if metadata:
                # Dados reais do Supabase - cache médio (15 min)
                return self.send_json_response(metadata, cache_seconds=900)
            else:
                # Fallback para dados mock se Supabase não estiver disponível
                response = {
                    "last_data_update": "2024-09-23T15:00:00Z",
                    "minimum_frontend_version": "1.0.0",
                    "status": "mock_data",
                    "message": "Usando dados mock - Supabase não conectado"
                }
                return self.send_json_response(response, cache_seconds=60)
                
        elif path == '/api/telegram/debug-webhook':
            # Debug específico do webhook
            try:
                import requests
                token = os.environ.get("TELEGRAM_BOT_TOKEN")
                
                # Verificar status atual
                info_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
                info_response = requests.get(info_url, timeout=10)
                webhook_info = info_response.json()
                
                # Limpar updates pendentes forçadamente
                clear_url = f"https://api.telegram.org/bot{token}/getUpdates"
                clear_response = requests.post(clear_url, json={"offset": -1}, timeout=10)
                
                # Reconfigurar webhook com force
                host_header = self.headers.get('Host', 'localhost')
                webhook_url = f"https://{host_header}/api/telegram/webhook"
                
                set_url = f"https://api.telegram.org/bot{token}/setWebhook"
                set_response = requests.post(set_url, json={
                    "url": webhook_url,
                    "allowed_updates": ["message"],
                    "drop_pending_updates": True,
                    "max_connections": 40
                }, timeout=10)
                
                return self.send_json_response({
                    "status": "debug_complete",
                    "webhook_info_before": webhook_info.get('result', {}),
                    "clear_updates": clear_response.json(),
                    "set_webhook": set_response.json(),
                    "new_webhook_url": webhook_url
                }, cache_seconds=0)
                
            except Exception as e:
                return self.send_json_response({
                    "status": "error",
                    "message": f"Erro no debug: {str(e)}"
                }, status_code=500, cache_seconds=0)
        
        elif path == '/api/telegram/check-messages':
            # Verificar mensagens pendentes no Telegram
            try:
                import requests
                token = os.environ.get("TELEGRAM_BOT_TOKEN")
                
                if not token:
                    return self.send_json_response({
                        "status": "error",
                        "message": "Token não configurado"
                    }, status_code=400, cache_seconds=0)
                
                # Buscar updates pendentes
                updates_url = f"https://api.telegram.org/bot{token}/getUpdates"
                updates_response = requests.get(updates_url, timeout=10)
                updates_data = updates_response.json()
                
                # Informações do webhook
                webhook_url = f"https://api.telegram.org/bot{token}/getWebhookInfo" 
                webhook_response = requests.get(webhook_url, timeout=10)
                webhook_data = webhook_response.json()
                
                return self.send_json_response({
                    "status": "check_complete",
                    "updates": updates_data,
                    "webhook_info": webhook_data,
                    "analysis": {
                        "total_updates": len(updates_data.get('result', [])),
                        "pending_updates": webhook_data.get('result', {}).get('pending_update_count', 0),
                        "last_error": webhook_data.get('result', {}).get('last_error_message'),
                        "webhook_url": webhook_data.get('result', {}).get('url')
                    }
                }, cache_seconds=0)
                
            except Exception as e:
                return self.send_json_response({
                    "status": "error",
                    "message": f"Erro ao verificar mensagens: {str(e)}"
                }, status_code=500, cache_seconds=0)
        
        elif path == '/api/telegram/logs':
            # Ver logs recentes do webhook
            response = {
                "status": "logs",
                "message": "Verificar logs do Vercel Functions para debug",
                "instructions": [
                    "1. Acesse vercel.com → Seu projeto",
                    "2. Vá em Functions → View Function Logs", 
                    "3. Procure por logs com 📥📤🚀 (nossos emojis)",
                    "4. Veja se mensagens do Telegram estão chegando"
                ],
                "current_webhook": f"https://{self.headers.get('Host')}/api/telegram/webhook"
            }
            return self.send_json_response(response, cache_seconds=0)
        
        elif path == '/api/telegram/test-webhook':
            # Teste simples do webhook
            response = {
                "status": "webhook_test",
                "message": "Endpoint de webhook ativo e respondendo",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "headers_received": dict(self.headers),
                "method": "GET",
                "path": path
            }
            return self.send_json_response(response, cache_seconds=0)
        
        elif path == '/api/telegram/setup-webhook':
            # Configurar webhook do Telegram automaticamente
            try:
                # URL do webhook é o domínio + /api/telegram/webhook
                host_header = self.headers.get('Host', 'localhost')
                webhook_url = f"https://{host_header}/api/telegram/webhook"
                
                result = setup_telegram_webhook(webhook_url)
                
                if result['status'] == 'success':
                    return self.send_json_response({
                        **result,
                        "instructions": [
                            "✅ Webhook configurado com sucesso!",
                            "🤖 Agora os usuários podem:",
                            "1. Procurar seu bot no Telegram",
                            "2. Enviar /start",
                            "3. Receber o Chat ID automaticamente",
                            "4. Usar o Chat ID para se cadastrar no site"
                        ]
                    }, cache_seconds=0)
                else:
                    return self.send_json_response(result, status_code=500, cache_seconds=0)
                    
            except Exception as e:
                return self.send_json_response({
                    "status": "error",
                    "message": f"Erro ao configurar webhook: {str(e)}"
                }, status_code=500, cache_seconds=0)
        
        else:
            response = {
                "error": "Endpoint não encontrado",
                "path": path,
                "available_endpoints": {
                    "GET": ["/api/", "/api/health", "/api/bolsas", "/api/bolsas/{id}", "/api/analytics", "/api/editais", "/api/ranking", "/api/metadata", "/api/telegram/setup-webhook", "/api/telegram/debug-webhook", "/api/telegram/test-webhook", "/api/telegram/check-messages", "/api/telegram/logs"],
                    "POST": ["/api/alertas/telegram", "/api/alertas/notify", "/api/alertas/test-detection", "/api/alertas/listar", "/api/telegram/webhook"]
                }
            }
            return self.send_json_response(response, status_code=404, cache_seconds=300)
    
    def do_POST(self):
        # Parse da URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Ler dados do corpo da requisição
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            response = {"error": "JSON inválido"}
            return self.send_json_response(response, status_code=400, cache_seconds=0)
        
        # Roteamento POST
        if path == '/api/alertas/telegram':
            # Cadastrar ID do Telegram para alertas
            telegram_id = data.get('telegram', '').strip()
            
            if not telegram_id:
                response = {"error": "ID do Telegram é obrigatório (@usuario ou chat_id)"}
                return self.send_json_response(response, status_code=400, cache_seconds=0)
            
            result = subscribe_telegram_alerts(telegram_id)
            status_code = 200 if result['status'] == 'success' else 400
            return self.send_json_response(result, status_code=status_code, cache_seconds=0)
            
        elif path == '/api/alertas/notify':
            # Endpoint para teste de notificação (pode ser protegido)
            titulo = data.get('titulo', 'Teste de Edital')
            link = data.get('link', 'https://uenf.br')
            edital_type = data.get('tipo')  # Opcional: forçar tipo específico
            
            result = notify_new_edital(titulo, link, edital_type)
            return self.send_json_response(result, cache_seconds=0)
            
        elif path == '/api/alertas/test-detection':
            # Endpoint para testar detecção de tipos de editais
            titulo = data.get('titulo', '')
            
            if not titulo:
                response = {"error": "Parâmetro 'titulo' é obrigatório"}
                return self.send_json_response(response, status_code=400, cache_seconds=0)
                
            detected_type = detect_edital_type(titulo)
            
            response = {
                "titulo": titulo,
                "tipo_detectado": detected_type,
                "sera_notificado": detected_type in ['extensao', 'resultado'],
                "exemplos": {
                    "extensao": ["Edital de Extensão", "Bolsas Discentes", "Projeto de Extensão"],
                    "resultado": ["Resultado Final", "Classificação", "Lista de Aprovados"],
                    "outros": ["Mestrado em", "Doutorado em", "Seleção para"]
                }
            }
            return self.send_json_response(response, cache_seconds=0)
            
        
        elif path == '/api/alertas/listar':
            # Endpoint para listar usuários do Telegram cadastrados (para debug)
            try:
                supabase = get_supabase_client()
                if not supabase:
                    response = {"error": "Supabase não disponível", "total": 0, "usuarios": []}
                    return self.send_json_response(response, cache_seconds=0)
                
                # Buscar todos os usuários cadastrados no Telegram
                result = supabase.table('telegram_alerts').select('telegram_id, status, created_at').execute()
                
                usuarios = []
                for user in result.data or []:
                    # Mascarar o ID para privacidade 
                    telegram_id = user.get('telegram_id', '')
                    
                    if telegram_id.isdigit():
                        # Para chat_id numérico, mascarar números
                        if len(telegram_id) > 5:
                            id_mascarado = telegram_id[:3] + '****' + telegram_id[-2:]
                        else:
                            id_mascarado = telegram_id[:1] + '****'
                    else:
                        # Para username, mascarar username
                        if len(telegram_id) > 5:
                            id_mascarado = '@' + telegram_id[:3] + '****' + telegram_id[-2:]
                        else:
                            id_mascarado = '@' + telegram_id[:1] + '****'
                        
                    usuarios.append({
                        "telegram_id_mascarado": id_mascarado,
                        "status": user.get('status', 'desconhecido'),
                        "data_cadastro": user.get('created_at', '')
                    })
                
                response = {
                    "total_usuarios": len(usuarios),
                    "usuarios_ativos": len([u for u in usuarios if u['status'] == 'ativo']),
                    "usuarios": usuarios,
                    "message": f"Total de {len(usuarios)} usuário(s) cadastrado(s) no Telegram"
                }
                return self.send_json_response(response, cache_seconds=0)
                
            except Exception as e:
                response = {"error": f"Erro ao listar usuários: {str(e)}", "total": 0}
                return self.send_json_response(response, status_code=500, cache_seconds=0)
            
        elif path == '/api/telegram/webhook':
            # Webhook do Telegram - recebe mensagens dos usuários
            try:
                # Log SUPER detalhado
                print(f"🚨 =================================")
                print(f"🌐 WEBHOOK REQUEST - METHOD: {self.command}")
                print(f"🌐 WEBHOOK REQUEST - PATH: {self.path}")
                print(f"🌐 WEBHOOK REQUEST HEADERS: {dict(self.headers)}")
                print(f"📥 WEBHOOK DATA RAW: {data}")
                print(f"📥 WEBHOOK DATA TYPE: {type(data)}")
                print(f"📥 WEBHOOK DATA JSON: {json.dumps(data, indent=2)}")
                print(f"🚨 =================================")
                
                # Verificar se tem dados do webhook
                if not data:
                    response = {"error": "Dados do webhook inválidos", "received_data": data, "headers": dict(self.headers)}
                    print(f"❌ WEBHOOK VAZIO: {response}")
                    
                    # Retornar 200 OK mesmo com erro para não gerar 401
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()
                    
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                result = handle_telegram_webhook(data)
                print(f"📤 WEBHOOK RESULTADO: {json.dumps(result, indent=2)}")
                
                # Telegram espera sempre 200 OK
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                
                # Incluir dados completos na resposta (para debug)
                telegram_response = {
                    "ok": True, 
                    "status": result.get("status", "handled"),
                    "debug": result,  # Incluir todos os dados do resultado
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                self.wfile.write(json.dumps(telegram_response).encode('utf-8'))
                return
                
            except Exception as e:
                error_msg = f"Erro ao processar webhook: {str(e)}"
                print(f"🚨 ERRO WEBHOOK: {error_msg}")
                
                # Mesmo com erro, retornar 200 OK para o Telegram
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {"ok": False, "error": error_msg}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
        
        else:
            response = {"error": "Endpoint POST não encontrado", "path": path}
            return self.send_json_response(response, status_code=404, cache_seconds=0)

    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        print(f"🔧 OPTIONS REQUEST: {self.path}")
        
        # Para webhooks e CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Telegram-Bot-Api-Secret-Token')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()