import { useCallback, useMemo } from "react";
import { v4 as uuidv4 } from "uuid";

// Chave para armazenar dados da sessão
const SESSION_KEY = "uenf-view-session";
const VIEWED_BOLSAS_KEY = "uenf-viewed-bolsas";

interface ViewSession {
  sessionId: string;
  startTime: number;
  viewedBolsas: Set<string>;
}

/**
 * Hook para gerenciar views únicas por sessão do navegador
 * Previne contagem múltipla de views para a mesma bolsa na mesma sessão
 */
export const useViewSession = () => {
  // Gera ou recupera session ID
  const session = useMemo((): ViewSession => {
    try {
      const storedSession = sessionStorage.getItem(SESSION_KEY);
      const viewedBolsasStr = sessionStorage.getItem(VIEWED_BOLSAS_KEY);

      if (storedSession) {
        const parsed = JSON.parse(storedSession);
        const viewedBolsas = viewedBolsasStr
          ? new Set(JSON.parse(viewedBolsasStr))
          : new Set<string>();

        return {
          sessionId: parsed.sessionId,
          startTime: parsed.startTime,
          viewedBolsas,
        };
      }
    } catch (error) {
      console.warn("Erro ao recuperar sessão:", error);
    }

    // Criar nova sessão
    const newSession: ViewSession = {
      sessionId: uuidv4(),
      startTime: Date.now(),
      viewedBolsas: new Set<string>(),
    };

    // Salvar no sessionStorage
    try {
      sessionStorage.setItem(
        SESSION_KEY,
        JSON.stringify({
          sessionId: newSession.sessionId,
          startTime: newSession.startTime,
        })
      );
      sessionStorage.setItem(VIEWED_BOLSAS_KEY, JSON.stringify([]));
    } catch (error) {
      console.warn("Erro ao salvar sessão:", error);
    }

    return newSession;
  }, []);

  /**
   * Verifica se uma bolsa já foi vista nesta sessão
   */
  const hasViewedBolsa = useCallback(
    (bolsaId: string): boolean => {
      return session.viewedBolsas.has(bolsaId);
    },
    [session.viewedBolsas]
  );

  /**
   * Marca uma bolsa como vista nesta sessão
   * Retorna true se foi a primeira vez, false se já tinha sido vista
   */
  const markBolsaAsViewed = useCallback(
    (bolsaId: string): boolean => {
      if (session.viewedBolsas.has(bolsaId)) {
        return false; // Já foi vista
      }

      // Adiciona à sessão atual
      session.viewedBolsas.add(bolsaId);

      // Persiste no sessionStorage
      try {
        const viewedArray = Array.from(session.viewedBolsas);
        sessionStorage.setItem(VIEWED_BOLSAS_KEY, JSON.stringify(viewedArray));
      } catch (error) {
        console.warn("Erro ao salvar bolsa vista:", error);
      }

      return true; // Primeira vez vista
    },
    [session.viewedBolsas]
  );

  /**
   * Limpa todas as bolsas vistas (útil para debug ou reset)
   */
  const clearViewedBolsas = useCallback(() => {
    session.viewedBolsas.clear();
    try {
      sessionStorage.setItem(VIEWED_BOLSAS_KEY, JSON.stringify([]));
    } catch (error) {
      console.warn("Erro ao limpar bolsas vistas:", error);
    }
  }, [session.viewedBolsas]);

  /**
   * Estatísticas da sessão atual
   */
  const getSessionStats = useCallback(() => {
    const now = Date.now();
    const sessionDuration = now - session.startTime;

    return {
      sessionId: session.sessionId,
      duration: sessionDuration,
      durationFormatted: formatDuration(sessionDuration),
      viewedCount: session.viewedBolsas.size,
      viewedBolsas: Array.from(session.viewedBolsas),
    };
  }, [session]);

  return {
    sessionId: session.sessionId,
    hasViewedBolsa,
    markBolsaAsViewed,
    clearViewedBolsas,
    getSessionStats,
  };
};

/**
 * Formata duração em milissegundos para string legível
 */
function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}
