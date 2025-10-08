import unicodedata
import re

def get_match_key(text: str) -> str:
    """
    Normalização para COMPARAÇÃO de strings (nomes, etc.).
    Remove acentos, pontuação e normaliza espaços.
    """
    if not isinstance(text, str):
        return ""
    try:
        # Etapa 1: Remover acentos
        text_sem_acentos = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        
        # Etapa 2: Substituir apenas pontuações que separam palavras por espaço
        # Hífen, dois pontos, parênteses
        text_com_espacos = re.sub(r'[\-:\(\)]', ' ', text_sem_acentos)
        
        # Etapa 3: Remover o restante da pontuação (como /, .)
        text_sem_pontuacao = re.sub(r'[^\w\s]', '', text_com_espacos)
        
        # Etapa 4: Converter para maiúsculas e normalizar espaços
        text_upper = text_sem_pontuacao.upper()
        return " ".join(text_upper.split())
    except Exception:
        return ""
