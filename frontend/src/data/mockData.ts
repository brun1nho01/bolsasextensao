import { Bolsa, Edital } from "@/types/api";

// Mock data para demonstração quando a API não estiver disponível
export const mockBolsas: Bolsa[] = [
  {
    id: "1",
    tipo: "Bolsa Extensão Discente UENF",
    status: "disponivel",
    nome_projeto: "Desenvolvimento de Sistema de Monitoramento Ambiental",
    orientador: "Prof. Dr. João Silva Santos",
    created_at: "2025-01-15T10:00:00Z",
    view_count: 127,
    descricao:
      "Este projeto visa desenvolver uma plataforma integrada para monitoramento em tempo real de parâmetros ambientais críticos, incluindo qualidade do ar, níveis de poluição sonora e dados meteorológicos. O sistema utilizará sensores IoT, machine learning para análise preditiva e uma interface web responsiva para visualização dos dados coletados.",
  },
  {
    id: "2",
    tipo: "Bolsa Pesquisa UENF",
    status: "preenchida",
    candidato_aprovado: "Maria Fernanda Costa",
    nome_projeto: "Análise de Dados Climáticos usando Machine Learning",
    orientador: "Prof. Dra. Ana Paula Rodrigues",
    created_at: "2025-01-10T14:30:00Z",
    view_count: 89,
    descricao:
      "Projeto de pesquisa focado na aplicação de algoritmos de aprendizado de máquina para análise e predição de padrões climáticos. Utilizando redes neurais profundas e técnicas de análise de séries temporais, o projeto busca desenvolver modelos preditivos para eventos climáticos extremos e mudanças sazonais.",
  },
  {
    id: "3",
    tipo: "Bolsa Extensão Discente UENF",
    status: "aberta",
    nome_projeto: "Aplicativo Mobile para Gestão Rural",
    orientador: "Prof. Dr. Carlos Eduardo Lima",
    created_at: "2025-01-20T09:15:00Z",
    view_count: 156,
    descricao:
      "Desenvolvimento de aplicativo móvel multiplataforma para auxiliar produtores rurais na gestão de suas propriedades. O app incluirá funcionalidades como controle de estoque, monitoramento de culturas, gestão financeira, previsão do tempo e marketplace para venda direta de produtos agrícolas.",
  },
  {
    id: "4",
    tipo: "Bolsa Pesquisa UENF",
    status: "aguardando",
    nome_projeto: "Estudo de Biodiversidade na Mata Atlântica",
    orientador: "Prof. Dr. Roberto Mendes",
    created_at: "2025-01-12T16:45:00Z",
    view_count: 73,
    descricao:
      "Pesquisa interdisciplinar para catalogar e estudar a biodiversidade da fauna e flora na região da Mata Atlântica do Norte Fluminense. O projeto envolve coleta de dados em campo, análise genética de espécies, mapeamento de habitats e desenvolvimento de estratégias de conservação sustentável.",
  },
  {
    id: "5",
    tipo: "Bolsa Extensão Discente UENF",
    status: "preenchida",
    candidato_aprovado: "Pedro Augusto Silva",
    nome_projeto: "Desenvolvimento de Jogos Educativos",
    orientador: "Prof. Dra. Luciana Souza",
    created_at: "2025-01-08T11:20:00Z",
    view_count: 201,
    descricao:
      "Criação de jogos educativos digitais para o ensino de matemática e ciências em escolas públicas. Os jogos utilizarão elementos de gamificação, realidade aumentada e inteligência artificial para personalizar a experiência de aprendizagem de cada estudante, tornando o ensino mais interativo e eficaz.",
  },
  {
    id: "6",
    tipo: "Bolsa Pesquisa UENF",
    status: "disponivel",
    nome_projeto: "Inteligência Artificial aplicada à Agricultura",
    orientador: "Prof. Dr. Fernando Oliveira",
    created_at: "2025-01-18T13:00:00Z",
    view_count: 234,
    descricao:
      "Projeto de pesquisa em agricultura de precisão utilizando IA para otimização de cultivos. Inclui desenvolvimento de sistemas de visão computacional para detecção de pragas e doenças, algoritmos de otimização para irrigação inteligente e modelos preditivos para maximização de produtividade agrícola.",
  },
  {
    id: "7",
    tipo: "Bolsa Extensão Discente UENF",
    status: "aberta",
    nome_projeto: "Plataforma de E-learning para Comunidades Rurais",
    orientador: "Prof. Dra. Patrícia Moreira",
    created_at: "2025-01-14T08:30:00Z",
    view_count: 98,
    descricao:
      "Desenvolvimento de plataforma digital de ensino à distância especializada em capacitação para comunidades rurais. A plataforma oferecerá cursos sobre técnicas agrícolas sustentáveis, gestão rural, tecnologias digitais e empreendedorismo, com foco na inclusão digital e desenvolvimento socioeconômico local.",
  },
  {
    id: "8",
    tipo: "Bolsa Pesquisa UENF",
    status: "disponivel",
    nome_projeto: "Análise de Qualidade da Água em Reservatórios",
    orientador: "Prof. Dr. Marcelo Barbosa",
    created_at: "2025-01-16T15:10:00Z",
    view_count: 67,
    descricao:
      "Estudo abrangente sobre a qualidade da água em reservatórios da região Norte Fluminense, utilizando técnicas avançadas de análise química, microbiológica e sensoriamento remoto. O projeto visa desenvolver indicadores de qualidade da água e protocolos de monitoramento para garantir a segurança hídrica da população.",
  },
];

