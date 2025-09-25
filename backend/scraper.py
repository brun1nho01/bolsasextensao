import requests
from bs4 import BeautifulSoup
import os
import tempfile
import uuid
from urllib.parse import urljoin
import re
import time
import locale
from datetime import datetime

class UenfScraper:
    def __init__(self, parser, db_manager, page_num=1):
        self.base_url = "https://uenf.br" # Base para juntar links de PDF
        self.scrape_url = f"https://uenf.br/portal/editais/{page_num}/" # A página que vamos raspar
        self.parser = parser
        self.db_manager = db_manager
        self.session = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        self.session.headers.update(headers)
        try:
            # Tenta configurar o locale. Se falhar, o fallback manual será usado.
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        except locale.Error:
            print("  > Aviso: locale 'pt_BR.UTF-8' não encontrado. Usando fallback para parse de datas.")
            pass

    def _parse_publication_date(self, date_str: str) -> str | None:
        """Converte uma data em texto (ex: 'julho 25, 2025') para o formato AAAA-MM-DD."""
        if not date_str:
            return None
        
        # Tentativa 1: Usando o locale do sistema
        try:
            date_obj = datetime.strptime(date_str, '%B %d, %Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass # Continua para o fallback se o formato não for exatamente esse

        # Tentativa 2: Fallback manual com mapeamento de meses (mais robusto)
        month_map = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03', 'abril': '04',
            'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
            'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
        }
        try:
            # Limpa e normaliza a string: "julho 25, 2025" -> "julho 25 2025"
            cleaned_str = date_str.lower().replace(',', '').replace(' de ', ' ')
            
            parts = cleaned_str.split()
            if len(parts) == 3:
                month_name, day, year = parts
                month_num = month_map.get(month_name)
                if month_num:
                    return f"{year}-{month_num}-{day.zfill(2)}"
        except Exception:
            print(f"  > Aviso: Falha final ao parsear a data '{date_str}' com o método manual.")
            return None
        
        return None

    def _make_request_with_retry(self, url: str, stream=False):
        """Tenta fazer uma requisição GET até 3 vezes com delay exponencial."""
        retries = 3
        delay = 1  # segundos
        for i in range(retries):
            try:
                response = self.session.get(url, timeout=30, stream=stream)
                response.raise_for_status()
                return response
            except (requests.ConnectionError, requests.Timeout) as e:
                print(f"  > Erro de conexão/timeout ao acessar {url} (tentativa {i+1}/{retries}): {e}")
                if i < retries - 1:
                    time.sleep(delay)
                    delay *= 2  # Aumenta o delay para a próxima tentativa
                else:
                    print(f"  > Desistindo de acessar {url} após {retries} tentativas.")
                    return None
        return None

    def _extract_centro_from_text(self, text: str) -> str | None:
        """Extrai a sigla do centro (CCT, CCH, CCTA, CBB) de um texto."""
        centros_map = {'cbb': 'cbb', 'cct': 'cct', 'ccta': 'ccta', 'cch': 'cch'}
        # Ordena as chaves pelo comprimento, da maior para a menor, para evitar falsos positivos (ex: "cct" em "ccta")
        sorted_keys = sorted(centros_map.keys(), key=len, reverse=True)
        for key in sorted_keys:
            if key in text.lower():
                return centros_map[key]
        return None

    def _download_pdfs_to_temp_files(self, edital_url, is_resultado=False):
        all_temp_files = []
        data_publicacao_str = None # Variavel para guardar a data
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            # Usa a função com retentativas para a página do edital
            response = self._make_request_with_retry(edital_url)
            if not response:
                print(f"  > Falha ao acessar a página do edital {edital_url} após múltiplas tentativas.")
                return None, [], None

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Tenta extrair a data de publicação do post
            date_tag = soup.select_one('span.elementor-post-info__item--type-date')
            if date_tag:
                data_publicacao_str = date_tag.get_text(strip=True)
            
            # Encontra todos os links de PDF no conteúdo principal do post
            all_link_tags = soup.find_all('a', href=lambda href: href and href.endswith('.pdf'))
            
            centros_map = {'cbb': 'cbb', 'cct': 'cct', 'ccta': 'ccta', 'cch': 'cch'}
            # Ordena as chaves para garantir que a mais longa ("ccta") seja verificada antes da mais curta ("cct")
            sorted_centro_keys = sorted(centros_map.keys(), key=len, reverse=True)
            keywords_exclusao = ['boletim', 'epidemiológico', 'errata']

            # Filtra links de projeto e candidatos a principal, excluindo links indesejados
            caminhos_pdf_projetos_com_centro = []
            candidatos_a_principal_relative = []
            for tag in all_link_tags:
                link_text = tag.get_text(strip=True).lower()
                link_href = tag['href']

                if any(kw in link_text for kw in keywords_exclusao):
                    continue # Pula o link se for da lista de exclusão

                centro_encontrado = None
                for key in sorted_centro_keys:
                    if key in link_text:
                        centro_encontrado = centros_map[key]
                        break
                
                if centro_encontrado:
                    caminhos_pdf_projetos_com_centro.append({'href': link_href, 'centro': centro_encontrado})
                else:
                    candidatos_a_principal_relative.append(link_href)

            # O primeiro candidato que não foi excluído ou classificado como projeto é o principal
            pdf_link_principal_relative = candidatos_a_principal_relative[0] if candidatos_a_principal_relative else None
            
            if not caminhos_pdf_projetos_com_centro and not pdf_link_principal_relative and all_link_tags:
                 # Caso especial: se após a filtragem não sobrar nada, mas existiam PDFs,
                 # pode ser uma página de resultado simples. Pega o primeiro não excluído.
                 for tag in all_link_tags:
                    if not any(kw in tag.get_text(strip=True).lower() for kw in keywords_exclusao):
                        pdf_link_principal_relative = tag['href']
                        break

            def download_pdf(relative_url):
                nonlocal all_temp_files
                try:
                    # Garante que a URL é absoluta
                    pdf_url = urljoin(self.base_url, relative_url)
                    # Usa a função com retentativas para baixar o PDF
                    pdf_response = self._make_request_with_retry(pdf_url)
                    if not pdf_response:
                        print(f"  > Falha ao baixar o PDF {pdf_url} após múltiplas tentativas.")
                        return None
                    
                    fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix=f"scraper-uenf-{uuid.uuid4()}-")
                    os.close(fd)
                    with open(temp_path, 'wb') as f:
                        f.write(pdf_response.content)
                    all_temp_files.append(temp_path)
                    return temp_path
                except requests.RequestException as e:
                    print(f"  > Falha ao baixar o PDF {pdf_url}: {e}")
                    return None

            temp_file_principal = download_pdf(pdf_link_principal_relative) if pdf_link_principal_relative else None
            
            temp_files_projetos = []
            if caminhos_pdf_projetos_com_centro:
                print(f"  > Encontrados {len(caminhos_pdf_projetos_com_centro)} PDF(s) de projetos. Baixando...")
                for item in caminhos_pdf_projetos_com_centro:
                    temp_path = download_pdf(item['href'])
                    if temp_path:
                        temp_files_projetos.append({'path': temp_path, 'centro': item['centro']})
            
            return temp_file_principal, temp_files_projetos, data_publicacao_str
        
        except Exception as e:
            print(f"  > Erro inesperado ao baixar PDFs do edital {edital_url}: {e}")
            return None, [], None

    def fetch_news(self):
        try:
            # Busca a data do último edital salvo no banco ANTES de começar
            latest_date_in_db_str = self.db_manager.get_latest_edital_date()
            latest_date_in_db = None
            if latest_date_in_db_str:
                latest_date_in_db = datetime.strptime(latest_date_in_db_str, '%Y-%m-%d').date()
                print(f"Última data de publicação no banco: {latest_date_in_db.strftime('%d/%m/%Y')}")

            response = self._make_request_with_retry(self.scrape_url)
            if not response:
                print(f"  > Falha ao buscar a página de editais {self.scrape_url}. Pulando para a próxima.")
                return 0
            # Lista de editais obtida com sucesso

        except requests.RequestException as e:
            print(f"Erro ao buscar a página de editais: {e}")
            return 0

        soup = BeautifulSoup(response.content, 'html.parser')
        
        link_tags = soup.select('div.elementor-widget-theme-post-title h2 a')
        link_tags.reverse()

        print(f"\n>>> {len(link_tags)} notícias encontradas. Analisando cada uma (em ordem inversa)...\n")
        
        novos_editais_processados = 0
        for i, link_tag in enumerate(link_tags):
            titulo = link_tag.get_text(strip=True)
            
            # [DEBUG] Adicionado para ver qual edital está sendo processado
            print(f"\n--- [SCRAPER] Análisando Edital {i+1}/{len(link_tags)}: '{titulo}' ---", flush=True)

            titulo_lower = titulo.lower()
            if 'proex' not in titulo_lower and 'extensão' not in titulo_lower:
                continue
            
            keywords_inscricao = ['inscreve', 'inscrições', 'inscrição', 'seletivo', 'seleção']
            keywords_resultado = ['resultado', 'classificados']

            is_inscricao = any(kw in titulo_lower for kw in keywords_inscricao)
            is_resultado = any(kw in titulo_lower for kw in keywords_resultado)

            if not is_inscricao and not is_resultado:
                continue

            edital_url = link_tag['href']
            
            caminho_pdf_principal, caminhos_pdf_projetos, data_publicacao_str = self._download_pdfs_to_temp_files(edital_url, is_resultado)
            data_publicacao = self._parse_publication_date(data_publicacao_str)
            
            # --- LÓGICA DE OTIMIZAÇÃO ---
            if data_publicacao and latest_date_in_db:
                data_publicacao_obj = datetime.strptime(data_publicacao, '%Y-%m-%d').date()
                if data_publicacao_obj <= latest_date_in_db:
                    print(f"  > Ignorando edital '{titulo}' (publicado em {data_publicacao_obj.strftime('%d/%m/%Y')}) pois é anterior ou igual ao último já salvo.")
                    continue # Pula para o próximo edital da lista
            
            # Download de PDFs concluído
            
            all_files_paths = ([caminho_pdf_principal] if caminho_pdf_principal else []) + [item['path'] for item in caminhos_pdf_projetos]
            
            try:
                if is_resultado and not caminhos_pdf_projetos:
                    print(f"Ignorando edital de resultado (sem PDFs de projeto): '{titulo}'")
                    continue
                if is_inscricao and not (caminho_pdf_principal and caminhos_pdf_projetos):
                    print(f"Ignorando edital de inscrição (incompleto): '{titulo}'")
                    continue
                
                if is_inscricao and caminho_pdf_principal and caminhos_pdf_projetos:
                    dados_edital = self.parser.parse_noticia(
                        titulo, 
                        caminho_pdf_principal, 
                        caminhos_pdf_projetos,
                        data_publicacao=data_publicacao
                    )
                    if dados_edital and dados_edital.get('projetos'):
                        self.db_manager.upsert_edital(dados_edital, edital_url)
                        novos_editais_processados += 1

                elif is_resultado and caminhos_pdf_projetos:
                    lista_orientadores = self.db_manager.get_all_orientadores()
                    if not lista_orientadores:
                        print("  > Aviso: Nenhum orientador no banco de dados para usar como referência...")
                    
                    dados_resultado = self.parser.parse_noticia(
                        titulo, 
                        caminho_pdf_principal,
                        caminhos_pdf_projetos,
                        orientadores_conhecidos=lista_orientadores,
                        data_publicacao=data_publicacao
                    )
                    if dados_resultado and dados_resultado.get('aprovados'):
                        self.db_manager.atualizar_bolsas_com_resultado(dados_resultado['aprovados'])
                        novos_editais_processados += 1

            except Exception as e:
                print(f"  > Erro inesperado ao processar o edital '{titulo}': {e}")
            finally:
                self._cleanup_temp_files(all_files_paths)
                
        return novos_editais_processados

    def _cleanup_temp_files(self, file_paths):
        for path in file_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as e:
                    print(f"  > Erro ao remover arquivo temporário {path}: {e}")
