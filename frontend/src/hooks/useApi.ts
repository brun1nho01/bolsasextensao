import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
      const errorMessage =
        errorData?.detail || `Erro na requisição: ${response.statusText}`;
      // Lança o erro detalhado para ser pego pelo React Query e logado no console
      throw new Error(errorMessage);
    }
    return response.json();
  } catch (error) {
    // Loga o erro detalhado no console para depuração
    console.error("Erro detalhado da API:", error);

    // Exibe uma notificação de erro genérica para o usuário
    toast.error("Ops! Ocorreu um erro", {
      description:
        "Não foi possível conectar ao servidor. Por favor, tente novamente mais tarde.",
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

// Fetcher for a single bolsa (not a hook)
export const fetchBolsa = (id: string, increment: boolean = false) => {
  return apiFetcher<Bolsa>(`/api/bolsas/${id}?increment_view=${increment}`);
};

// Fetch bolsas with filters
export const useBolsas = (
  filters: FilterParams = {},
  enabled: boolean = true
) => {
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
    enabled, // Só executa a query se enabled for true
  });
};

// Fetch single bolsa details, replacing the old useBolsaData
export const useBolsa = (id: string | null) => {
  return useQuery<Bolsa, Error>({
    queryKey: ["bolsa", id],
    queryFn: () => fetchBolsa(id, false),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Increment view count for a bolsa (only if not viewed in this session)
export const useIncrementBolsaView = () => {
  const queryClient = useQueryClient();

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
    // Optimistic update for instant UI feedback
    onMutate: async (variables) => {
      await queryClient.cancelQueries({
        queryKey: ["bolsa", variables.bolsaId],
      });
      const previousBolsa = queryClient.getQueryData<Bolsa>([
        "bolsa",
        variables.bolsaId,
      ]);

      if (previousBolsa) {
        queryClient.setQueryData<Bolsa>(["bolsa", variables.bolsaId], {
          ...previousBolsa,
          view_count: (previousBolsa.view_count || 0) + 1,
        });
      }
      return { previousBolsa };
    },
    onError: (err, variables, context) => {
      if (context?.previousBolsa) {
        queryClient.setQueryData(
          ["bolsa", variables.bolsaId],
          context.previousBolsa
        );
      }
    },
    onSettled: (data, error, variables) => {
      queryClient.invalidateQueries({ queryKey: ["bolsa", variables.bolsaId] });
      // Also invalidate ranking and bolsa list to reflect new view count eventually
      queryClient.invalidateQueries({ queryKey: ["ranking"] });
      queryClient.invalidateQueries({ queryKey: ["bolsas"] });
    },
  });
};

// Fetch ranking
export const useRanking = (enabled: boolean = true) => {
  return useQuery<RankingResponse, Error>({
    queryKey: ["ranking"],
    queryFn: () => apiFetcher<RankingResponse>("/api/ranking"),
    staleTime: 10 * 60 * 1000, // 10 minutes
    enabled, // Só executa a query se enabled for true
  });
};

// Fetch editais
export const useEditais = (enabled: boolean = true) => {
  return useQuery<EditaisResponse, Error>({
    queryKey: ["editais"],
    queryFn: () => apiFetcher<EditaisResponse>("/api/editais"),
    staleTime: 30 * 60 * 1000, // 30 minutes
    enabled, // Só executa a query se enabled for true
  });
};
