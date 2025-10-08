from supabase import create_client, Client
import os
from dotenv import load_dotenv
import re
import unicodedata
from difflib import get_close_matches
from collections import defaultdict
from typing import Optional
from datetime import datetime, timezone

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
    def __init__(self, supabase_url: str, supabase_key: str):
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

    def _get_match_key(self, text: str) -> str:
        """
        Normalização para COMPARAÇÃO de strings (nomes, etc.).
        Remove acentos, pontuação e normaliza espaços.
        """
        if not isinstance(text, str):
            return ""
        try:
            text_sem_acentos = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
            text_upper = text_sem_acentos.upper()
            text_limpo = re.sub(r'[^\w\s]', '', text_upper)
            return " ".join(text_limpo.split())
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
        base_normalized_text = self._get_match_key(text)
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

    def _registrar_notificacao_enviada(self, edital_id: str, edital_titulo: str, edital_link: str, tipo_edital: str, tipo_notificacao: str, resultado: dict):
        """
        📝 Registra notificação enviada no histórico.
        Permite auditoria e análise de notificações.
        """
        try:
            # Extrai informações do resultado
            status = resultado.get('status', 'desconhecido')
            usuarios_notificados = resultado.get('sent_count', 0)
            
            # Prepara detalhes em JSON
            detalhes = {
                'resultado_completo': resultado,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Determina status da notificação
            status_final = 'enviada' if status in ['success', 'sent'] else ('ignorada' if status == 'skipped' else 'erro')
            
            # Insere no histórico
            self.client.table('notificacoes_enviadas').insert({
                'edital_id': edital_id,
                'edital_titulo': edital_titulo,
                'edital_link': edital_link,
                'tipo_edital': tipo_edital,
                'tipo_notificacao': tipo_notificacao,
                'usuarios_notificados': usuarios_notificados,
                'status': status_final,
                'detalhes': detalhes
            }).execute()
            
            print(f"📝 Histórico atualizado: {status_final} - {usuarios_notificados} usuário(s)")
            
        except Exception as e:
            print(f"⚠️ Erro ao registrar histórico de notificação: {e}")
            # Não falha a operação principal se o log falhar

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
                if edital_id:
                    res_existentes = self.client.table('projetos').select('id, nome_projeto').eq('edital_id', edital_id).execute()
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
                'data_divulgacao_resultado': edital_data.get('data_divulgacao_resultado'),  # NOVO CAMPO
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
                
                # 🔔 NOTIFICAÇÕES TELEGRAM INTELIGENTES
                # ✅ Só notifica se for EDITAL NOVO (evita spam de editais já notificados)
                # ✅ Detecta tipo correto: 'inscricao' ou 'resultado'
                # ✅ Registra em histórico para auditoria
                
                if is_edital_novo:  # ← VERIFICAÇÃO CRÍTICA: Só notifica editais NOVOS
                    try:
                        tipo_edital = edital_data.get('etapa', 'inscricao')  # 'inscricao' ou 'resultado'
                        tipo_notificacao = 'extensao' if tipo_edital == 'inscricao' else 'resultado'
                        
                        # Log da tentativa de notificação
                        print(f"📱 [NOVO EDITAL] Preparando notificação: '{edital_data.get('titulo')}'")
                        print(f"   ├─ Tipo Edital: {tipo_edital}")
                        print(f"   ├─ Tipo Notificação: {tipo_notificacao}")
                        print(f"   └─ Link: {edital_url}")
                        
                        # Chama sistema de notificações
                        from telegram_integration import call_telegram_notifications
                        
                        notification_result = call_telegram_notifications(
                            titulo=edital_data.get('titulo', 'Novo Edital'),
                            link=edital_url,
                            tipo=tipo_notificacao
                        )
                        
                        # Registra no histórico
                        self._registrar_notificacao_enviada(
                            edital_id=final_edital_id,
                            edital_titulo=edital_data.get('titulo'),
                            edital_link=edital_url,
                            tipo_edital=tipo_edital,
                            tipo_notificacao=tipo_notificacao,
                            resultado=notification_result
                        )
                        
                        print(f"✅ Notificação enviada e registrada: {notification_result.get('status', 'unknown')}")
                            
                    except Exception as e:
                        print(f"❌ Erro ao enviar notificação: {e}")
                        # Registra erro no histórico mesmo assim
                        try:
                            self._registrar_notificacao_enviada(
                                edital_id=final_edital_id,
                                edital_titulo=edital_data.get('titulo'),
                                edital_link=edital_url,
                                tipo_edital=edital_data.get('etapa', 'inscricao'),
                                tipo_notificacao='erro',
                                resultado={'status': 'erro', 'message': str(e)}
                            )
                        except:
                            pass  # Se nem o log funcionar, só ignora
                else:
                    print(f"ℹ️ [EDITAL EXISTENTE] Notificação ignorada (já foi notificado): '{edital_data.get('titulo')}'")
                
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
        Atualiza o status das bolsas para 'preenchida' com base nos resultados.
        Lida com orientadores que podem ter múltiplos projetos.
        """
        if not aprovados:
            return 0

        print(f"  > Atualizando status de {len(aprovados)} bolsas com base no resultado...")
        bolsas_atualizadas = 0

        # ETAPA 1: Carregar todos os orientadores do DB para correspondência fuzzy
        todos_orientadores_db = self.get_all_orientadores()
        if not todos_orientadores_db:
            return 0 # Aborta se não houver orientadores para comparar

        # CRIA UM MAPA ONDE UMA CHAVE NORMALIZADA PODE TER MÚLTIPLAS VARIAÇÕES ORIGINAIS (COM ACENTOS DIFERENTES)
        orientador_keys_to_originals = defaultdict(list)
        for o in todos_orientadores_db:
            key = self._get_match_key(o)
            if o not in orientador_keys_to_originals[key]:
                orientador_keys_to_originals[key].append(o)


        for aprovado in aprovados:
            # Processando candidato aprovado
            
            orientador_original = aprovado.get('orientador')
            projeto_original = aprovado.get('nome_projeto')
            
            # CHAVES DE COMPARAÇÃO (sem acentos)
            orientador_key_pdf = self._get_match_key(orientador_original)
            projeto_match_key_pdf = self._get_project_match_key(projeto_original)

            # Tentando correspondência de orientador/projeto

            if not orientador_original or not projeto_original:
                continue

            # ETAPA 2: Correspondência Fuzzy do Nome do Orientador
            # Mapeia a chave de match (sem acento) para o nome original (com acento) do DB
            
            # Compara as chaves sem acento
            matches_keys = get_close_matches(orientador_key_pdf, list(orientador_keys_to_originals.keys()), n=5, cutoff=0.75)
            
            if not matches_keys:
                print(f"  > Aviso: Não foi possível encontrar um orientador correspondente para a chave '{orientador_key_pdf}' no banco de dados. Pulando...", flush=True)
                continue

            # Recupera TODAS as variações originais (com e sem acento) dos orientadores que deram match
            matches_db_orientadores = []
            for key in matches_keys:
                matches_db_orientadores.extend(orientador_keys_to_originals[key])
            
            # Remove duplicatas se houver
            matches_db_orientadores = list(set(matches_db_orientadores))

            # Orientadores similares encontrados

            try:
                # ETAPA 3: Busca os projetos de TODOS os orientadores encontrados (usando o nome com acento do DB)
                response = self.client.table('projetos').select('id, nome_projeto').in_('orientador', matches_db_orientadores).execute()
                projetos_do_orientador = response.data
                
                # Projetos encontrados para os orientadores correspondentes

                best_match_project = None
                
                # --- LÓGICA DE MATCHING RESTAURADA ---
                if projetos_do_orientador:
                    
                    # Camada 1: Busca por correspondência exata primeiro (usando chaves de match)
                    for p_db in projetos_do_orientador:
                        p_db_match_key = self._get_project_match_key(p_db['nome_projeto'])
                        if p_db_match_key == projeto_match_key_pdf:
                            best_match_project = p_db
                            # Match exato encontrado
                            break
                    
                    # Camada 2: Verificação de Substring (usando chaves de match)
                    if not best_match_project:
                        for p_db in projetos_do_orientador:
                            p_db_match_key = self._get_project_match_key(p_db['nome_projeto'])
                            if projeto_match_key_pdf in p_db_match_key:
                                best_match_project = p_db
                                # Match por substring encontrado
                                break

                    # Camada 3: Similaridade de Jaccard (usando chaves de match)
                    if not best_match_project:
                        best_jaccard_match = None
                        highest_score = 0.0
                        projeto_normalizado_words = set(projeto_match_key_pdf.split())
                        for p_db in projetos_do_orientador:
                            db_project_words = set(self._get_project_match_key(p_db['nome_projeto']).split())
                            if not projeto_normalizado_words or not db_project_words: continue
                            
                            intersection = len(projeto_normalizado_words.intersection(db_project_words))
                            union = len(projeto_normalizado_words.union(db_project_words))
                            score = intersection / union if union > 0 else 0
                            
                            if score > highest_score:
                                highest_score = score
                                best_jaccard_match = p_db
                        
                        if highest_score >= 0.6:
                            best_match_project = best_jaccard_match
                            # Match por similaridade Jaccard encontrado


                    # Camada 4: Correspondência "Fuzzy" (usando chaves de match)
                    if not best_match_project:
                        match_map = {self._get_project_match_key(p['nome_projeto']): p for p in projetos_do_orientador}
                        matches = get_close_matches(projeto_match_key_pdf, list(match_map.keys()), n=1, cutoff=0.8)
                        if matches:
                            best_match_project = match_map[matches[0]]
                            # Match fuzzy encontrado

                # 3. Se encontrou um projeto, atualiza a bolsa
                if best_match_project and best_match_project.get('id'):
                    projeto_id = best_match_project['id']
                    numero_perfil = self._normalize_perfil(aprovado.get('numero_perfil'))
                    # Salva o nome do candidato com acentos
                    candidato_aprovado = self._normalize_text_for_db(aprovado.get('candidato_aprovado'))
                    
                    # --- LÓGICA ANTI-DUPLICAÇÃO DE CANDIDATO ---
                    # 1. Busca todos os candidatos já aprovados para este projeto (com acentos)
                    response_candidatos_existentes = self.client.table('bolsas').select('candidato_aprovado').eq('projeto_id', projeto_id).eq('status', 'preenchida').execute()
                    candidatos_existentes_db = [c['candidato_aprovado'] for c in response_candidatos_existentes.data if c.get('candidato_aprovado')]

                    # 2. Compara usando chaves de match (sem acentos)
                    if candidatos_existentes_db:
                        candidato_aprovado_key = self._get_match_key(candidato_aprovado)
                        candidatos_existentes_keys = [self._get_match_key(c) for c in candidatos_existentes_db]
                        matches = get_close_matches(candidato_aprovado_key, candidatos_existentes_keys, n=1, cutoff=0.95)
                        if matches:
                            continue # Pula para o próximo aprovado da lista
                    
                    # --- CORREÇÃO FINAL: Lógica de SELECT-THEN-UPDATE ---
                    # 1. Encontrar UMA bolsa disponível que corresponda aos critérios.
                    select_bolsa_response = self.client.table('bolsas').select('id').eq('projeto_id', projeto_id).eq('numero_perfil', numero_perfil).eq('status', 'disponivel').limit(1).execute()

                    if select_bolsa_response.data:
                        bolsa_id_para_atualizar = select_bolsa_response.data[0]['id']
                        
                        # 2. Atualizar a bolsa específica usando seu ID.
                        update_response = self.client.table('bolsas').update({
                            'status': 'preenchida',
                            'candidato_aprovado': candidato_aprovado
                        }).eq('id', bolsa_id_para_atualizar).execute()
                        
                        if update_response.data:
                            bolsas_atualizadas += 1
                    else:
                        projeto_nome_para_log = self._normalize_text_for_db(projeto_original)
                        print(f"  > Aviso: Nenhuma bolsa disponível encontrada para o projeto '{projeto_nome_para_log}' com perfil '{numero_perfil}'.", flush=True)
                else:
                    # --- INÍCIO DA LÓGICA DE FALLBACK v2 (Mais Segura) ---
                    # Se a correspondência do nome do projeto falhou, verificamos se é seguro usar um fallback.
                    # É seguro APENAS se o orientador tiver UM ÚNICO projeto cadastrado, eliminando ambiguidades.
                    print(f"  > [Fallback] Match de nome falhou. Verificando se o orientador '{orientador_original}' tem apenas um projeto para desambiguação.", flush=True)
                    
                    # Conta quantos projetos o orientador tem no total.
                    count_response = self.client.table('projetos').select('id', count='exact').in_('orientador', matches_db_orientadores).execute()
                    
                    if count_response.count == 1:
                        # SUCESSO SEM AMBIGUIDADE: O orientador só tem 1 projeto, então podemos associar a bolsa a ele.
                        projeto_id = count_response.data[0]['id']
                        numero_perfil = self._normalize_perfil(aprovado.get('numero_perfil'))
                        candidato_aprovado = self._normalize_text_for_db(aprovado.get('candidato_aprovado'))
                        print(f"  > [Fallback] Sucesso! O orientador tem um único projeto (ID: {projeto_id}). Procurando bolsa disponível.", flush=True)

                        # Procura uma bolsa disponível nesse único projeto com o perfil correto.
                        select_bolsa_response = self.client.table('bolsas').select('id').eq('projeto_id', projeto_id).eq('numero_perfil', numero_perfil).eq('status', 'disponivel').limit(1).execute()

                        if select_bolsa_response.data:
                            bolsa_id_para_atualizar = select_bolsa_response.data[0]['id']
                            update_response = self.client.table('bolsas').update({
                                'status': 'preenchida',
                                'candidato_aprovado': candidato_aprovado
                            }).eq('id', bolsa_id_para_atualizar).execute()
                            
                            if update_response.data:
                                bolsas_atualizadas += 1
                        else:
                             print(f"  > [Fallback] Aviso: Nenhuma bolsa disponível encontrada para o projeto único do orientador '{orientador_original}' com perfil '{numero_perfil}'.", flush=True)
                    else:
                        # FALHA FINAL: O orientador tem 0 ou mais de 1 projeto, então não é seguro fazer o fallback.
                        print(f"  > Aviso: Nenhum projeto encontrado para o orientador '{matches_db_orientadores[0] if matches_db_orientadores else orientador_original}' com o nome de projeto '{projeto_original}'. Fallback não aplicado devido a {count_response.count} projetos associados (risco de ambiguidade).", flush=True)
                    # --- FIM DA LÓGICA DE FALLBACK ---

            except Exception as e:
                print(f"  > Erro ao atualizar bolsa para o candidato '{aprovado.get('candidato_aprovado')}': {e}", flush=True)
        
        print(f"  > {bolsas_atualizadas} bolsas foram atualizadas para 'preenchida'.", flush=True)
        
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
                q_normalized = self._get_match_key(q)
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
                    q_normalized = self._get_match_key(q)
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
                q_normalized = self._get_match_key(q)
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
            # Garante que 'data_publicacao' e 'data_divulgacao_resultado' sejam retornados
            query = self.client.table('editais').select(
                'id, titulo, link, data_fim_inscricao, created_at, data_publicacao, data_divulgacao_resultado'
            ).order('data_publicacao', desc=True).range(offset, offset + page_size - 1)
            
            return query.execute().data
        except Exception as e:
            print(f"  > Erro ao buscar editais: {e}")
            return []

    def get_edital(self, edital_id: str):
        """Busca um único edital pelo seu ID."""
        try:
            # Garante que 'data_publicacao' e 'data_divulgacao_resultado' sejam retornados
            return self.client.table('editais').select(
                'id, titulo, link, data_fim_inscricao, created_at, data_publicacao, data_divulgacao_resultado'
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

