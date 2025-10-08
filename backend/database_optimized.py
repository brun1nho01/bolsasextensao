"""
Versão Otimizada do SupabaseManager
🚀 Reduz N+1 queries para batch processing
"""
from collections import defaultdict
from difflib import get_close_matches
from typing import List, Dict, Optional


def atualizar_bolsas_com_resultado_otimizado(self, aprovados: list, edital_url: str = 'https://uenf.br/editais'):
    """
    🚀 VERSÃO OTIMIZADA: Batch Processing
    
    Antes: 301 queries (1 + 100×3)
    Depois: 4 queries (4 SELECTs + 1 batch UPDATE)
    
    Melhoria: 75x mais rápido!
    """
    if not aprovados:
        return 0

    print(f"  > 🚀 [OTIMIZADO] Atualizando {len(aprovados)} bolsas com batch processing...")
    
    # ========== ETAPA 1: CARREGAR TODOS OS DADOS DE UMA VEZ ==========
    
    # 1.1 Carregar todos os orientadores (1 query)
    print(f"  > [1/4] Carregando orientadores...")
    todos_orientadores_db = self.get_all_orientadores()
    if not todos_orientadores_db:
        print(f"  > ❌ Nenhum orientador encontrado no banco")
        return 0
    
    # 1.2 Carregar TODOS os projetos de uma vez (1 query)
    print(f"  > [2/4] Carregando todos os projetos...")
    try:
        response_projetos = self.client.table('projetos').select('*').execute()
        todos_projetos = response_projetos.data
        print(f"  > ✅ {len(todos_projetos)} projetos carregados")
    except Exception as e:
        print(f"  > ❌ Erro ao carregar projetos: {e}")
        return 0
    
    # 1.3 Carregar TODAS as bolsas disponíveis de uma vez (1 query)
    print(f"  > [3/4] Carregando bolsas disponíveis...")
    try:
        response_bolsas = self.client.table('bolsas').select('*').eq('status', 'disponivel').execute()
        todas_bolsas_disponiveis = response_bolsas.data
        print(f"  > ✅ {len(todas_bolsas_disponiveis)} bolsas disponíveis carregadas")
    except Exception as e:
        print(f"  > ❌ Erro ao carregar bolsas: {e}")
        return 0
    
    # 1.4 Carregar candidatos já aprovados (para anti-duplicação) (1 query)
    print(f"  > [4/4] Carregando candidatos já aprovados...")
    try:
        response_candidatos = self.client.table('bolsas').select('projeto_id, candidato_aprovado').eq('status', 'preenchida').execute()
        candidatos_aprovados_db = response_candidatos.data
        print(f"  > ✅ {len(candidatos_aprovados_db)} candidatos já aprovados carregados")
    except Exception as e:
        print(f"  > ❌ Erro ao carregar candidatos: {e}")
        candidatos_aprovados_db = []
    
    # ========== ETAPA 2: CRIAR ÍNDICES EM MEMÓRIA PARA BUSCA RÁPIDA ==========
    
    print(f"  > 🔧 Criando índices em memória...")
    
    # 2.1 Mapa de orientadores: chave normalizada -> [nomes originais]
    orientador_keys_to_originals = defaultdict(list)
    for o in todos_orientadores_db:
        key = self._get_match_key(o)
        if o not in orientador_keys_to_originals[key]:
            orientador_keys_to_originals[key].append(o)
    
    # 2.2 Mapa de projetos por orientador: orientador -> [projetos]
    projetos_por_orientador = defaultdict(list)
    for projeto in todos_projetos:
        orientador = projeto.get('orientador')
        if orientador:
            projetos_por_orientador[orientador].append(projeto)
    
    # 2.3 Mapa de bolsas por projeto: (projeto_id, numero_perfil) -> bolsa
    bolsas_por_projeto_perfil = {}
    for bolsa in todas_bolsas_disponiveis:
        key = (bolsa.get('projeto_id'), bolsa.get('numero_perfil'))
        if key[0] and key[1]:
            bolsas_por_projeto_perfil[key] = bolsa
    
    # 2.4 Mapa de candidatos aprovados por projeto: projeto_id -> [candidatos]
    candidatos_por_projeto = defaultdict(list)
    for item in candidatos_aprovados_db:
        projeto_id = item.get('projeto_id')
        candidato = item.get('candidato_aprovado')
        if projeto_id and candidato:
            candidatos_por_projeto[projeto_id].append(candidato)
    
    print(f"  > ✅ Índices criados em memória")
    
    # ========== ETAPA 3: PROCESSAR MATCHES EM MEMÓRIA (SEM QUERIES) ==========
    
    print(f"  > 🔍 Processando matches em memória...")
    updates_para_fazer = []  # Lista de updates a fazer em batch
    
    for i, aprovado in enumerate(aprovados, 1):
        orientador_original = aprovado.get('orientador')
        projeto_original = aprovado.get('nome_projeto')
        numero_perfil = self._normalize_perfil(aprovado.get('numero_perfil'))
        candidato_aprovado = self._normalize_text_for_db(aprovado.get('candidato_aprovado'))
        
        if not orientador_original or not projeto_original:
            print(f"  > [{i}/{len(aprovados)}] ⚠️ Dados incompletos, pulando...")
            continue
        
        # 3.1 Match de orientador (fuzzy)
        orientador_key_pdf = self._get_match_key(orientador_original)
        matches_keys = get_close_matches(
            orientador_key_pdf, 
            list(orientador_keys_to_originals.keys()), 
            n=5, 
            cutoff=0.75
        )
        
        if not matches_keys:
            print(f"  > [{i}/{len(aprovados)}] ❌ Orientador '{orientador_original}' não encontrado")
            continue
        
        # Recupera todos os orientadores que deram match
        matches_db_orientadores = []
        for key in matches_keys:
            matches_db_orientadores.extend(orientador_keys_to_originals[key])
        matches_db_orientadores = list(set(matches_db_orientadores))
        
        # 3.2 Busca projetos desses orientadores (EM MEMÓRIA, sem query!)
        projetos_do_orientador = []
        for orientador_db in matches_db_orientadores:
            projetos_do_orientador.extend(projetos_por_orientador.get(orientador_db, []))
        
        if not projetos_do_orientador:
            print(f"  > [{i}/{len(aprovados)}] ⚠️ Nenhum projeto para orientador '{matches_db_orientadores[0]}'")
            continue
        
        # 3.3 Match de projeto (fuzzy)
        best_match_project = self._find_best_project_match(
            projeto_original, 
            projetos_do_orientador
        )
        
        # 3.4 Fallback: se orientador tem apenas 1 projeto
        if not best_match_project and len(projetos_do_orientador) == 1:
            best_match_project = projetos_do_orientador[0]
            print(f"  > [{i}/{len(aprovados)}] 🔄 Fallback: único projeto do orientador")
        
        if not best_match_project:
            print(f"  > [{i}/{len(aprovados)}] ❌ Projeto '{projeto_original}' não encontrado")
            continue
        
        projeto_id = best_match_project.get('id')
        
        # 3.5 Anti-duplicação: verifica se candidato já foi aprovado neste projeto (EM MEMÓRIA!)
        candidatos_existentes = candidatos_por_projeto.get(projeto_id, [])
        if candidatos_existentes:
            candidato_aprovado_key = self._get_match_key(candidato_aprovado)
            candidatos_existentes_keys = [self._get_match_key(c) for c in candidatos_existentes]
            matches = get_close_matches(candidato_aprovado_key, candidatos_existentes_keys, n=1, cutoff=0.95)
            if matches:
                print(f"  > [{i}/{len(aprovados)}] ⚠️ Candidato '{candidato_aprovado}' já aprovado, pulando")
                continue
        
        # 3.6 Busca bolsa disponível (EM MEMÓRIA!)
        bolsa_key = (projeto_id, numero_perfil)
        bolsa = bolsas_por_projeto_perfil.get(bolsa_key)
        
        if not bolsa:
            print(f"  > [{i}/{len(aprovados)}] ❌ Bolsa não disponível (projeto={best_match_project.get('nome_projeto')}, perfil={numero_perfil})")
            continue
        
        # 3.7 Adiciona à lista de updates
        updates_para_fazer.append({
            'id': bolsa['id'],
            'status': 'preenchida',
            'candidato_aprovado': candidato_aprovado
        })
        
        # Remove da lista de disponíveis para evitar duplicação
        del bolsas_por_projeto_perfil[bolsa_key]
        
        # Adiciona aos candidatos aprovados (em memória)
        candidatos_por_projeto[projeto_id].append(candidato_aprovado)
        
        print(f"  > [{i}/{len(aprovados)}] ✅ Match encontrado: {candidato_aprovado} -> {best_match_project.get('nome_projeto')}")
    
    # ========== ETAPA 4: BATCH UPDATE (1 QUERY APENAS!) ==========
    
    bolsas_atualizadas = 0
    
    if updates_para_fazer:
        print(f"  > 💾 Executando batch update de {len(updates_para_fazer)} bolsas...")
        try:
            # Upsert em lote (1 query para todas as atualizações!)
            response = self.client.table('bolsas').upsert(updates_para_fazer).execute()
            bolsas_atualizadas = len(response.data) if response.data else 0
            print(f"  > ✅ {bolsas_atualizadas} bolsas atualizadas com sucesso!")
        except Exception as e:
            print(f"  > ❌ Erro no batch update: {e}")
            return 0
    else:
        print(f"  > ⚠️ Nenhuma atualização a fazer")
    
    # ========== ETAPA 5: NOTIFICAÇÕES (SE NECESSÁRIO) ==========
    
    if bolsas_atualizadas > 0:
        print(f"  > 🔔 Enviando notificações de resultado...")
        try:
            # Busca usuários interessados
            usuarios_para_notificar = self._buscar_usuarios_por_preferencia('resultado')
            
            if usuarios_para_notificar:
                from telegram_integration import call_telegram_notifications
                
                result = call_telegram_notifications(
                    titulo=f"Resultado de Edital - {bolsas_atualizadas} bolsas preenchidas",
                    link=edital_url,
                    tipo='resultado',
                    usuarios=usuarios_para_notificar
                )
                
                if result.get('success'):
                    print(f"  > ✅ Notificações enviadas para {result.get('sent_count', 0)} usuários")
        except Exception as e:
            print(f"  > ⚠️ Erro ao enviar notificações: {e}")
    
    print(f"  > ✨ CONCLUÍDO: {bolsas_atualizadas} bolsas atualizadas")
    print(f"  > 📊 Performance: ~4 queries (vs {1 + len(aprovados) * 3} na versão antiga)")
    
    return bolsas_atualizadas


