from backend.utils import get_match_key

def test_get_match_key_com_acentos():
    """Testa se a função remove acentos corretamente."""
    assert get_match_key("PROJETO DE EXTENSÃO CIENTÍFICA") == "PROJETO DE EXTENSAO CIENTIFICA"

def test_get_match_key_com_pontuacao():
    """Testa se a função remove pontuação."""
    assert get_match_key("Bolsas-UENF: Edital Nº 01/2025.") == "BOLSAS UENF EDITAL Nº 012025"

def test_get_match_key_com_espacos_extras():
    """Testa se a função normaliza múltiplos espaços."""
    assert get_match_key("  Múltiplos   espaços  ") == "MULTIPLOS ESPACOS"

def test_get_match_key_string_vazia():
    """Testa se a função lida com strings vazias."""
    assert get_match_key("") == ""

def test_get_match_key_texto_complexo():
    """Testa uma combinação de todos os casos."""
    texto = "  Resultado da Seleção (Edital PROEX/UENF Nº 25) - Apoio Acadêmico  "
    esperado = "RESULTADO DA SELECAO EDITAL PROEXUENF Nº 25 APOIO ACADEMICO"
    assert get_match_key(texto) == esperado
