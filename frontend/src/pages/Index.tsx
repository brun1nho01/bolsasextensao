import { useCallback, useEffect, useMemo, useState } from "react";
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
import {
  useBolsas,
  useRanking,
  useEditais,
  useBolsa,
  useIncrementBolsaView,
} from "@/hooks/useApi";
import { useDeviceType } from "@/hooks/use-mobile";
import { useViewSession } from "@/hooks/useViewSession";
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

const Index = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const { isMobile, isTablet, isDesktop } = useDeviceType();
  const { sessionId, hasViewedBolsa, markBolsaAsViewed } = useViewSession();
  const incrementViewMutation = useIncrementBolsaView();

  // Estados que não dependem da URL
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selectedBolsaId, setSelectedBolsaId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  // A URL é a única fonte da verdade para os filtros e seção
  const currentSection = (searchParams.get("section") as Section) || "bolsas";

  const filters = useMemo(() => {
    const page = parseInt(searchParams.get("page") || "1", 10);
    const q = searchParams.get("q") || "";
    const status = searchParams.get("status") || "all";
    const tipo = searchParams.get("tipo") || "all";
    const centro = searchParams.get("centro") || "all";
    const orientador = searchParams.get("orientador") || "all";
    const sort = searchParams.get("sort") || "nome_projeto";
    const order = (searchParams.get("order") as "asc" | "desc") || "asc";

    return { page, q, status, tipo, centro, orientador, sort, order };
  }, [searchParams]);

  // Funções para manipular a URL, estabilizadas com useCallback
  const handleUpdateParams = useCallback(
    (newParams: Record<string, string | number>, resetPage = false) => {
      setSearchParams(
        (prev) => {
          const newSearchParams = new URLSearchParams(prev);
          Object.entries(newParams).forEach(([key, value]) => {
            if (value) {
              newSearchParams.set(key, String(value));
            } else {
              newSearchParams.delete(key);
            }
          });

          if (resetPage) {
            newSearchParams.delete("page");
          }
          return newSearchParams;
        },
        { replace: true }
      );
    },
    [setSearchParams]
  );

  const handlePageChange = useCallback(
    (page: number) => {
      handleUpdateParams({ page });
    },
    [handleUpdateParams]
  );

  const handleClearFilters = useCallback(() => {
    setSearchParams(
      (prev) => {
        const newSearchParams = new URLSearchParams(prev);
        // Mantém section, sort, order e page
        const preserved = {
          section: newSearchParams.get("section"),
          sort: newSearchParams.get("sort"),
          order: newSearchParams.get("order"),
          page: newSearchParams.get("page"), // Mantém a página atual
        };
        const clearedParams = new URLSearchParams();
        if (preserved.section) clearedParams.set("section", preserved.section);
        if (preserved.sort) clearedParams.set("sort", preserved.sort);
        if (preserved.order) clearedParams.set("order", preserved.order);
        if (preserved.page) clearedParams.set("page", preserved.page);

        return clearedParams;
      },
      { replace: true }
    );
  }, [setSearchParams]);

  const handleSetCurrentSection = useCallback(
    (section: Section) => {
      const newSearchParams = new URLSearchParams();
      newSearchParams.set("section", section);
      setSearchParams(newSearchParams, { replace: true });
    },
    [setSearchParams]
  );

  // Preparar filtros para a API usando useMemo para otimização
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
  const {
    data: bolsasData,
    isLoading,
    error,
  } = useBolsas(apiFilters, currentSection === "bolsas");
  const { data: rankingData } = useRanking(currentSection === "ranking");
  const { data: editaisData } = useEditais(currentSection === "editais");
  const { data: preenchidasData } = useBolsas(
    { status: "preenchida", page_size: 1 },
    true
  );
  const { data: totalBolsasData } = useBolsas({ page_size: 1 }, true);
  const { data: selectedBolsaData } = useBolsa(selectedBolsaId);

  // Efeito para incrementar a visualização quando o modal abre
  useEffect(() => {
    if (selectedBolsaId && !hasViewedBolsa(selectedBolsaId)) {
      incrementViewMutation.mutate({ bolsaId: selectedBolsaId, sessionId });
      markBolsaAsViewed(selectedBolsaId);
    }
  }, [
    selectedBolsaId,
    hasViewedBolsa,
    markBolsaAsViewed,
    incrementViewMutation,
    sessionId,
  ]);

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
    // Não invalida queries aqui para evitar re-fetches desnecessários durante navegação
    // As queries serão invalidadas automaticamente pelo incremento de view count
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
            onSearch={(query) => handleUpdateParams({ q: query }, true)}
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
                        handleUpdateParams(payload, true)
                      }
                      onClearFilters={handleClearFilters}
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
                                  handleUpdateParams(payload, true)
                                }
                                onClearFilters={handleClearFilters}
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
                      onPageChange={handlePageChange}
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
                          onClick={handleClearFilters}
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
                    onPageChange={handlePageChange}
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