export const mockEditais: Edital[] = [
  {
    id: "1",
    titulo: "Edital PIBEX 2025.1 - Bolsas de Extensão",
    data_publicacao: "2025-01-05T09:00:00Z",
    data_limite: "2025-02-15T23:59:59Z",
    status: "ativo",
    descricao:
      "Programa Institucional de Bolsas de Extensão voltado para projetos que promovam a interação entre universidade e sociedade.",
  },
  {
    id: "2",
    titulo: "Edital PIBIC 2025.1 - Bolsas de Iniciação Científica",
    data_publicacao: "2025-01-10T10:00:00Z",
    data_limite: "2025-02-20T23:59:59Z",
    status: "ativo",
    descricao:
      "Programa Institucional de Bolsas de Iniciação Científica para desenvolvimento de pesquisas científicas.",
  },
  {
    id: "3",
    titulo: "Edital Especial - Projetos de Sustentabilidade",
    data_publicacao: "2024-12-15T14:00:00Z",
    data_limite: "2025-01-30T23:59:59Z",
    status: "ativo",
    descricao:
      "Edital específico para projetos focados em sustentabilidade ambiental e desenvolvimento sustentável.",
  },
  {
    id: "4",
    titulo: "Edital PIBEX 2024.2 - Bolsas de Extensão",
    data_publicacao: "2024-08-01T09:00:00Z",
    data_limite: "2024-09-15T23:59:59Z",
    status: "encerrado",
    descricao:
      "Programa Institucional de Bolsas de Extensão do segundo semestre de 2024.",
  },
  {
    id: "5",
    titulo: "Edital Futuro - Inovação Tecnológica 2025.2",
    data_publicacao: "2025-06-01T10:00:00Z",
    data_limite: "2025-07-15T23:59:59Z",
    status: "em_breve",
    descricao:
      "Edital especial para projetos de inovação tecnológica e desenvolvimento de soluções digitais.",
  },
];

// Função para simular delay de API
export const delay = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

// Funções para simular chamadas da API
export const fetchMockBolsas = async (filters: any = {}) => {
  await delay(800); // Simula delay da API

  let filteredBolsas = [...mockBolsas];

  // Aplicar filtros
  if (filters.status && filters.status !== "all") {
    filteredBolsas = filteredBolsas.filter(
      (bolsa) => bolsa.status === filters.status
    );
  }

  if (filters.q) {
    const query = filters.q.toLowerCase();
    filteredBolsas = filteredBolsas.filter(
      (bolsa) =>
        bolsa.nome_projeto.toLowerCase().includes(query) ||
        bolsa.orientador.toLowerCase().includes(query) ||
        bolsa.tipo.toLowerCase().includes(query)
    );
  }

  // Ordenação
  if (filters.sort) {
    filteredBolsas.sort((a, b) => {
      let aValue, bValue;

      switch (filters.sort) {
        case "view_count":
          aValue = a.view_count;
          bValue = b.view_count;
          break;
        case "created_at":
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
          break;
        case "nome_projeto":
          aValue = a.nome_projeto.toLowerCase();
          bValue = b.nome_projeto.toLowerCase();
          break;
        case "orientador":
          aValue = a.orientador.toLowerCase();
          bValue = b.orientador.toLowerCase();
          break;
        default:
          return 0;
      }

      if (filters.order === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  }

  // Paginação
  const page = filters.page || 1;
  const pageSize = filters.page_size || 12;
  const startIndex = (page - 1) * pageSize;
  const endIndex = startIndex + pageSize;

  return {
    items: filteredBolsas.slice(startIndex, endIndex),
    total: filteredBolsas.length,
    page,
    page_size: pageSize,
    total_pages: Math.ceil(filteredBolsas.length / pageSize),
  };
};

export const fetchMockRanking = async () => {
  await delay(500);

  // Ordenar por view_count decrescente
  const sortedBolsas = [...mockBolsas].sort(
    (a, b) => b.view_count - a.view_count
  );

  return {
    items: sortedBolsas.slice(0, 10), // Top 10
  };
};

export const fetchMockEditais = async () => {
  await delay(600);

  return {
    items: mockEditais,
  };
};
