from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
import uuid

class Bolsa(BaseModel):
    id: uuid.UUID
    projeto_id: Optional[uuid.UUID] = None
    tipo: Optional[str] = None
    vagas: Optional[int] = None
    numero_perfil: Optional[str] = None
    requisito: Optional[str] = None
    status: str = 'disponivel'
    candidato_aprovado: Optional[str] = None
    created_at: datetime
    view_count: Optional[int] = 0

    class Config:
        from_attributes = True

# Novo modelo para refletir a estrutura da VIEW do banco de dados
class BolsaComProjeto(BaseModel):
    id: uuid.UUID
    projeto_id: uuid.UUID
    tipo: str
    vagas: int
    numero_perfil: Optional[str] = None
    requisito: Optional[str] = None
    status: str
    created_at: datetime
    data_publicacao: Optional[date] = None
    data_fim_inscricao: Optional[date] = None
    data_divulgacao_resultado: Optional[date] = None  # NOVO CAMPO
    candidato_aprovado: Optional[str] = None
    view_count: int
    remuneracao: Optional[float] = None
    edital_id: uuid.UUID
    nome_projeto: str
    orientador: str
    resumo: Optional[str] = None
    centro: Optional[str] = None
    edital_nome: str
    url_edital: str
    fts: Optional[str] = None

class BolsasResponse(BaseModel):
    bolsas: List[BolsaComProjeto]
    total: int
    page: int
    page_size: int
    total_pages: int
    # 🆕 CAMPOS PARA CONTAGEM DE VAGAS
    total_vagas: Optional[int] = None  # Soma total de vagas
    vagas_preenchidas: Optional[int] = None  # Soma de vagas preenchidas

class Projeto(BaseModel):
    id: uuid.UUID
    edital_id: Optional[uuid.UUID] = None
    nome_projeto: str
    orientador: Optional[str] = None
    centro: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class Edital(BaseModel):
    id: uuid.UUID
    titulo: str
    link: str
    data_fim_inscricao: Optional[date] = None
    data_publicacao: Optional[date] = None
    data_divulgacao_resultado: Optional[date] = None  # NOVO CAMPO
    created_at: datetime

    class Config:
        from_attributes = True