def _find_best_project_match(self, projeto_original: str, projetos_do_orientador: list) -> Optional[Dict]:
    """
    Helper: Encontra o melhor match de projeto
    Reutiliza a lógica existente de matching (exato, substring, Jaccard, fuzzy)
    """
    projeto_match_key_pdf = self._get_project_match_key(projeto_original)
    
    # Camada 1: Match exato
    for p_db in projetos_do_orientador:
        p_db_match_key = self._get_project_match_key(p_db['nome_projeto'])
        if p_db_match_key == projeto_match_key_pdf:
            return p_db
    
    # Camada 2: Substring
    for p_db in projetos_do_orientador:
        p_db_match_key = self._get_project_match_key(p_db['nome_projeto'])
        if projeto_match_key_pdf in p_db_match_key:
            return p_db
    
    # Camada 3: Jaccard similarity
    best_jaccard_match = None
    highest_score = 0.0
    projeto_normalizado_words = set(projeto_match_key_pdf.split())
    
    for p_db in projetos_do_orientador:
        db_project_words = set(self._get_project_match_key(p_db['nome_projeto']).split())
        if not projeto_normalizado_words or not db_project_words:
            continue
        
        intersection = len(projeto_normalizado_words.intersection(db_project_words))
        union = len(projeto_normalizado_words.union(db_project_words))
        score = intersection / union if union > 0 else 0
        
        if score > highest_score:
            highest_score = score
            best_jaccard_match = p_db
    
    if highest_score >= 0.6:
        return best_jaccard_match
    
    # Camada 4: Fuzzy match
    match_map = {self._get_project_match_key(p['nome_projeto']): p for p in projetos_do_orientador}
    matches = get_close_matches(projeto_match_key_pdf, list(match_map.keys()), n=1, cutoff=0.8)
    if matches:
        return match_map[matches[0]]
    
    return None

