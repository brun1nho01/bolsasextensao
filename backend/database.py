from supabase import create_client, Client
import os
from dotenv import load_dotenv
import re
import unicodedata
from difflib import get_close_matches
from collections import defaultdict
from typing import Optional

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
            print("Conexão com Supabase estabelecida com sucesso.")
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

    def upsert_edital(self, edital_data: dict, edital_url: str):
        """
        Insere ou atualiza um edital de forma transacional usando uma função RPC no Supabase.
        A lógica de correspondência fuzzy de projetos é feita em Python antes de enviar os dados.
        """
        if not self.client:
            print("Cliente Supabase não inicializado. Abortando operação.")
            return None

        try:
            # 1. Busca o ID do edital existente ou prepara para criar um novo
            response = self.client.table('editais').select('id').eq('link', edital_url).execute()
            edital_id = response.data[0]['id'] if response.data else None

            # 2. Prepara a lista de projetos para o payload final
            projetos_payload = []
            projetos_data = edital_data.get('projetos', [])

            if not projetos_data:
                print(f"  > Edital '{edital_data.get('titulo')}' não continha projetos. Apenas o edital será salvo/atualizado.")
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
                        print(f"  [DB-MATCH] Projeto '{nome_projeto_db}' corresponde ao projeto existente ID: {projeto_id_existente}")

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
                'projetos': projetos_payload
            }

            # 4. Chama a função RPC com o payload completo
            print(f"  > Enviando payload para a função RPC 'handle_edital_upsert'...")
            rpc_response = self.client.rpc('handle_edital_upsert', {'edital_payload': payload_final}).execute()

            if rpc_response.data:
                final_edital_id = rpc_response.data
                print(f"  > Sucesso! Edital '{edital_data.get('titulo')}' e seus projetos foram salvos de forma transacional. ID: {final_edital_id}")
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

    def atualizar_bolsas_com_resultado(self, aprovados: list):
        """
        Atualiza o status das bolsas para 'preenchida' com base nos resultados.
        Lida com orientadores que podem ter múltiplos projetos.
        """
        if not aprovados:
            return 0

        print(f"  > Atualizando status de {len(aprovados)} bolsas com base no resultado...")
        bolsas_atualizadas = 0

        # ETAPA 1: Carregar todos os orientadores do DB para correspondência fuzzy
        print("  [DB-UPDATE] Carregando todos os orientadores do banco de dados para correspondência...", flush=True)
        todos_orientadores_db = self.get_all_orientadores()
        if not todos_orientadores_db:
            print("  > Aviso: Não foi possível carregar a lista de orientadores. A correspondência de nomes pode falhar.", flush=True)
            return 0 # Aborta se não houver orientadores para comparar

        # CRIA UM MAPA ONDE UMA CHAVE NORMALIZADA PODE TER MÚLTIPLAS VARIAÇÕES ORIGINAIS (COM ACENTOS DIFERENTES)
        orientador_keys_to_originals = defaultdict(list)
        for o in todos_orientadores_db:
            key = self._get_match_key(o)
            if o not in orientador_keys_to_originals[key]:
                orientador_keys_to_originals[key].append(o)


        for aprovado in aprovados:
            # NOVO DEBUG: Imprime o registro que está sendo processado
            print(f"\n--- Processando: {aprovado.get('candidato_aprovado')} / {aprovado.get('orientador')} ---", flush=True)
            
            orientador_original = aprovado.get('orientador')
            projeto_original = aprovado.get('nome_projeto')
            
            # CHAVES DE COMPARAÇÃO (sem acentos)
            orientador_key_pdf = self._get_match_key(orientador_original)
            projeto_match_key_pdf = self._get_project_match_key(projeto_original)

            # [NOVO DEBUG] Adicionado para ver os dados originais do resultado
            print(f"  [DB-UPDATE] Tentando match para Chave Orientador: '{orientador_key_pdf}' | Chave Projeto: '{projeto_match_key_pdf}'")

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

            print(f"  [DB-UPDATE] Orientadores com alta similaridade encontrados: {matches_db_orientadores}", flush=True)

            try:
                # ETAPA 3: Busca os projetos de TODOS os orientadores encontrados (usando o nome com acento do DB)
                response = self.client.table('projetos').select('id, nome_projeto').in_('orientador', matches_db_orientadores).execute()
                projetos_do_orientador = response.data
                
                # [NOVO DEBUG] Adicionado para ver o que o DB retornou
                print(f"  [DB-UPDATE] Total de projetos encontrados para os orientadores correspondentes: {len(projetos_do_orientador)}")
                if projetos_do_orientador:
                    # Imprime os nomes dos projetos encontrados para facilitar a depuração
                    for p in projetos_do_orientador:
                        print(f"    - Projeto no DB: '{p.get('nome_projeto')}' (ID: {p.get('id')})")

                best_match_project = None
                
                # --- LÓGICA DE MATCHING RESTAURADA ---
                if projetos_do_orientador:
                    
                    # Camada 1: Busca por correspondência exata primeiro (usando chaves de match)
                    for p_db in projetos_do_orientador:
                        p_db_match_key = self._get_project_match_key(p_db['nome_projeto'])
                        if p_db_match_key == projeto_match_key_pdf:
                            best_match_project = p_db
                            print(f"  [DB-UPDATE-MATCH] Sucesso (Camada 1: Match Exato) com '{p_db['nome_projeto']}'")
                            break
                    
                    # Camada 2: Verificação de Substring (usando chaves de match)
                    if not best_match_project:
                        for p_db in projetos_do_orientador:
                            p_db_match_key = self._get_project_match_key(p_db['nome_projeto'])
                            if projeto_match_key_pdf in p_db_match_key:
                                best_match_project = p_db
                                print(f"  [DB-UPDATE-MATCH] Sucesso (Camada 2: Substring) com '{p_db['nome_projeto']}'")
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
                            print(f"  [DB-UPDATE-MATCH] Sucesso (Camada 3: Jaccard Score {highest_score:.2f}) com '{best_match_project['nome_projeto']}'")


                    # Camada 4: Correspondência "Fuzzy" (usando chaves de match)
                    if not best_match_project:
                        match_map = {self._get_project_match_key(p['nome_projeto']): p for p in projetos_do_orientador}
                        matches = get_close_matches(projeto_match_key_pdf, list(match_map.keys()), n=1, cutoff=0.8)
                        if matches:
                            best_match_project = match_map[matches[0]]
                            print(f"  [DB-UPDATE-MATCH] Sucesso (Camada 4: Fuzzy) com '{best_match_project['nome_projeto']}'")

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
                            print(f"  > [DB-UPDATE] Candidato com chave '{candidato_aprovado_key}' já consta como aprovado para este projeto. Pulando para evitar duplicatas.", flush=True)
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

    def get_bolsas_paginated(self, page: int = 1, page_size: int = 10, status: Optional[str] = None, centro: Optional[str] = None, tipo: Optional[str] = None, q: Optional[str] = None, sort: str = 'created_at', order: str = 'desc'):
        """
        Busca bolsas no banco de dados com filtros, paginação e ordenação, retornando também o total.
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
                "total_pages": total_pages
            }
        except Exception as e:
            print(f"  > Erro ao buscar bolsas paginadas: {e}")
            return {
                "bolsas": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
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
            # Garante que 'data_publicacao' seja retornado e ordena pela data de publicação real
            query = self.client.table('editais').select(
                'id, titulo, link, data_fim_inscricao, created_at, data_publicacao'
            ).order('data_publicacao', desc=True).range(offset, offset + page_size - 1)
            
            return query.execute().data
        except Exception as e:
            print(f"  > Erro ao buscar editais: {e}")
            return []

    def get_edital(self, edital_id: str):
        """Busca um único edital pelo seu ID."""
        try:
            # Garante que 'data_publicacao' seja retornado
            return self.client.table('editais').select(
                'id, titulo, link, data_fim_inscricao, created_at, data_publicacao'
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
            print(f"  > Timestamp de 'last_data_update' atualizado para: {timestamp}")
        except Exception as e:
            print(f"  > Erro ao atualizar o timestamp de last_data_update: {e}")

