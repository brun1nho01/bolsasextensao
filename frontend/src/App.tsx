import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, useQueryClient } from "@tanstack/react-query";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { createSyncStoragePersister } from "@tanstack/query-sync-storage-persister";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import { compareVersions } from "compare-versions";
import { fetchMetadata } from "@/hooks/useApi";
import { toast } from "sonner";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import TelegramFloatingButton from "./components/TelegramFloatingButton";
// 🐛 DEBUG: Importe apenas durante desenvolvimento
// import { ViewSessionDebug } from "./components/debug/ViewSessionDebug";

const CACHE_VERSION_KEY = "uenf-bolsas-cache-version";
const APP_VERSION = import.meta.env.PACKAGE_VERSION || "0.0.0";

// Lógica de verificação de versão e cache
const VersionChecker = () => {
  const queryClient = useQueryClient();

  useEffect(() => {
    const checkVersionAndData = async () => {
      try {
        console.log(`[Cache Check] Versão atual do app: ${APP_VERSION}`);
        const metadata = await fetchMetadata();

        // 1. Verificação da Versão do Código (Hard Refresh)
        if (
          compareVersions(APP_VERSION, metadata.minimum_frontend_version) < 0
        ) {
          console.warn(
            `[Cache Check] Frontend desatualizado! Versão local: ${APP_VERSION}, Mínima necessária: ${metadata.minimum_frontend_version}. Forçando hard refresh.`
          );
          toast.warning("Uma nova versão está disponível!", {
            description:
              "A página será atualizada para carregar a nova versão.",
            duration: 5000,
            onDismiss: () => window.location.reload(),
          });
          // Limpa o cache de dados antes de recarregar
          await queryClient.invalidateQueries();
          return; // Interrompe a execução para aguardar o refresh
        }

        // 2. Verificação da Versão dos Dados (Soft Invalidation)
        const lastKnownDataUpdate = localStorage.getItem(CACHE_VERSION_KEY);
        if (lastKnownDataUpdate !== metadata.last_data_update) {
          console.log(
            `[Cache Check] Novos dados detectados! Limpando cache de queries. Local: ${lastKnownDataUpdate}, Servidor: ${metadata.last_data_update}`
          );
          toast.info("Dados atualizados!", {
            description: "Novas bolsas e editais foram carregados.",
            duration: 3000,
          });
          // Invalida todas as queries para forçar a busca de novos dados
          await queryClient.invalidateQueries();
          localStorage.setItem(CACHE_VERSION_KEY, metadata.last_data_update);
        } else {
          console.log("[Cache Check] Cache de dados está atualizado.");
        }
      } catch (error) {
        console.error("Falha ao verificar metadados:", error);
      }
    };

    checkVersionAndData();
  }, [queryClient]);

  return null; // Este componente não renderiza nada
};

// Configuração do QueryClient para cache padrão e garbage collection
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      gcTime: 1000 * 60 * 60 * 24, // 24 horas
    },
  },
});

// Configuração do persister para salvar o cache no LocalStorage
const persister = createSyncStoragePersister({
  storage: window.localStorage,
});

const App = () => (
  <PersistQueryClientProvider
    client={queryClient}
    persistOptions={{ persister }}
  >
    <TooltipProvider>
      <VersionChecker />
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
      {/* Botão flutuante Telegram - aparece em todas as páginas */}
      <TelegramFloatingButton />
      {/* 🐛 DEBUG: Descomente para ativar debug durante desenvolvimento */}
      {/* {process.env.NODE_ENV === 'development' && <ViewSessionDebug />} */}
    </TooltipProvider>
  </PersistQueryClientProvider>
);

export default App;
