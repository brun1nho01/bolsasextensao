import { useReducer, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { HeroSection } from "@/components/layout/hero-section";
import { AdvancedFilters } from "@/components/filters/advanced-filters";
import { BolsaGrid } from "@/components/bolsas/bolsa-grid";
import { BolsaList } from "@/components/bolsas/bolsa-list";
import { RankingPodium } from "@/components/ranking/ranking-podium";
import { EditaisTimeline } from "@/components/editais/editais-timeline";
import { BolsaDetailsModal } from "@/components/modals/bolsa-details-modal";
import { useBolsas, useRanking, useEditais, useBolsa } from "@/hooks/useApi";
import { useDeviceType } from "@/hooks/use-mobile";
import { Bolsa } from "@/types/api";
import { Button } from "@/components/ui/button";
import { TrendingUp, Calendar, LayoutGrid, Filter } from "lucide-react";
import { ScrollingBackgroundProvider } from "@/components/layout/scrolling-background";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { ViewToggle } from "@/components/ui/view-toggle";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

// 1. Definir a estrutura do estado dos filtros
type FilterState = {
  q: string;
  status: string;
  tipo: string;
  orientador: string;
  centro: string;
  sort: string;
  order: "asc" | "desc";
  page: number;
};

type Section = "bolsas" | "ranking" | "editais";

// 2. Definir as ações que podem modificar o estado
type FilterAction =
  | { type: "SET_FILTER"; payload: Partial<FilterState> }
  | { type: "SET_PAGE"; payload: number }
  | { type: "SET_SEARCH"; payload: string }
  | { type: "CLEAR_FILTERS" };

const initialState: FilterState = {
  q: "",
  status: "all",
  tipo: "all",
  orientador: "all",
  centro: "all",
  sort: "nome_projeto",
  order: "asc",
  page: 1,
};

// 3. Criar a função reducer
function filtersReducer(state: FilterState, action: FilterAction): FilterState {
  switch (action.type) {
    case "SET_FILTER":
      return { ...state, ...action.payload, page: 1 }; // Reseta a página em qualquer filtro
    case "SET_PAGE":
      return { ...state, page: action.payload };
    case "SET_SEARCH":
      return { ...state, q: action.payload, page: 1 }; // Reseta a página na busca
    case "CLEAR_FILTERS":
      return { ...initialState, sort: state.sort, order: state.order }; // Mantém a ordenação
    default:
      return state;
  }
}

// Função para inicializar o estado a partir da URL
const initializer = (searchParams: URLSearchParams): FilterState => {
  return {
    q: searchParams.get("q") || initialState.q,
    status: searchParams.get("status") || initialState.status,
    tipo: searchParams.get("tipo") || initialState.tipo,
    orientador: searchParams.get("orientador") || initialState.orientador,
    centro: searchParams.get("centro") || initialState.centro,
    sort: searchParams.get("sort") || initialState.sort,
    order: (searchParams.get("order") as "asc" | "desc") || initialState.order,
    page: parseInt(searchParams.get("page") || "1", 10),
  };
};

const Index = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const { isMobile, isTablet, isDesktop } = useDeviceType();

  // 4. Substituir múltiplos useStates por um único useReducer
  const [filters, dispatch] = useReducer(
    filtersReducer,
    searchParams,
    initializer
  );

  // Estados que não são filtros permanecem como useState
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selectedBolsaId, setSelectedBolsaId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const currentSection = (searchParams.get("section") as Section) || "bolsas";

  const handleSetCurrentSection = (section: Section) => {
    const params = new URLSearchParams(searchParams);
    params.set("section", section);
    // Ao trocar de aba, removemos os filtros de bolsa e a paginação
    params.delete("q");
    params.delete("status");
    params.delete("tipo");
    params.delete("orientador");
    params.delete("centro");
    params.delete("sort");
    params.delete("order");
    params.delete("page");
    setSearchParams(params);
    // Limpa o estado dos filtros também
    dispatch({ type: "CLEAR_FILTERS" });
  };

  // 5. Sincronizar o estado do reducer com a URL (apenas para filtros de bolsa)
  useEffect(() => {
    // Este efeito só deve rodar se a seção for 'bolsas'
    if (currentSection !== "bolsas") return;

    const params = new URLSearchParams(searchParams);
    // Adiciona parâmetros à URL apenas se forem diferentes do estado inicial
    if (filters.q) params.set("q", filters.q);
    else params.delete("q");
    if (filters.status !== "all") params.set("status", filters.status);
    else params.delete("status");
    if (filters.tipo !== "all") params.set("tipo", filters.tipo);
    else params.delete("tipo");
    if (filters.orientador !== "all")
      params.set("orientador", filters.orientador);
    else params.delete("orientador");
    if (filters.centro !== "all") params.set("centro", filters.centro);
    else params.delete("centro");
    if (filters.sort !== initialState.sort) params.set("sort", filters.sort);
    else params.delete("sort");
    if (filters.order !== initialState.order)
      params.set("order", filters.order);
    else params.delete("order");
    if (filters.page > 1) params.set("page", filters.page.toString());
    else params.delete("page");

    setSearchParams(params, { replace: true });
  }, [filters, currentSection, setSearchParams]);

  // 6. Preparar filtros para a API usando useMemo para otimização
  const apiFilters = useMemo(() => {
    return {
      page: filters.page,
      page_size: 12,
      q: filters.q || undefined,
      status: filters.status !== "all" ? filters.status : undefined,
      centro: filters.centro !== "all" ? filters.centro : undefined,
      tipo: filters.tipo !== "all" ? filters.tipo : undefined,
      sort: filters.sort,
      order: filters.order,
    };
  }, [filters]);

  // API Hooks
  const { data: bolsasData, isLoading, error } = useBolsas(apiFilters);
  const { data: rankingData } = useRanking();
  const { data: editaisData } = useEditais();
  const { data: preenchidasData } = useBolsas({
    status: "preenchida",
    page_size: 1,
  });
  const { data: totalBolsasData } = useBolsas({ page_size: 1 });
  const { data: selectedBolsaData } = useBolsa(selectedBolsaId || "");

  // 🆕 Usar contagem de vagas ao invés de contagem de bolsas
  const bolsasAtivas = totalBolsasData?.total_vagas ?? totalBolsasData?.total;
  const bolsasPreenchidas =
    totalBolsasData?.vagas_preenchidas ?? preenchidasData?.total;

  useEffect(() => {
    if (error) {
      console.error("Falha ao buscar bolsas:", error);
    }
  }, [error]);

  const handleBolsaClick = (bolsa: Bolsa) => {
    setSelectedBolsaId(bolsa.id);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedBolsaId(null);
    // Invalida as queries de "bolsas" e "ranking" para buscar os dados atualizados
    queryClient.invalidateQueries({ queryKey: ["bolsas"] });
    queryClient.invalidateQueries({ queryKey: ["ranking"] });
  };

  return (
    <>
      <BolsaDetailsModal
        bolsa={selectedBolsaData || null}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />

      <ScrollingBackgroundProvider>
        <main>
          <HeroSection
            onSearch={(query) =>
              dispatch({ type: "SET_SEARCH", payload: query })
            }
            searchQuery={filters.q}
            totalProjetos={bolsasAtivas}
            bolsasPreenchidas={bolsasPreenchidas}
          />

          <div className="container mx-auto px-4 py-8">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center justify-center gap-2 sm:gap-4 mb-12 flex-wrap px-4"
            >
              <Button
                variant={currentSection === "bolsas" ? "default" : "outline"}
                onClick={() => handleSetCurrentSection("bolsas")}
                className={`${
                  currentSection === "bolsas"
                    ? "gradient-primary shadow-glow"
                    : "glass"
                } text-sm sm:text-base`}
              >
                <LayoutGrid className="w-4 h-4 mr-2" />
                Bolsas
              </Button>
              <Button
                variant={currentSection === "ranking" ? "default" : "outline"}
                onClick={() => handleSetCurrentSection("ranking")}
                className={`${
                  currentSection === "ranking"
                    ? "gradient-primary shadow-glow"
                    : "glass"
                } text-sm sm:text-base`}
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                Ranking
              </Button>
              <Button
                variant={currentSection === "editais" ? "default" : "outline"}
                onClick={() => handleSetCurrentSection("editais")}
                className={`${
                  currentSection === "editais"
                    ? "gradient-primary shadow-glow"
                    : "glass"
                } text-sm sm:text-base`}
              >
                <Calendar className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Timeline de </span>Editais
              </Button>
            </motion.div>

            {/* Seção de Bolsas com alternância de view */}
            {currentSection === "bolsas" && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex gap-8"
              >
                {/* Desktop Filters */}
                {isDesktop && (
                  <div className="w-80 flex-shrink-0">
                    <AdvancedFilters
                      filters={filters}
                      onFiltersChange={(payload) =>
                        dispatch({ type: "SET_FILTER", payload })
                      }
                      onClearFilters={() => dispatch({ type: "CLEAR_FILTERS" })}
                      isOpen={filtersOpen}
                      onToggle={() => setFiltersOpen(!filtersOpen)}
                    />
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-center mb-8 flex-wrap gap-4">
                    <div className="flex items-center gap-4">
                      <ViewToggle view={viewMode} onViewChange={setViewMode} />

                      {/* Mobile/Tablet Filter Button */}
                      {(isMobile || isTablet) && (
                        <Sheet open={filtersOpen} onOpenChange={setFiltersOpen}>
                          <SheetTrigger asChild>
                            <Button variant="outline" className="glass">
                              <Filter className="w-4 h-4 mr-2" />
                              Filtros
                            </Button>
                          </SheetTrigger>
                          <SheetContent
                            side={isTablet ? "right" : "bottom"}
                            className={isTablet ? "w-96" : "h-[85vh]"}
                          >
                            <div className="mt-6">
                              <AdvancedFilters
                                filters={filters}
                                onFiltersChange={(payload) =>
                                  dispatch({ type: "SET_FILTER", payload })
                                }
                                onClearFilters={() =>
                                  dispatch({ type: "CLEAR_FILTERS" })
                                }
                                isOpen={true}
                                onToggle={() => {}}
                              />
                            </div>
                          </SheetContent>
                        </Sheet>
                      )}
                    </div>

                    <PaginationControls
                      currentPage={filters.page}
                      totalPages={bolsasData?.total_pages ?? 1}
                      onPageChange={(page) =>
                        dispatch({ type: "SET_PAGE", payload: page })
                      }
                    />
                  </div>

                  {/* Clear Filters Button */}
                  {!isLoading &&
                    (filters.q ||
                      filters.status !== "all" ||
                      filters.centro !== "all" ||
                      filters.tipo !== "all") && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex justify-end mb-6 px-2"
                      >
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => dispatch({ type: "CLEAR_FILTERS" })}
                          className="text-xs hover:bg-muted/50"
                        >
                          Limpar filtros
                        </Button>
                      </motion.div>
                    )}

                  {viewMode === "grid" ? (
                    <BolsaGrid
                      bolsas={bolsasData?.bolsas ?? []}
                      loading={isLoading}
                      onBolsaClick={handleBolsaClick}
                      total={bolsasData?.total}
                    />
                  ) : (
                    <BolsaList
                      bolsas={bolsasData?.bolsas ?? []}
                      loading={isLoading}
                      onBolsaClick={handleBolsaClick}
                      total={bolsasData?.total}
                    />
                  )}
                  <PaginationControls
                    currentPage={filters.page}
                    totalPages={bolsasData?.total_pages ?? 1}
                    onPageChange={(page) =>
                      dispatch({ type: "SET_PAGE", payload: page })
                    }
                    className="mt-8 flex justify-center"
                  />
                </div>
              </motion.div>
            )}

            {/* Seção de Ranking */}
            {currentSection === "ranking" && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                {rankingData ? (
                  <RankingPodium
                    topBolsas={rankingData}
                    onBolsaClick={handleBolsaClick}
                  />
                ) : (
                  <div className="text-center py-16">Carregando ranking...</div>
                )}
              </motion.div>
            )}

            {/* Seção de Editais */}
            {currentSection === "editais" && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {editaisData ? (
                  <EditaisTimeline editais={editaisData} />
                ) : (
                  <div className="text-center py-16">Carregando editais...</div>
                )}
              </motion.div>
            )}
          </div>
        </main>
      </ScrollingBackgroundProvider>
    </>
  );
};

export default Index;
