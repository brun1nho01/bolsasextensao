import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  BolsasResponse,
  Bolsa,
  FilterParams,
  RankingResponse,
  EditaisResponse,
  Metadata,
} from "@/types/api";
import { useViewSession } from "./useViewSession";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? "" : "http://127.0.0.1:8000");

// 1. Centralized API Fetcher
const apiFetcher = async <T>(
  endpoint: string,
  params?: URLSearchParams
): Promise<T> => {
  const url = `${API_BASE_URL}${endpoint}${params ? `?${params}` : ""}`;
  try {
    const response = await fetch(url);
    if (!response.ok) {
      // Tenta extrair uma mensagem de erro da API, se houver
      const errorData = await response.json().catch(() => null);
      throw new Error(
        errorData?.detail || `Erro na requisição: ${response.statusText}`
      );
    }
    return response.json();
  } catch (error) {
    // Exibe a notificação de erro para o usuário
    toast.error("Erro de API", {
      description:
        error instanceof Error
          ? error.message
          : "Não foi possível conectar ao servidor.",
    });
    // Relança o erro para que o React Query possa gerenciá-lo
    throw error;
  }
};

// Fetch metadata
export const fetchMetadata = () => {
  // Usamos o fetcher diretamente, pois não precisa ser um hook do React Query
  return apiFetcher<Metadata>("/api/metadata");
};

// Fetch bolsas with filters
export const useBolsas = (filters: FilterParams = {}) => {
  return useQuery<BolsasResponse, Error>({
    queryKey: ["bolsas", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      // Converte apenas filtros válidos para parâmetros de URL
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
      return apiFetcher<BolsasResponse>("/api/bolsas", params);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Fetch single bolsa details WITHOUT incrementing view count
export const useBolsaData = (id: string) => {
  return useQuery<Bolsa, Error>({
    queryKey: ["bolsa-data", id],
    queryFn: () => apiFetcher<Bolsa>(`/api/bolsas/${id}?increment_view=false`),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Increment view count for a bolsa (only if not viewed in this session)
export const useIncrementBolsaView = () => {
  return useMutation({
    mutationFn: async ({
      bolsaId,
      sessionId,
    }: {
      bolsaId: string;
      sessionId: string;
    }) => {
      const response = await fetch(
        `${API_BASE_URL}/api/bolsas/${bolsaId}/increment-view`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ session_id: sessionId }),
        }
      );
      if (!response.ok) {
        throw new Error("Failed to increment view");
      }
      return response.json();
    },
  });
};

// Fetch single bolsa details WITH session-aware view tracking
export const useBolsa = (id: string) => {
  const { sessionId, hasViewedBolsa, markBolsaAsViewed } = useViewSession();
  const incrementViewMutation = useIncrementBolsaView();

  return useQuery<Bolsa, Error>({
    queryKey: ["bolsa", id],
    queryFn: async () => {
      // Primeiro, busca os dados da bolsa sem incrementar views
      const bolsa = await apiFetcher<Bolsa>(
        `/api/bolsas/${id}?increment_view=false`
      );

      // Verifica se já foi vista nesta sessão
      if (!hasViewedBolsa(id)) {
        // Primeira vez que vê nesta sessão - incrementa view
        try {
          await incrementViewMutation.mutateAsync({ bolsaId: id, sessionId });
          markBolsaAsViewed(id);

          // Atualiza o contador local para UI responsiva
          bolsa.view_count = (bolsa.view_count || 0) + 1;

          // View incrementada com sucesso
          if (process.env.NODE_ENV === "development") {
            console.log(
              `📊 View incrementada para bolsa ${id} (sessão: ${sessionId.slice(
                0,
                8
              )}...)`
            );
          }
        } catch (error) {
          if (process.env.NODE_ENV === "development") {
            console.warn("Erro ao incrementar view:", error);
          }
          // Marca como vista mesmo se falhou, para não ficar tentando
          markBolsaAsViewed(id);
        }
      } else {
        if (process.env.NODE_ENV === "development") {
          console.log(
            `👁️ Bolsa ${id} já foi vista nesta sessão - não incrementando`
          );
        }
      }

      return bolsa;
    },
    enabled: !!id,
    staleTime: 30 * 1000, // 30 seconds - menor cache para refletir mudanças de view
    retry: 1, // Reduz tentativas para não inflar views
  });
};

// Fetch ranking
export const useRanking = () => {
  return useQuery<RankingResponse, Error>({
    queryKey: ["ranking"],
    queryFn: () => apiFetcher<RankingResponse>("/api/ranking"),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Fetch editais
export const useEditais = () => {
  return useQuery<EditaisResponse, Error>({
    queryKey: ["editais"],
    queryFn: () => apiFetcher<EditaisResponse>("/api/editais"),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Trigger scrape
export const useScrape = () => {
  return useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/scrape/start`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error("Failed to start scrape");
      }
      return response.json();
    },
  });
};
