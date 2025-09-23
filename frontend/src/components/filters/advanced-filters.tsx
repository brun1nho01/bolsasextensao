import { motion } from "framer-motion";
import { Filter, X, Users, BookOpen, Calendar, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";

interface FilterState {
  status: string;
  tipo: string;
  orientador: string;
  centro: string;
  sort: string;
  order: "asc" | "desc";
}

interface AdvancedFiltersProps {
  filters: FilterState;
  onFiltersChange: (filters: Partial<FilterState>) => void;
  onClearFilters: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

export function AdvancedFilters({
  filters,
  onFiltersChange,
  onClearFilters,
  isOpen,
  onToggle,
}: AdvancedFiltersProps) {
  const activeFiltersCount = Object.values(filters).filter(
    (value) => value && value !== "all"
  ).length;

  return (
    <div className="sticky top-4 z-40">
      {/* Filter Toggle Button */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="mb-4"
      >
        <Button
          onClick={onToggle}
          variant="outline"
          className="glass w-full justify-between hover:scale-105 transition-transform"
        >
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4" />
            <span>Filtros Avançados</span>
            {activeFiltersCount > 0 && (
              <Badge className="badge-info px-2 py-0.5 text-xs">
                {activeFiltersCount}
              </Badge>
            )}
          </div>
          <motion.div
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <Filter className="w-4 h-4" />
          </motion.div>
        </Button>
      </motion.div>

      {/* Filters Panel */}
      <motion.div
        initial={false}
        animate={{
          height: isOpen ? "auto" : 0,
          opacity: isOpen ? 1 : 0,
        }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="overflow-visible relative z-40"
      >
        <GlassCard className="p-6 space-y-6 relative z-40">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Target className="w-5 h-5 text-primary" />
              Filtros Personalizados
            </h3>
            {activeFiltersCount > 0 && (
              <Button
                onClick={onClearFilters}
                variant="ghost"
                size="sm"
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="w-4 h-4 mr-1" />
                Limpar Tudo
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Status Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-success" />
                Status da Bolsa
              </label>
              <Select
                value={filters.status}
                onValueChange={(value) => onFiltersChange({ status: value })}
              >
                <SelectTrigger className="glass border-glass-border">
                  <SelectValue placeholder="Todos os status" />
                </SelectTrigger>
                <SelectContent className="glass border-glass-border bg-card z-50 shadow-glass">
                  <SelectItem value="all">Todos os status</SelectItem>
                  <SelectItem value="disponivel">Disponível</SelectItem>
                  <SelectItem value="aberta">Aberta</SelectItem>
                  <SelectItem value="preenchida">Preenchida</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Tipo Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-info" />
                Tipo de Bolsa
              </label>
              <Select
                value={filters.tipo}
                onValueChange={(value) => onFiltersChange({ tipo: value })}
              >
                <SelectTrigger className="glass border-glass-border">
                  <SelectValue placeholder="Todos os tipos" />
                </SelectTrigger>
                <SelectContent className="glass border-glass-border bg-card z-50 shadow-glass">
                  <SelectItem value="all">Todos os tipos</SelectItem>
                  <SelectItem value="extensao">Bolsa Extensão</SelectItem>
                  <SelectItem value="UA Superior">Bolsa UA Superior</SelectItem>
                  <SelectItem value="UA Médio">Bolsa UA Médio</SelectItem>
                  <SelectItem value="UA Fundamental">
                    Bolsa UA Fundamental
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Centro Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <Users className="w-4 h-4 text-warning" />
                Centro UENF
              </label>
              <Select
                value={filters.centro}
                onValueChange={(value) => onFiltersChange({ centro: value })}
              >
                <SelectTrigger className="glass border-glass-border">
                  <SelectValue placeholder="Todos os centros" />
                </SelectTrigger>
                <SelectContent className="glass border-glass-border bg-card z-50 shadow-glass">
                  <SelectItem value="all">Todos os centros</SelectItem>
                  <SelectItem value="ccta">CCTA</SelectItem>
                  <SelectItem value="cct">CCT</SelectItem>
                  <SelectItem value="cbb">CBB</SelectItem>
                  <SelectItem value="cch">CCH</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Sort Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <Calendar className="w-4 h-4 text-primary" />
                Ordenar Por
              </label>
              <div className="flex gap-2">
                <Select
                  value={filters.sort}
                  onValueChange={(value) => onFiltersChange({ sort: value })}
                >
                  <SelectTrigger className="glass border-glass-border flex-1 min-w-0">
                    <SelectValue placeholder="Ordenar por" />
                  </SelectTrigger>
                  <SelectContent className="glass border-glass-border bg-card z-50 shadow-glass">
                    <SelectItem value="nome_projeto">
                      Nome do Projeto
                    </SelectItem>
                    <SelectItem value="view_count">Visualizações</SelectItem>
                    <SelectItem value="orientador">Orientador</SelectItem>
                    <SelectItem value="created_at">Data de Criação</SelectItem>
                  </SelectContent>
                </Select>
                <Select
                  value={filters.order}
                  onValueChange={(value: "asc" | "desc") =>
                    onFiltersChange({ order: value })
                  }
                >
                  <SelectTrigger className="glass border-glass-border flex-1 min-w-0">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="glass border-glass-border bg-card z-50 shadow-glass">
                    {filters.sort === "nome_projeto" ||
                    filters.sort === "orientador" ? (
                      <>
                        <SelectItem value="asc">A → Z</SelectItem>
                        <SelectItem value="desc">Z → A</SelectItem>
                      </>
                    ) : (
                      <>
                        <SelectItem value="desc">Maior → Menor</SelectItem>
                        <SelectItem value="asc">Menor → Maior</SelectItem>
                      </>
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Quick Filters */}
          <div className="pt-4 border-t border-glass-border">
            <label className="text-sm font-medium mb-3 block">
              Filtros Rápidos
            </label>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onFiltersChange({ status: "disponivel" })}
                className={`glass hover:bg-success/20 ${
                  filters.status === "disponivel"
                    ? "bg-success/20 border-success"
                    : ""
                }`}
              >
                Disponíveis
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  onFiltersChange({ sort: "view_count", order: "desc" })
                }
                className={`glass hover:bg-primary/20 ${
                  filters.sort === "view_count" && filters.order === "desc"
                    ? "bg-primary/20 border-primary"
                    : ""
                }`}
              >
                Mais Vistas
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  onFiltersChange({ sort: "created_at", order: "desc" })
                }
                className={`glass hover:bg-info/20 ${
                  filters.sort === "created_at" && filters.order === "desc"
                    ? "bg-info/20 border-info"
                    : ""
                }`}
              >
                Mais Recentes
              </Button>
            </div>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  );
}
