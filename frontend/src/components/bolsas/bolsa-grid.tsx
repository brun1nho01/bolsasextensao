import { motion } from "framer-motion";
import { Grid, List, SortAsc, SortDesc, Eye } from "lucide-react";
import { useState } from "react";
import { Bolsa } from "@/types/api";
import { BolsaCard } from "./bolsa-card";
import { StatusBadge } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface BolsaGridProps {
  bolsas: Bolsa[];
  loading?: boolean;
  onBolsaClick: (bolsa: Bolsa) => void;
  total?: number;
}

export function BolsaGrid({
  bolsas,
  loading,
  onBolsaClick,
  total,
}: BolsaGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card h-80"
          >
            <div className="animate-pulse">
              <div className="h-4 bg-muted rounded w-3/4 mb-4"></div>
              <div className="h-3 bg-muted rounded w-1/2 mb-6"></div>
              <div className="space-y-2">
                <div className="h-3 bg-muted rounded"></div>
                <div className="h-3 bg-muted rounded w-5/6"></div>
                <div className="h-3 bg-muted rounded w-4/6"></div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    );
  }

  if (!bolsas.length) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center py-16"
      >
        <div className="glass-card max-w-md mx-auto p-8">
          <div className="w-16 h-16 bg-muted rounded-full mx-auto mb-4 flex items-center justify-center">
            <Grid className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">
            Nenhuma bolsa encontrada
          </h3>
          <p className="text-muted-foreground text-sm">
            Tente ajustar os filtros ou termos de busca para encontrar mais
            resultados.
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with View Toggle and Stats */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between flex-wrap gap-4"
      >
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold">Bolsas Ativas</h2>
          {total && (
            <Badge variant="outline" className="glass px-3 py-1">
              {total} {total === 1 ? "resultado" : "resultados"}
            </Badge>
          )}
        </div>
      </motion.div>

      {/* Grid View */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
      >
        {bolsas.map((bolsa, index) => (
          <BolsaCard
            key={bolsa.id}
            bolsa={bolsa}
            onClick={onBolsaClick}
            index={index}
          />
        ))}
      </motion.div>
    </div>
  );
}
