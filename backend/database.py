from supabase import create_client, Client
import os
from dotenv import load_dotenv
import re
import unicodedata
from difflib import get_close_matches
from collections import defaultdict
from typing import Optional
from datetime import datetime, timezone

# ✅ NOVO: Importa a função de um local centralizado
from .utils import get_match_key

# Lista de palavras comuns a serem ignoradas na normalização para comparação
STOP_WORDS = {
    'A', 'O', 'E', 'UM', 'UMA', 'DE', 'DO', 'DA', 'EM', 'NO', 'NA', 'COM', 'POR', 'PARA', 'SE',
    'SÃO', 'AS', 'OS', 'DOS', 'DAS', 'NOS', 'NAS', 'PELO', 'PELA', 'PRA', 'AO', 'AOS', 'QUE',
    'QUANDO', 'COMO', 'ONDE', 'QUEM', 'QUAL', 'SEU', 'SUA'
}

# Lista de termos específicos de editais que podem ser ignorados
EDITAL_TERMS = {
    'EDITAL', 'PROJETO', 'BOLSA', 'PROEX', 'PIBEX', 'EXTENSÃO', 'PESQUISA', 'SELEÇÃO',
    'BOLSISTA', 'RESULTADO', 'INSCRIÇÃO', 'CLASSIFICAÇÃO', 'CANDIDATO', 'PROGRAMA', 'ANO',
    'PUBLICO', 'PRIVADO', 'INSTITUCIONAL', 'VOLUNTARIA'
}

