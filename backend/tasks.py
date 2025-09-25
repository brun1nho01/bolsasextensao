import os
from dotenv import load_dotenv
from scraper import UenfScraper
from parser import UenfParser
from database import SupabaseManager
import sys
from datetime import datetime, timezone
import logging

# 🔇 Configuração de Logging para Limpar os Logs
# Silencia logs informativos do httpx (usado pela biblioteca do Supabase)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Adiciona o diretório raiz do projeto ao sys.path
# Isso garante que os módulos sejam encontrados ao executar como script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_scraping_task():
    """
    Orquestra o processo de scraping, parsing e armazenamento dos dados.
    """
    try:
        # A API já terá carregado as variáveis de ambiente, mas para execução manual é bom garantir.
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            print("Erro: Variáveis de ambiente do Supabase não encontradas.")
            raise ValueError("SUPABASE_URL e SUPABASE_KEY são necessárias.")

        db_manager = SupabaseManager(supabase_url=supabase_url, supabase_key=supabase_key)
        parser = UenfParser()
        
        # Agora busca em mais páginas, começando da primeira (mais recente)
        # A lógica inteligente no scraper irá parar a busca quando encontrar editais antigos
        paginas_para_raspar = range(1, 6) # Tenta buscar das páginas 1 a 5
        
        total_novos_editais = 0
        for page_num in paginas_para_raspar:
            # Processando página
            
            scraper = UenfScraper(parser=parser, db_manager=db_manager, page_num=page_num)
            novos_editais_encontrados = scraper.fetch_news()
            total_novos_editais += novos_editais_encontrados

            # Se a página não retornou nenhum edital novo, podemos parar de procurar em páginas mais antigas
            if novos_editais_encontrados == 0 and page_num > 1:
                # Nenhum edital novo, interrompendo busca
                break
        
        # Se pelo menos um edital novo foi processado, atualiza o timestamp no banco
        if total_novos_editais > 0:
            timestamp_utc = datetime.now(timezone.utc).isoformat()
            db_manager.update_last_data_update(timestamp_utc)

        # Processo concluído

    except Exception as e:
        print(f"Ocorreu um erro inesperado na tarefa de scraping: {e}")
        import traceback
        traceback.print_exc()
    
    # Fim da tarefa de scraping

if __name__ == "__main__":
    # Execução manual do scraping
    # Garante que o .env na pasta 'backend' seja carregado ao rodar o script diretamente
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=dotenv_path)
    run_scraping_task()
