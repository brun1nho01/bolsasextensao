import os
import re
import json
import time
import fitz
import google.generativeai as genai
from dotenv import load_dotenv
import unicodedata
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions as google_exceptions
from difflib import get_close_matches
from datetime import datetime

# ✅ NOVO: Importa a função de um local centralizado
from .utils import get_match_key


def _save_error_log(context: str, content: str):
    """Salva uma resposta de IA que causou erro em um arquivo de log."""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"parser_error_{context}_{timestamp}.log"
    filepath = os.path.join(log_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  > [LOG-ERRO] Resposta da IA que causou falha foi salva em: {filepath}")
    except Exception as e:
        print(f"  > [LOG-ERRO] Falha ao salvar o arquivo de log: {e}")

class UenfParser:
    def __init__(self):
        load_dotenv()
        
        # ✅ CORREÇÃO: Usar gerenciador seguro de API keys
        from api_key_manager import key_manager
        
        try:
            self.api_keys = key_manager.get_gemini_keys()
            self.key_manager = key_manager
        except ValueError as e:
            raise ValueError(f"Erro ao carregar API keys: {e}")
            
        self.current_key_index = 0
        print(f"  > {len(self.api_keys)} chave(s) de API do Gemini carregada(s) de forma segura.")
        
        # A configuração inicial da chave será feita na primeira chamada.
        genai.configure(api_key=self.api_keys[self.current_key_index])

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            safety_settings=safety_settings
        )
        
        print("Modelo Gemini (2.5 Flash) inicializado.")

    def _call_gemini_api_with_rotation(self, prompt: str):
        """
        Chama a API do Gemini e gerencia a rotação de chaves em caso de erro de cota diária.
        """
        while self.current_key_index < len(self.api_keys):
            try:
                # Usa a chave atual para a requisição
                print(f"  > [API] Usando chave de API #{self.current_key_index + 1}...")
                
                # ✅ CORREÇÃO: Rastrear uso da chave
                self.key_manager.track_usage(self.current_key_index)
                
                response = self.model.generate_content(prompt, request_options={'timeout': 600})
                return response # Sucesso, retorna a resposta

            except google_exceptions.ResourceExhausted as e:
                # Verifica se o erro é especificamente sobre a cota DIÁRIA
                if "GenerateRequestsPerDay" in str(e):
                    print(f"  > [API-AVISO] Chave de API #{self.current_key_index + 1} atingiu o limite DIÁRIO de requisições.")
                    self.current_key_index += 1
                    
                    if self.current_key_index < len(self.api_keys):
                        # Se ainda houver chaves, configura a próxima e tenta novamente no próximo loop
                        next_key = self.api_keys[self.current_key_index]
                        genai.configure(api_key=next_key)
                        print(f"  > [API] Trocando para a chave #{self.current_key_index + 1}.")
                        
                        # RECRIA O MODELO com a nova chave. Essencial para que a nova chave seja usada.
                        self.model = genai.GenerativeModel(
                            'gemini-2.5-flash',
                            safety_settings={
                                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                            }
                        )
                    else:
                        # Acabaram as chaves
                        print("  > [API-ERRO] Todas as chaves de API atingiram o limite diário.")
                        return None
                else:
                    # É outro tipo de erro 429 (ex: por minuto), que as pausas devem resolver. Lança o erro.
                    print(f"  > [API-ERRO] Erro de recurso esgotado (provavelmente por minuto): {e}")
                    raise e
            
            except Exception as e:
                print(f"  > [API-ERRO] Um erro inesperado ocorreu ao chamar a API Gemini: {e}")
                # Para outros tipos de erro, não rotaciona a chave e lança a exceção
                raise e
        
        # Se saiu do loop, significa que todas as chaves falharam
        return None

    def _classify_etapa(self, titulo, texto_pdf):
        titulo = titulo.lower()
        texto_pdf = texto_pdf.lower()

        if any(keyword in titulo for keyword in ['resultado', 'convocação', 'convocacao']):
            return 'resultado'
        if 'homologação do resultado' in texto_pdf or 'resultado final' in texto_pdf:
            return 'resultado'

        if 'entrevista' in titulo:
            return 'entrevista'
        if 'homologadas' in titulo:
            return 'homologacao'
            
        return 'inscricao'
    
    def _classify_modalidade(self, titulo: str) -> str:
        """Classifica a modalidade do edital (extensao ou apoio_academico) com base no título"""
        titulo_lower = titulo.lower()
        
        # ProAC / Apoio Acadêmico tem prioridade (mais específico)
        # Verifica com e sem acento
        apoio_keywords = ['proac', 'apoio acadêmico', 'apoio academico']
        if any(keyword in titulo_lower for keyword in apoio_keywords):
            return 'apoio_academico'
        
        # PROEX / Extensão
        extensao_keywords = ['proex', 'extensão', 'extensao']
        if any(keyword in titulo_lower for keyword in extensao_keywords):
            return 'extensao'
        
        # Fallback: se chegou até aqui mas não identificou, considera extensão por padrão
        return 'extensao'

    def _extract_and_clean_text_from_pdf(self, pdf_path: str) -> str:
        try:
            text = ""
            # Abre o PDF com a nova biblioteca, PyMuPDF (fitz)
            with fitz.open(pdf_path) as doc:
                # Itera sobre cada página do documento
                for page in doc:
                    # Extrai o texto da página preservando as quebras de linha
                    text += page.get_text("text") or ""

            # Substitui múltiplos espaços por um único espaço EM CADA LINHA, mas MANTÉM as quebras de linha.
            lines = text.split('\n')
            cleaned_lines = [re.sub(r' +', ' ', line).strip() for line in lines]
            cleaned_text = '\n'.join(cleaned_lines)

            return cleaned_text
        except Exception as e:
            # Mensagem de erro caso até mesmo a PyMuPDF falhe
            print(f"  > Erro ao ler o PDF {os.path.basename(pdf_path)} com PyMuPDF: {e}")
            return ""


    def _parse_resultado_com_ia(self, caminho_pdf: str, orientadores_conhecidos: list = None) -> list:
        # Analisando PDF de resultado
        
        todos_aprovados_final = []
        
        try:
            with fitz.open(caminho_pdf) as doc:
                for page_num, page in enumerate(doc):
                    texto_pagina = page.get_text("text")
                    if not texto_pagina or len(texto_pagina.strip()) < 100:
                        continue # Pula páginas vazias
                        
                    print(f"  > Processando página {page_num + 1}/{len(doc)}...", flush=True)

                    time.sleep(5)

                    prompt = f"""
                    Sua tarefa é extrair dados tabulares de uma página de um PDF de resultados de bolsas para um formato JSON ESTRITO.

                    **REGRAS CRÍTICAS E INFALÍVEIS:**
                    1.  **SAÍDA EXCLUSIVAMENTE JSON:** Sua resposta DEVE ser um único objeto JSON. NÃO inclua NENHUM texto, explicação ou markdown (```json).
                    2.  **SCHEMA OBRIGATÓRIO:** O JSON DEVE ter duas chaves: `headers` (uma lista de strings) e `rows` (uma lista de listas).
                    3.  **AGRUPAMENTO DE LINHAS:** Se os dados de uma única entrada (como um nome de projeto longo) estiverem espalhados por várias linhas no texto, você DEVE agrupá-los em uma única string na célula correspondente da linha.
                    4.  **SEMPRE EXTRAIA LINHAS:** Tente extrair todas as linhas de dados que pareçam pertencer a uma tabela, mesmo que a formatação seja imperfeita. É melhor retornar uma linha com dados parciais do que omitir a linha inteira.
                    5.  **NORMALIZAÇÃO DE CABEÇALHOS:** Normalize os cabeçalhos que você encontrar para o seguinte padrão obrigatório: `COORDENADOR`, `PROJETO`, `NOME`, `COLOCAÇÃO`, `PERFIL`, `Nº VAGAS`. Por exemplo, se encontrar "NOME DO BOLSISTA" ou "NOME DISCENTE", o cabeçalho no JSON deve ser `NOME`.
                    6.  **TIPOS DE BOLSAS:** Bolsas com nome de Universidade Aberta, é a mesma coisa que Bolsa UA, sendo os três tipos diferentes, médio, superior e fundamental.
                    7.  **CASO VAZIO:** Se a página não contiver NENHUMA tabela de resultados, retorne `{{"headers": [], "rows": []}}`.

                    **EXEMPLO DE EXECUÇÃO PERFEITA 1 (Agrupamento de Linhas):**
                    *ENTRADA:*
                    ```
                    COORDENADOR PROJETO NOME COLOCAÇÃO PERFIL Nº VAGAS
                    Gerson Adriano Silva
                    Entomologia Nas Escolas: Uso De Coleções
                    Entomológicas. Maria Luiza da Silva 1º Classificado 1 1
                    ```
                    *SAÍDA JSON ESPERADA:*
                    ```json
                    {{
                      "headers": ["COORDENADOR", "PROJETO", "NOME", "COLOCAÇÃO", "PERFIL", "Nº VAGAS"],
                      "rows": [
                        ["Gerson Adriano Silva", "Entomologia Nas Escolas: Uso De Coleções Entomológicas.", "Maria Luiza da Silva", "1º Classificado", "1", "1"]
                      ]
                    }}
                    ```

                    **EXEMPLO DE EXECUÇÃO PERFEITA 2 (Normalização de Cabeçalho e Dados Completos):**
                    *ENTRADA:*
                    ```
                    ORIENTADOR PROJETO NOME DISCENTE CLASSIFICAÇÃO PERFIL Nº VAGAS
                    Fábio Lopes Olivares Desenvolvimento de biopesticida... João Pedro Ribeiro 1º Lugar 2 1
                    ```
                    *SAÍDA JSON ESPERADA:*
                    ```json
                    {{
                      "headers": ["COORDENADOR", "PROJETO", "NOME", "COLOCAÇÃO", "PERFIL", "Nº VAGAS"],
                      "rows": [
                        ["Fábio Lopes Olivares", "Desenvolvimento de biopesticida...", "João Pedro Ribeiro", "1º Lugar", "2", "1"]
                      ]
                    }}
                    ```

                    Agora, processe o texto real abaixo com MÁXIMA ATENÇÃO a todas as regras.

                    **Texto da Página do PDF para Análise:**
                    ---
                    {texto_pagina}
                    ---
                    """
                    
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            resposta_ia = self._call_gemini_api_with_rotation(prompt)
                            if not resposta_ia:
                                print("  > [PARSER] Abortando análise de resultados pois todas as chaves de API estão esgotadas.")
                                return todos_aprovados_final

                            match = re.search(r'```json\s*(\{.*?\})\s*```', resposta_ia.text, re.DOTALL)
                            json_text = match.group(1) if match else resposta_ia.text
                            
                            dados_brutos = json.loads(json_text)
                            
                            headers = [h.upper() for h in dados_brutos.get("headers", [])]
                            rows = dados_brutos.get("rows", [])
                            
                            if not headers or not rows:
                                print(f"  > Aviso: IA não retornou cabeçalhos ou linhas para a página {page_num + 1}.")
                                break

                            def get_col_index(aliases):
                                for alias in aliases:
                                    if alias in headers:
                                        return headers.index(alias)
                                return -1

                            idx_orientador = get_col_index(['COORDENADOR', 'ORIENTADOR'])
                            idx_candidato = get_col_index(['CANDIDATO', 'DISCENTE', 'BOLSISTA', 'NOME'])
                            idx_perfil = get_col_index(['PERFIL', 'Nº PERFIL'])
                            idx_colocacao = get_col_index(['COLOCAÇÃO', 'CLASSIFICAÇÃO'])
                            idx_projeto = get_col_index(['PROJETO'])

                            if -1 in [idx_orientador, idx_candidato, idx_perfil, idx_colocacao, idx_projeto]:
                                print(f"  > Aviso: Não foi possível mapear colunas na página {page_num + 1}. Cabeçalhos: {headers}")
                                break 

                            for row in rows:
                                if len(row) <= max(idx_orientador, idx_candidato, idx_perfil, idx_colocacao, idx_projeto):
                                    continue

                                colocacao = str(row[idx_colocacao]).upper()
                                if "RESERVA" in colocacao:
                                    continue

                                perfil_bruto = str(row[idx_perfil]).strip()
                                if not perfil_bruto.isdigit():
                                    continue

                                orientador_bruto = row[idx_orientador]
                                orientador_corrigido = orientador_bruto

                                if orientadores_conhecidos:
                                    orientador_bruto_key = get_match_key(orientador_bruto)
                                    orientador_keys_map = {get_match_key(o): o for o in orientadores_conhecidos}
                                    matches_keys = get_close_matches(orientador_bruto_key, list(orientador_keys_map.keys()), n=1, cutoff=0.8)
                                    
                                    if matches_keys:
                                        orientador_corrigido = orientador_keys_map[matches_keys[0]]

                                todos_aprovados_final.append({
                                    "orientador": orientador_corrigido,
                                    "nome_projeto": row[idx_projeto],
                                    "numero_perfil": row[idx_perfil],
                                    "candidato_aprovado": row[idx_candidato]
                                })

                            break

                        except Exception as e:
                            print(f"  > Tentativa {attempt + 1}/{max_retries} na página {page_num + 1} falhou: {e}")
                            if attempt + 1 == max_retries:
                                print(f"  > Erro final na página {page_num + 1} após {max_retries} tentativas.")
                                if 'resposta_ia' in locals() and hasattr(resposta_ia, 'text'):
                                    _save_error_log(f"resultado_pdf_page_{page_num+1}", resposta_ia.text)
                            else:
                                time.sleep(5)
            
            return todos_aprovados_final

        except Exception as e:
            print(f"  > Erro crítico ao abrir ou processar o PDF {os.path.basename(caminho_pdf)}: {e}")
            return []

    def _parse_bolsas_com_ia(self, pdf_path):
        """
        Abordagem "Fatiar e Conquistar" para extrair bolsas de editais de inscrição:
        1. (Python) Lê o PDF inteiro e fatia o texto em blocos de projeto individuais.
        2. (IA) Para cada bloco de projeto, faz uma única chamada à IA para extrair todos os detalhes.
        """
        texto_pdf = self._extract_and_clean_text_from_pdf(pdf_path)
        
        # [NOVO DEBUG] Verifica o resultado da extração de texto
        # Texto extraído do PDF

        if not texto_pdf or len(texto_pdf) < 100:
            return None

        # Etapa 1 (Python): Fatiar o texto em blocos de projeto.
        # A lógica foi revertida para o método original, mais robusto, que usa finditer
        # para lidar com os casos onde "PROGRAMA" e "DADOS DO PROJETO" aparecem juntos.
        pattern = r'PROGRAMA:|DADOS\s+DO(S)?\s+PROJETO(S)?'
        matches = list(re.finditer(pattern, texto_pdf, flags=re.IGNORECASE))
        
        split_indices = []
        if matches:
            split_indices.append(matches[0].start())
            for i in range(len(matches) - 1):
                current_match = matches[i]
                next_match = matches[i+1]
                is_programa = 'PROGRAMA' in current_match.group(0).upper()
                is_dados = 'DADOS' in next_match.group(0).upper()
                distance = next_match.start() - current_match.start()
                if is_programa and is_dados and distance < 400:
                    continue
                split_indices.append(next_match.start())

        blocos_de_texto = []
        for i, start_index in enumerate(split_indices):
            end_index = split_indices[i+1] if i + 1 < len(split_indices) else len(texto_pdf)
            blocos_de_texto.append(texto_pdf[start_index:end_index])
        
        # [DEBUG] Adicionado para verificar quantos projetos foram encontrados no PDF
        print(f"  > Padrão de separação encontrou {len(blocos_de_texto)} blocos de projeto em '{os.path.basename(pdf_path)}'.")

        if not blocos_de_texto:
            print(f"  > Aviso: Nenhum bloco de projeto encontrado no PDF via separador: {os.path.basename(pdf_path)}")
            return None

        projetos_finais = []
        resumo_pendente = "" # Buffer para carregar um resumo para o próximo projeto, conforme a lógica solicitada.

        # Etapa 2 (IA): Loop para processar um projeto de cada vez
        for i, texto_bloco in enumerate(blocos_de_texto):
            print(f"    > Processando Bloco {i+1}/{len(blocos_de_texto)}...")

            # Etapa Intermediária (Python): Separar dados estruturados do resumo.
            # Usamos um Regex flexível para encontrar "RESUMO" e capturar o que vem antes e depois.
            match = re.search(r"^(.*?)(RESUMO.*)$", texto_bloco, re.DOTALL | re.IGNORECASE)
            
            texto_para_ia = texto_bloco
            resumo_encontrado_no_bloco = ""

            if match:
                texto_para_ia = match.group(1).strip()
                resumo_encontrado_no_bloco = match.group(2).strip()
            
            # [DEBUG] Adicionado para imprimir o texto exato enviado para a IA.
            # Enviando bloco de texto para IA

            prompt_detalhes_projeto = f"""
                Sua tarefa é extrair informações de um projeto de edital para um formato JSON ESTRITO E CONSISTENTE.

                **REGRAS CRÍTICAS:**
                1.  **SAÍDA EXCLUSIVAMENTE JSON:** Responda APENAS com o objeto JSON.
                2.  **SCHEMA OBRIGATÓRIO:** O JSON DEVE seguir este schema:
                    - `nome_projeto` (string)
                    - `orientador` (string)
                    - `detalhe_bolsas` (lista de objetos), onde CADA objeto da lista DEVE conter:
                        - `tipo_bolsa` (string)
                        - `vagas` (inteiro)
                        - `numero_perfil` (inteiro)
                        - `requisitos` (string)
                        - `valor_bolsa` (float)
                3.  **DESAMBIGUAÇÃO:** Ignore qualquer "Coordenador de Programa" ou "Nome de Programa" no início do texto. Foque APENAS no `nome_projeto` e `orientador` que estão diretamente associados aos detalhes das bolsas.
                4   **TIPO DE BOLSA:** Bolsas com nome de Universidade Aberta, é a mesma coisa que Bolsa UA, sendo os três tipos diferentes, médio, superior e fundamental.
                5.  **DADOS NUMÉRICOS:** `vagas` e `numero_perfil` devem ser extraídos como NÚMEROS (inteiros). `valor_bolsa` deve ser um NÚMERO (float).
                6.  **EXEMPLO DE SAÍDA:**
                    ```json
                    {{
                      "nome_projeto": "Trilhas das Abelhas",
                      "orientador": "Maria Cristina Gaglianone",
                      "detalhe_bolsas": [
                        {{
                          "tipo_bolsa": "Bolsa Extensão Discente UENF",
                          "vagas": 3,
                          "numero_perfil": 1,
                          "requisitos": "Estar matriculado em curso de graduação na UENF em Ciências Biológicas...",
                          "valor_bolsa": 700.00
                        }}
                      ]
                    }}
                    ```

                **Texto para Análise:**
                ---
                {texto_para_ia}
                ---
            """
            
            # LÓGICA DE RETENTATIVAS (RETRY) PARA RESISTIR A TIMEOUTS DA API
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self._call_gemini_api_with_rotation(prompt_detalhes_projeto)
                    if not response: # Se retornou None, todas as chaves acabaram
                        print("  > [PARSER] Abortando análise de bolsas pois todas as chaves de API estão esgotadas.")
                        return projetos_finais # Retorna o que conseguiu até agora
                
                    # [NOVO LOG] Adicionado para depurar a resposta completa da IA
                    # Resposta da IA recebida

                    json_text = response.text.strip()
                    if json_text.startswith("```json"):
                        json_text = json_text[7:]
                    if json_text.endswith("```"):
                        json_text = json_text[:-3]
                    
                    dados_projeto = json.loads(json_text)

                    if dados_projeto and dados_projeto.get("detalhe_bolsas"):
                        if all(k in dados_projeto for k in ["nome_projeto", "orientador", "detalhe_bolsas"]):
                            
                            # --- LÓGICA DE ATRIBUIÇÃO DE RESUMO ---
                            # Se há um resumo pendente da iteração anterior, ele pertence a ESTE projeto.
                            if resumo_pendente:
                                dados_projeto["resumo"] = resumo_pendente.replace("RESUMO", "").strip()
                                resumo_pendente = "" # Limpa o buffer

                            # Agora, avalia o resumo encontrado no bloco ATUAL.
                            # Se o projeto JÁ tem um resumo (do buffer) e encontramos outro, o novo é para o PRÓXIMO projeto.
                            if "resumo" in dados_projeto and resumo_encontrado_no_bloco:
                                resumo_pendente = resumo_encontrado_no_bloco
                            # Se o projeto AINDA não tem resumo, o que encontramos pertence a ele.
                            elif resumo_encontrado_no_bloco:
                                dados_projeto["resumo"] = resumo_encontrado_no_bloco.replace("RESUMO", "").strip()
                            
                            projetos_finais.append(dados_projeto)
                        else:
                            print(f"    > Aviso: IA retornou JSON incompleto para o bloco {i+1}. Título: {dados_projeto.get('nome_projeto', 'N/A')}")
                    else:
                        # [DEBUG] Log aprimorado para falhas de extração
                        print(f"    > Aviso: IA não retornou detalhes de bolsas para o bloco {i+1}.")
                        print(f"      - Texto enviado para a IA (sem resumo):\\n---\\n{texto_para_ia[:500]}...\\n---")
                    
                    # Se chegou aqui, a tentativa foi bem-sucedida, então sai do loop de retry
                    break 

                except Exception as e:
                    print(f"  > Tentativa {attempt + 1}/{max_retries} de processar bloco {i+1} com IA falhou: {e}")
                    if attempt + 1 == max_retries:
                        print(f"    > Erro final no bloco {i+1} após {max_retries} tentativas.")
                        if 'response' in locals() and hasattr(response, 'text'):
                            _save_error_log(f"bolsa_pdf_bloco_{i+1}", response.text)
                    else:
                        time.sleep(5) # Espera 12 segundos antes de tentar novamente

            # Garante uma pausa de 5 segundos ENTRE cada bloco de projeto para não exceder o limite da API.
            time.sleep(5)

        return projetos_finais

    def _parse_data_fim_inscricao(self, pdf_path):
        texto_pdf = self._extract_and_clean_text_from_pdf(pdf_path)
        if not texto_pdf or len(texto_pdf) < 100:
            return None

        prompt = f"""
            Analise o texto do edital a seguir e encontre a data final para as inscrições.
            Procure por "Período de Inscrição" ou "Cronograma".
            Sua resposta deve ser um JSON com a chave "data_fim_inscricao" (formato "DD/MM/YYYY") ou null.

            Texto do edital para análise:
            ---
            {texto_pdf}
            ---
        """
        try:
            # As configurações de segurança já estão no self.model
            response = self._call_gemini_api_with_rotation(prompt)
            if not response:
                print("  > [PARSER] Abortando análise de data pois todas as chaves de API estão esgotadas.")
                return None

            match = re.search(r'```json\s*(\{.*?\})\s*```', response.text, re.DOTALL)
            json_text = match.group(1) if match else response.text

            dados = json.loads(json_text)
            return dados.get("data_fim_inscricao", None)
        except Exception as e:
            print(f"  > Erro ao fazer parsing da resposta da IA para data: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                _save_error_log("data_fim_inscricao", response.text)
            return None

    def _formatar_data_para_db(self, data_str):
        """Converte data de DD/MM/AAAA para AAAA-MM-DD."""
        if not data_str or not isinstance(data_str, str):
            return None
        try:
            # Tenta converter do formato brasileiro
            return datetime.strptime(data_str, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            # Se já estiver no formato correto ou for inválida, retorna None ou o original se preferir
            print(f"  > Aviso: Formato de data inesperado recebido: {data_str}")
            return None

    def _extract_data_from_titulo(self, titulo):
        match = re.search(r'inscrições até (\d{2}/\d{2})', titulo, re.IGNORECASE)
        if match:
            from datetime import datetime
            data_brasileira = f"{match.group(1)}/{datetime.now().year}"
            return self._formatar_data_para_db(data_brasileira)
        return None

    def parse_noticia(self, titulo: str, caminho_pdf_principal: str, caminhos_pdf_projetos: list, orientadores_conhecidos: list = None, data_publicacao: str = None) -> dict:
        dados_extraidos = {
            "titulo": titulo,
            "etapa": None,
            "data_fim_inscricao": None,
            "data_publicacao": data_publicacao,
            "projetos": [],
            "aprovados": []
        }
        try:
            titulo_lower = titulo.lower()
            is_resultado = any(kw in titulo_lower for kw in ['resultado', 'classificados'])
            is_inscricao = any(kw in titulo_lower for kw in ['inscreve', 'inscrições', 'inscrição', 'seletivo', 'seleção'])

            # ✅ Classifica modalidade: extensao ou apoio_academico
            dados_extraidos["modalidade"] = self._classify_modalidade(titulo)

            if is_resultado:
                dados_extraidos['etapa'] = 'resultado'
                todos_aprovados = []
                print(f"  > Processando {len(caminhos_pdf_projetos)} PDF(s) de resultado para o edital '{titulo}'...")
                for item in caminhos_pdf_projetos:
                    pdf_path = item['path'] 
                    aprovados_no_pdf = self._parse_resultado_com_ia(pdf_path, orientadores_conhecidos)
                    if aprovados_no_pdf:
                        todos_aprovados.extend(aprovados_no_pdf)
                    time.sleep(1)
                dados_extraidos['aprovados'] = todos_aprovados

            elif is_inscricao and caminhos_pdf_projetos:
                dados_extraidos['etapa'] = 'inscricao'
                
                data_fim_bruta = self._extract_data_from_titulo(titulo)
                if not data_fim_bruta and caminho_pdf_principal:
                    data_fim_bruta = self._parse_data_fim_inscricao(caminho_pdf_principal)
                
                data_fim_formatada = self._formatar_data_para_db(data_fim_bruta)
                dados_extraidos['data_fim_inscricao'] = data_fim_formatada
                dados_extraidos['titulo'] = titulo
                
                projetos = []
                # [DEBUG] Adicionado para sabermos que o loop vai começar
                # Processando PDFs de projeto
                for i, item in enumerate(caminhos_pdf_projetos):
                    pdf_path = item['path']
                    centro = item['centro']
                    
                    # [DEBUG] Adicionado para identificar o PDF exato antes de processá-lo
                    # Processando PDF de projeto
                    
                    dados_bolsas = self._parse_bolsas_com_ia(pdf_path)
                    if dados_bolsas:
                        for projeto in dados_bolsas:
                            projeto['centro'] = centro
                        projetos.extend(dados_bolsas)
                    time.sleep(1)
                
                dados_extraidos['projetos'] = projetos
            
            else:
                return None

            return dados_extraidos

        except Exception as e:
            print(f"  > Ocorreu um erro inesperado no parser: {e}")
            import traceback
            traceback.print_exc()
            return None
