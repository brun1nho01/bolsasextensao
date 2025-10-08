// A interface Bolsa representa o modelo BolsaComProjeto do backend.
// Foi totalmente alinhada com os campos enviados pela API.
export interface Bolsa {
  id: string;
  projeto_id: string;
  tipo: string;
  remuneracao: number | null;
  vagas: number;
  numero_perfil: string | null;
  requisito: string | null;
  status: "disponivel" | "preenchida" | "aguardando" | "aberta";
  candidato_aprovado: string | null;
  created_at: string; // (datetime)
  data_publicacao: string | null; // (date)
  data_fim_inscricao: string | null; // (date)
  data_divulgacao_resultado: string | null; // (date) - NOVO CAMPO
  view_count: number;
  edital_id: string;
  nome_projeto: string;
  orientador: string;
  resumo: string | null;
  centro: string | null;
  edital_nome: string;
  url_edital: string;
  // 🆕 CAMPOS PARA AGRUPAMENTO
  vagas_total?: number; // Total de vagas do grupo
  vagas_preenchidas?: number; // Quantidade preenchidas
  vagas_disponiveis?: number; // Quantidade disponíveis
}

export interface BolsasResponse {
  bolsas: Bolsa[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  agrupadas?: boolean; // 🆕 Indica se são bolsas agrupadas
  // 🆕 CAMPOS PARA CONTAGEM DE VAGAS
  total_vagas?: number; // Soma total de vagas (222)
  vagas_preenchidas?: number; // Soma de vagas preenchidas
}

// A interface Edital foi corrigida para refletir os dados reais do backend.
export interface Edital {
  id: string;
  titulo: string;
  link: string;
  data_fim_inscricao: string | null; // (date)
  data_publicacao: string | null; // (date)
  data_divulgacao_resultado: string | null; // (date) - NOVO CAMPO
  modalidade?: string; // ← NOVO: "extensao" ou "apoio_academico"
  created_at: string; // (datetime)
}

export interface FilterParams {
  page?: number;
  page_size?: number;
  status?: string;
  q?: string;
  sort?: string;
  order?: "asc" | "desc";
  centro?: string;
  tipo?: string;
  // O filtro de orientador é tratado pelo campo 'q' (busca geral)
}

// O endpoint de ranking retorna um array de Bolsas diretamente.
export type RankingResponse = Bolsa[];

// O endpoint de editais retorna um array de Editais diretamente.
export type EditaisResponse = Edital[];

export interface Metadata {
  last_data_update: string; // ISO 8601 datetime string
  minimum_frontend_version: string; // Ex: "1.0.0"
}