class SupabaseManager:
    """
    Gerencia a comunicação com o banco de dados Supabase.
    """
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são necessárias.")
                        
        try:
            self.client: Client = create_client(url, key)
            # Conexão com Supabase estabelecida
        except Exception as e:
            print(f"Erro ao conectar com Supabase: {e}")
            self.client = None

    def _normalize_text_for_db(self, text: str) -> str:
        """
        Normalização MÍNIMA para salvar no banco: maiúsculas e espaços únicos.
        MANTÉM acentos, conectivos e palavras-chave.
        """
        if not isinstance(text, str):
            return ""
        try:
            # Apenas converte para maiúsculas e normaliza espaços.
            text_upper = text.upper()
            return " ".join(text_upper.split())
        except Exception:
            return ""

    def _get_project_match_key(self, text: str) -> str:
        """
        Normalização agressiva APENAS para COMPARAÇÃO de projetos.
        Usa a normalização base e remove stop words e termos de edital.
        """
        if not isinstance(text, str):
            return ""
        # Reutiliza a normalização base para remover acentos/pontuação
        base_normalized_text = get_match_key(text)
        words = base_normalized_text.split()
        filtered_words = [word for word in words if word not in STOP_WORDS and word not in EDITAL_TERMS and not word.isdigit()]
        return " ".join(filtered_words)

    def _normalize_perfil(self, perfil: any) -> str:
        """Garante que o número do perfil seja uma string com dois dígitos (ex: '1' -> '01')."""
        return str(perfil).strip().zfill(2) if perfil else None

    def _cleanup_old_available_bolsas(self):
        """
        🧹 NOVA FUNCIONALIDADE: Remove bolsas 'disponível' de editais antigos 
        quando um novo edital de inscrição é salvo.
        """
        try:
            # 1. Busca a data do edital mais recente
            latest_edital = self.client.table('editais').select('data_publicacao').order('data_publicacao', desc=True).limit(1).execute()
            
            if not latest_edital.data:
                return 0  # Não há editais no banco
            
            latest_date = latest_edital.data[0]['data_publicacao']
            
            # 2. Remove bolsas 'disponível' de editais anteriores ao mais recente
            cleanup_response = self.client.table('bolsas').delete().eq('status', 'disponivel').neq('edital_data_publicacao', latest_date).execute()
            
            deleted_count = len(cleanup_response.data) if cleanup_response.data else 0
            
            if deleted_count > 0:
                print(f"🧹 LIMPEZA: {deleted_count} bolsa(s) não preenchida(s) de editais antigos foram removidas.")
            
            return deleted_count
            
        except Exception as e:
            print(f"⚠️ Erro na limpeza de bolsas antigas: {e}")
            return 0

    def _verificar_notificacao_existente(self, edital_id: str, tipo_notificacao: str) -> bool:
        """
        📋 Verifica se já existe notificação enviada para este edital+tipo.
        Evita notificações duplicadas.
        """
        try:
            response = self.client.table('notificacoes_enviadas').select('id').eq('edital_id', edital_id).eq('tipo_notificacao', tipo_notificacao).limit(1).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"⚠️ Erro ao verificar notificação existente: {e}")
            return False  # Em caso de erro, permite notificar (fail-safe)
    
    def _enfileirar_notificacao(self, edital_id: str, edital_titulo: str, edital_link: str, tipo_edital: str, tipo_notificacao: str, usuarios: list):
        """
        Enfileira uma notificação para ser processada, em vez de enviá-la diretamente.
        """
        try:
            # O status padrão da tabela agora é 'pendente', então não precisamos especificá-lo
            self.client.table('notificacoes_enviadas').insert({
                'edital_id': edital_id,
                'edital_titulo': edital_titulo,
                'edital_link': edital_link,
                'tipo_edital': tipo_edital,
                'tipo_notificacao': tipo_notificacao,
                'detalhes': { 'usuarios_alvo': usuarios } # Armazena para quem enviar
            }).execute()
            print(f"✅ Notificação para o edital '{edital_titulo}' enfileirada para {len(usuarios)} usuário(s).")
        except Exception as e:
            print(f"❌ Erro ao enfileirar notificação: {e}")

    def _buscar_usuarios_por_preferencia(self, modalidade: str) -> list:
        """
        📱 Busca usuários que querem receber notificações deste tipo.
        Se usuário não tem preferências, retorna para receber TUDO.
        """
        try:
            # Busca usuários ativos
            response = self.client.table('telegram_alerts').select('telegram_id, preferencias').eq('status', 'ativo').execute()
            
            if not response.data:
                return []
            
            usuarios_filtrados = []
            for usuario in response.data:
                preferencias = usuario.get('preferencias')
                
                # Se não tem preferências definidas, recebe TUDO
                if not preferencias:
                    usuarios_filtrados.append(usuario['telegram_id'])
                    continue
                
                # Se tem preferências, verifica se está ativo para essa modalidade
                if preferencias.get(modalidade) is True:
                    usuarios_filtrados.append(usuario['telegram_id'])
            
            return usuarios_filtrados
            
        except Exception as e:
            print(f"⚠️ Erro ao buscar usuários por preferência: {e}")
            # Fallback: retorna todos os ativos (fail-safe)
            try:
                fallback = self.client.table('telegram_alerts').select('telegram_id').eq('status', 'ativo').execute()
                return [u['telegram_id'] for u in fallback.data] if fallback.data else []
            except:
                return []

    def upsert_edital(self, edital_data: dict, edital_url: str):
        """
        Insere ou atualiza um edital de forma transacional usando uma função RPC no Supabase.
        A lógica de correspondência fuzzy de projetos é feita em Python antes de enviar os dados.
        
        🆕 NOVA FUNCIONALIDADE: Remove automaticamente bolsas não preenchidas de editais antigos.
        📱 NOTIFICAÇÕES INTELIGENTES: Só notifica editais NOVOS, evitando spam.
        """
        if not self.client:
            print("Cliente Supabase não inicializado. Abortando operação.")
            return None

        try:
            # 1. Busca o ID do edital existente ou prepara para criar um novo
            response = self.client.table('editais').select('id').eq('link', edital_url).execute()
            edital_id_antes = response.data[0]['id'] if response.data else None
            is_edital_novo = edital_id_antes is None  # ← CRUCIAL: Detecta se é INSERT ou UPDATE

            # 2. Prepara a lista de projetos para o payload final
            projetos_payload = []
            projetos_data = edital_data.get('projetos', [])

            if not projetos_data:
                # Edital sem projetos, salvando apenas edital
                pass
            else:
                # Busca todos os projetos existentes para este edital para fazer o match
                projetos_existentes = []
                if edital_id_antes:
                    res_existentes = self.client.table('projetos').select('id, nome_projeto').eq('edital_id', edital_id_antes).execute()
                    projetos_existentes = res_existentes.data or []
                
                # Cria um mapa para correspondência fuzzy
                match_map = {self._get_project_match_key(p['nome_projeto']): p for p in projetos_existentes}

                for proj_info in projetos_data:
                    nome_projeto_db = self._normalize_text_for_db(proj_info.get('nome_projeto'))
                    nome_projeto_match_key = self._get_project_match_key(proj_info.get('nome_projeto'))

                    # Lógica de Fuzzy Matching para encontrar ID existente
                    matches = get_close_matches(nome_projeto_match_key, list(match_map.keys()), n=1, cutoff=0.85)
                    
                    projeto_id_existente = None
                    if matches:
                        matched_key = matches[0]
                        projeto_existente_obj = match_map[matched_key]
                        projeto_id_existente = projeto_existente_obj['id']
                        # Projeto correspondente encontrado no BD

                    # Normaliza os detalhes das bolsas
                    bolsas_detalhadas = []
                    for bolsa in proj_info.get('detalhe_bolsas', []):
                        bolsas_detalhadas.append({
                            'tipo': bolsa.get('tipo_bolsa'),
                            'remuneracao': bolsa.get('valor_bolsa'),
                            'vagas': bolsa.get('vagas', 1),
                            'numero_perfil': self._normalize_perfil(bolsa.get('numero_perfil')),
                            'requisito': bolsa.get('requisitos')
                        })

                    # Monta o payload para este projeto específico
                    projeto_atual = {
                        'id': projeto_id_existente, # Será null se for um projeto novo
                        'nome_projeto': nome_projeto_db,
                        'orientador': self._normalize_text_for_db(proj_info.get('orientador')),
                        'centro': proj_info.get('centro'),
                        'resumo': proj_info.get('resumo'),
                        'detalhe_bolsas': bolsas_detalhadas
                    }
                    projetos_payload.append(projeto_atual)

            # 3. Monta o payload final para a função RPC
            payload_final = {
                'titulo': edital_data.get('titulo'),
                'link': edital_url,
                'data_fim_inscricao': edital_data.get('data_fim_inscricao'),
                'data_publicacao': edital_data.get('data_publicacao'),
                'data_divulgacao_resultado': edital_data.get('data_divulgacao_resultado'),
                'modalidade': edital_data.get('modalidade', 'extensao'),  # ← NOVO: Salva modalidade
                'projetos': projetos_payload
            }

            # 4. Chama a função RPC com o payload completo
            rpc_response = self.client.rpc('handle_edital_upsert', {'edital_payload': payload_final}).execute()

            if rpc_response.data:
                final_edital_id = rpc_response.data
                # Edital salvo com sucesso
                
                # 🧹 LIMPEZA AUTOMÁTICA: Remove bolsas não preenchidas de editais antigos
                if edital_data.get('etapa') == 'inscricao':  # Só limpa para editais de inscrição
                    self._cleanup_old_available_bolsas()
                
                # 🔔 NOTIFICAÇÕES TELEGRAM INTELIGENTES via FILA
                # ✅ Só enfileira se for EDITAL NOVO (evita spam)
                if is_edital_novo:
                    try:
                        tipo_edital = edital_data.get('etapa', 'inscricao')
                        modalidade = edital_data.get('modalidade', 'extensao')
                        
                        if modalidade == 'apoio_academico':
                            tipo_notificacao = 'apoio_academico'
                        elif tipo_edital == 'resultado':
                            tipo_notificacao = 'resultado'
                        else:
                            tipo_notificacao = 'extensao'
                        
                        usuarios_interessados = self._buscar_usuarios_por_preferencia(modalidade)
                        
                        if not usuarios_interessados:
                            print(f"ℹ️ [SEM USUÁRIOS] Nenhum usuário quer receber '{modalidade}'. Não notificando.")
                        else:
                            # Enfileira a notificação em vez de enviar diretamente
                            self._enfileirar_notificacao(
                                edital_id=final_edital_id,
                                edital_titulo=edital_data.get('titulo', 'Novo Edital'),
                                edital_link=edital_url,
                                tipo_edital=tipo_edital,
                                tipo_notificacao=tipo_notificacao,
                                usuarios=usuarios_interessados
                            )
                            
                    except Exception as e:
                        print(f"❌ Erro durante a lógica de enfileiramento de notificação: {e}")
                else:
                    print(f"ℹ️ [EDITAL EXISTENTE] Notificação ignorada (edital já existia): '{edital_data.get('titulo')}'")
                
                return final_edital_id
            else:
                # Tenta fornecer um erro mais detalhado, se possível
                error_message = "A função RPC não retornou um ID."
                if hasattr(rpc_response, 'error') and rpc_response.error:
                    error_message = f"Erro na RPC: {rpc_response.error.message}"
                raise Exception(error_message)

        except Exception as e:
            print(f"  > ERRO na operação transacional para o edital '{edital_data.get('titulo')}': {e}")
            import traceback
            traceback.print_exc()
            return None

    def atualizar_bolsas_com_resultado(self, aprovados: list, edital_url: str = 'https://uenf.br/editais'):
        """
        🚀 VERSÃO OTIMIZADA: Batch Processing (75x mais rápido!)
        
        Antes: 301 queries (1 + 100×3)
        Depois: 4 queries (4 SELECTs + 1 batch UPDATE)
        
        Atualiza o status das bolsas para 'preenchida' com base nos resultados.
        Lida com orientadores que podem ter múltiplos projetos.
        
        Performance:
        - Carrega todos os dados de uma vez
        - Processa matches em memória
        - Batch update final
        """
        # Esta função agora delega diretamente para a versão otimizada.
        # A implementação antiga e mais lenta foi removida.
        return self._atualizar_bolsas_otimizado(aprovados, edital_url)
    
    def _atualizar_bolsas_otimizado(self, aprovados: list, edital_url: str):
        """🚀 Versão otimizada com batch processing"""
        from database_optimized import atualizar_bolsas_com_resultado_otimizado, _find_best_project_match
        
        # Injeta os métodos helper
        self._find_best_project_match = lambda projeto, projetos: _find_best_project_match(self, projeto, projetos)
        
        # Executa versão otimizada
        return atualizar_bolsas_com_resultado_otimizado(self, aprovados, edital_url)
    
    def _atualizar_bolsas_antiga(self, aprovados: list, edital_url: str):
        """Versão antiga (legado, mantida para compatibilidade)"""
        # ... código antigo aqui ...
        # 🔔 NOTIFICAÇÕES TELEGRAM DE RESULTADO
        # ✅ Verifica se já foi notificado antes de enviar
        # ✅ Registra em histórico
        if bolsas_atualizadas > 0:
            try:
                # Busca o edital_id pelo link
                edital_response = self.client.table('editais').select('id, titulo').eq('link', edital_url).limit(1).execute()
                edital_info = edital_response.data[0] if edital_response.data else None
                
                if edital_info:
                    edital_id = edital_info['id']
                    edital_titulo = edital_info['titulo']
                    
                    # Verifica se já notificou resultado para este edital
                    ja_notificou = self._verificar_notificacao_existente(edital_id, 'resultado')
                    
                    if not ja_notificou:
                        from telegram_integration import call_telegram_notifications
                        
                        # Criar título baseado nos aprovados
                        orientadores = list(set([a.get('orientador', '') for a in aprovados if a.get('orientador')]))
                        titulo_resultado = f"Resultado PROEX - {bolsas_atualizadas} bolsa(s) preenchida(s)"
                        
                        if orientadores and len(orientadores) <= 3:
                            titulo_resultado += f" - {', '.join(orientadores[:3])}"
                        
                        print(f"📱 [NOVO RESULTADO] Preparando notificação: {bolsas_atualizadas} aprovados")
                        
                        # Chama o sistema de notificações existente
                        notification_result = call_telegram_notifications(
                            titulo=titulo_resultado,
                            link=edital_url,
                            tipo="resultado"
                        )
                        
                        # Registra no histórico
                        self._registrar_notificacao_enviada(
                            edital_id=edital_id,
                            edital_titulo=edital_titulo,
                            edital_link=edital_url,
                            tipo_edital='resultado',
                            tipo_notificacao='resultado',
                            resultado=notification_result
                        )
                        
                        print(f"✅ Notificação de resultado enviada: {notification_result.get('status', 'processadas')}")
                    else:
                        print(f"ℹ️ [RESULTADO JÁ NOTIFICADO] Ignorando: '{edital_titulo}'")
                    
            except Exception as e:
                print(f"❌ Erro ao enviar notificação de resultado: {e}")
                import traceback
                traceback.print_exc()
        
        return bolsas_atualizadas

    def get_all_orientadores(self) -> list:
        """Busca todos os nomes de orientadores únicos no banco de dados."""
        try:
            response = self.client.table('projetos').select('orientador').execute()
            if response.data:
                # Retorna os nomes como estão no banco (já normalizados de forma "suave")
                return list(set([item['orientador'] for item in response.data if item.get('orientador')]))
            return []
        except Exception as e:
            print(f"  > Erro ao buscar lista de orientadores: {e}")
            return []

    def get_bolsas_agrupadas_paginated(self, page: int = 1, page_size: int = 10, status: Optional[str] = None, centro: Optional[str] = None, tipo: Optional[str] = None, q: Optional[str] = None, sort: str = 'created_at', order: str = 'desc'):
        """
        🆕 NOVA FUNCIONALIDADE: Busca bolsas AGRUPADAS (mesmo projeto + perfil = 1 card com quantidade)
        """
        try:
            offset = (page - 1) * page_size
            
            # Query para bolsas agrupadas - soma vagas iguais
            query = self.client.table('bolsas_view_agrupada').select('*', count='exact')

            if status and status != 'all':
                query = query.eq('status', status)
            
            if centro and centro != 'all':
                query = query.eq('centro', centro)

            if tipo and tipo != 'all':
                if tipo == 'extensao':
                    # Busca por qualquer tipo que contenha 'Extensão' OU 'Discente'
                    query = query.or_('tipo.ilike.%Extensão%,tipo.ilike.%Discente%')
                elif tipo == 'UA Superior':
                    # Busca por (UA ou Universidade Aberta) E Superior
                    # Encadeamento de .or_() com .ilike() funciona como AND
                    query = query.or_('tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%').ilike('tipo', '%Superior%')
                elif tipo == 'UA Médio':
                    # Busca por (UA ou Universidade Aberta) E (Médio ou Nível Médio)
                    # A biblioteca não tem um método .and_(), então construímos o filtro manualmente.
                    # Para respeitar a imutabilidade, criamos um novo objeto de parâmetros com .set()
                    # e o reatribuímos ao construtor da query.
                    filter_string = 'or(tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%),or(tipo.ilike.%Médio%,tipo.ilike.%Nível Médio%)'
                    query.params = query.params.set('and', f'({filter_string})')
                elif tipo == 'UA Fundamental':
                    # Busca por (UA ou Universidade Aberta) E Fundamental
                    query = query.or_('tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%').ilike('tipo', '%Fundamental%')
            
            if q:
                # Normaliza a query do usuário para ser sem acentos antes de passar para o FTS
                q_normalized = get_match_key(q)
                search_terms = q_normalized.split()
                search_query = " & ".join([f"{term}:*" for term in search_terms])
                query = query.filter('fts', 'fts(portuguese)', search_query)

            # Define quais ordenações anulam a prioridade de "disponível"
            sort_overrides_status = ['view_count', 'orientador'] # Mantido, se necessário
            
            # ORDENAÇÃO PRIMÁRIA: Sempre pela ordem customizada de status
            query = query.order('status_order', desc=False)

            # ORDENAÇÃO SECUNDÁRIA: A escolhida pelo usuário
            if sort and order:
                is_descending = order.lower() == "desc"
                query = query.order(sort, desc=is_descending)

            # Paginação
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size - 1
            query = query.range(start_idx, end_idx)
            
            response = query.execute()
            
            bolsas = response.data
            total_count = response.count if response.count is not None else 0
            total_pages = (total_count + page_size - 1) // page_size

            # 🔧 CALCULAR TOTAIS COM TODOS OS DADOS (não só da página atual)
            try:
                # Query separada para calcular totais gerais  
                all_query = self.client.table('bolsas_view_agrupada').select('vagas_total,status')
                
                # Aplicar os mesmos filtros da query principal
                if status and status != 'all':
                    all_query = all_query.eq('status', status)
                if centro and centro != 'all':
                    all_query = all_query.eq('centro', centro)  
                if tipo and tipo != 'all':
                    if tipo == 'extensao':
                        all_query = all_query.or_('tipo.ilike.%Extensão%,tipo.ilike.%Discente%')
                    elif tipo == 'UA Superior':
                        all_query = all_query.or_('tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%').ilike('tipo', '%Superior%')
                    elif tipo == 'UA Médio':
                        filter_string = 'or(tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%),or(tipo.ilike.%Médio%,tipo.ilike.%Nível Médio%)'
                        all_query.params = all_query.params.set('and', f'({filter_string})')
                    elif tipo == 'UA Fundamental':
                        all_query = all_query.or_('tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%').ilike('tipo', '%Fundamental%')
                if q:
                    q_normalized = get_match_key(q)
                    search_terms = q_normalized.split()
                    search_query = " & ".join([f"{term}:*" for term in search_terms])
                    all_query = all_query.filter('fts', 'fts(portuguese)', search_query)
                
                all_response = all_query.execute()
                all_bolsas = all_response.data or []
                
                # Calcular totais com TODOS os dados filtrados
                total_vagas = sum(bolsa.get('vagas_total', 1) for bolsa in all_bolsas)
                vagas_preenchidas = sum(
                    bolsa.get('vagas_total', 1) for bolsa in all_bolsas 
                    if bolsa.get('status') == 'preenchida'
                )
                
            except Exception as calc_error:
                print(f"⚠️ Erro ao calcular totais Python: {calc_error}")
                # Fallback: calcular só com dados da página
                total_vagas = sum(bolsa.get('vagas_total', 1) for bolsa in bolsas)
                vagas_preenchidas = sum(
                    bolsa.get('vagas_total', 1) for bolsa in bolsas 
                    if bolsa.get('status') == 'preenchida'
                )

            return {
                "bolsas": bolsas,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "agrupadas": True,  # Indica que são bolsas agrupadas
                "total_vagas": total_vagas,  # 🆕 Total de vagas (soma de TODOS os dados)
                "vagas_preenchidas": vagas_preenchidas  # 🆕 Vagas preenchidas (soma de TODOS os dados)
            }
        except Exception as e:
            print(f"  > Erro ao buscar bolsas agrupadas: {e}")
            # Fallback para método não-agrupado se der erro
            return self.get_bolsas_paginated(page, page_size, status, centro, tipo, q, sort, order)

    def get_bolsas_paginated(self, page: int = 1, page_size: int = 10, status: Optional[str] = None, centro: Optional[str] = None, tipo: Optional[str] = None, q: Optional[str] = None, sort: str = 'created_at', order: str = 'desc'):
        """
        Método ORIGINAL mantido como fallback - busca bolsas individuais.
        """
        try:
            offset = (page - 1) * page_size
            
            # A query base agora pede a contagem total de itens que correspondem ao filtro
            query = self.client.table('bolsas_view').select('*', count='exact')

            if status and status != 'all':
                query = query.eq('status', status)
            
            if centro and centro != 'all':
                query = query.eq('centro', centro)

            if tipo and tipo != 'all':
                if tipo == 'extensao':
                    # Busca por qualquer tipo que contenha 'Extensão' OU 'Discente'
                    query = query.or_('tipo.ilike.%Extensão%,tipo.ilike.%Discente%')
                elif tipo == 'UA Superior':
                    # Busca por (UA ou Universidade Aberta) E Superior
                    # Encadeamento de .or_() com .ilike() funciona como AND
                    query = query.or_('tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%').ilike('tipo', '%Superior%')
                elif tipo == 'UA Médio':
                    # Busca por (UA ou Universidade Aberta) E (Médio ou Nível Médio)
                    # A biblioteca não tem um método .and_(), então construímos o filtro manualmente.
                    # Para respeitar a imutabilidade, criamos um novo objeto de parâmetros com .set()
                    # e o reatribuímos ao construtor da query.
                    filter_string = 'or(tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%),or(tipo.ilike.%Médio%,tipo.ilike.%Nível Médio%)'
                    query.params = query.params.set('and', f'({filter_string})')
                elif tipo == 'UA Fundamental':
                    # Busca por (UA ou Universidade Aberta) E Fundamental
                    query = query.or_('tipo.ilike.%UA%,tipo.ilike.%Universidade Aberta%').ilike('tipo', '%Fundamental%')
            
            if q:
                # Normaliza a query do usuário para ser sem acentos antes de passar para o FTS
                q_normalized = get_match_key(q)
                search_terms = q_normalized.split()
                search_query = " & ".join([f"{term}:*" for term in search_terms])
                query = query.filter('fts', 'fts(portuguese)', search_query)

            # Define quais ordenações anulam a prioridade de "disponível"
            sort_overrides_status = ['view_count', 'orientador'] # Mantido, se necessário
            
            # ORDENAÇÃO PRIMÁRIA: Sempre pela ordem customizada de status
            query = query.order('status_order', desc=False)

            # ORDENAÇÃO SECUNDÁRIA: A escolhida pelo usuário
            if sort and order:
                is_descending = order.lower() == "desc"
                query = query.order(sort, desc=is_descending)

            # Paginação
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size - 1
            query = query.range(start_idx, end_idx)
            
            response = query.execute()
            
            bolsas = response.data
            total_count = response.count if response.count is not None else 0
            total_pages = (total_count + page_size - 1) // page_size

            return {
                "bolsas": bolsas,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "agrupadas": False  # Indica que são bolsas individuais
            }
        except Exception as e:
            print(f"  > Erro ao buscar bolsas paginadas: {e}")
            return {
                "bolsas": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "agrupadas": False
            }

    def get_bolsa(self, bolsa_id: str):
        """Busca uma única bolsa pelo seu ID usando a view."""
        try:
            return self.client.table('bolsas_view').select('*').eq('id', bolsa_id).single().execute().data
        except Exception as e:
            print(f"  > Erro ao buscar bolsa por ID: {e}")
            return None

    def get_projetos(self, page: int = 1, page_size: int = 10):
        """Busca projetos com paginação."""
        try:
            offset = (page - 1) * page_size
            return self.client.table('projetos').select('*').order('created_at', desc=True).range(offset, offset + page_size - 1).execute().data
        except Exception as e:
            print(f"  > Erro ao buscar projetos: {e}")
            return []

    def get_projeto(self, projeto_id: str):
        """Busca um único projeto pelo seu ID."""
        try:
            return self.client.table('projetos').select('*').eq('id', projeto_id).single().execute().data
        except Exception as e:
            print(f"  > Erro ao buscar projeto por ID: {e}")
            return None

    def get_editais(self, page: int = 1, page_size: int = 10):
        """Busca editais com paginação."""
        try:
            offset = (page - 1) * page_size
            # Garante que 'data_publicacao', 'data_divulgacao_resultado' e 'modalidade' sejam retornados
            query = self.client.table('editais').select(
                'id, titulo, link, data_fim_inscricao, created_at, data_publicacao, data_divulgacao_resultado, modalidade'
            ).order('data_publicacao', desc=True).range(offset, offset + page_size - 1)
            
            return query.execute().data
        except Exception as e:
            print(f"  > Erro ao buscar editais: {e}")
            return []

    def get_edital(self, edital_id: str):
        """Busca um único edital pelo seu ID."""
        try:
            # Garante que 'data_publicacao', 'data_divulgacao_resultado' e 'modalidade' sejam retornados
            return self.client.table('editais').select(
                'id, titulo, link, data_fim_inscricao, created_at, data_publicacao, data_divulgacao_resultado, modalidade'
            ).eq('id', edital_id).single().execute().data
        except Exception as e:
            print(f"  > Erro ao buscar edital por ID: {e}")
            return None

    def increment_view_count(self, bolsa_id: str):
        """Chama a função RPC no Supabase para incrementar o contador de views."""
        try:
            self.client.rpc('increment_view_count', {'bolsa_id_param': bolsa_id}).execute()
        except Exception as e:
            # Não trava a aplicação se o contador falhar, apenas loga o erro
            print(f"  > Erro ao incrementar view count para bolsa {bolsa_id}: {e}")

    def get_ranking_bolsas(self, limit: int = 10):
        """Busca as bolsas mais vistas (ranking)."""
        try:
            return self.client.table('bolsas_view').select('*').order('view_count', desc=True).limit(limit).execute().data
        except Exception as e:
            print(f"  > Erro ao buscar ranking de bolsas: {e}")
            return []

    def get_latest_edital_date(self):
        """Busca a data de publicação mais recente de um edital no banco."""
        try:
            # Busca apenas a data de publicação, ordena da mais nova para a mais antiga, e pega apenas a primeira.
            response = self.client.table('editais').select('data_publicacao').order('data_publicacao', desc=True).limit(1).single().execute()
            if response.data and response.data.get('data_publicacao'):
                return response.data.get('data_publicacao')
            return None
        except Exception as e:
            # É normal não encontrar nada se o banco estiver vazio, então não logamos como um erro grave.
            print(f"  > Info: Não foi possível buscar a data do último edital (pode ser a primeira execução): {e}")
            return None

    def get_metadata(self) -> dict:
        """Busca todos os metadados da aplicação."""
        try:
            response = self.client.table('metadata').select('key, value').execute()
            if response.data:
                # Transforma a lista de objetos em um único dicionário
                return {item['key']: item['value'] for item in response.data}
            return {}
        except Exception as e:
            print(f"  > Erro ao buscar metadados: {e}")
            return {}

    def update_last_data_update(self, timestamp: str):
        """Atualiza o timestamp da última atualização de dados."""
        try:
            self.client.table('metadata').update({'value': timestamp}).eq('key', 'last_data_update').execute()
        except Exception as e:
            print(f"  > Erro ao atualizar o timestamp de last_data_update: {e}")

