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

// Fetch single bolsa details
export const useBolsa = (id: string) => {
  return useQuery<Bolsa, Error>({
    queryKey: ["bolsa", id],
    queryFn: () => apiFetcher<Bolsa>(`/api/bolsas/${id}`),
    enabled: !!id, // A query só será executada se o ID existir
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
    staleTime: 15 * 60 * 1000, // 15 minutes
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
