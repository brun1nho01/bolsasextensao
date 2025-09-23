import { motion } from "framer-motion";
import { Bolsa } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Eye, Calendar, User, ChevronRight, Tag, Clock } from "lucide-react";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  formatPersonName,
  formatProjectTitle,
  parseDateAsLocal,
} from "@/lib/utils";
import { format, isFuture } from "date-fns";
import { ptBR } from "date-fns/locale";

interface BolsaListProps {
  bolsas: Bolsa[];
  loading: boolean;
  onBolsaClick: (bolsa: Bolsa) => void;
}

const BolsaListItem = ({
  bolsa,
  onBolsaClick,
}: {
  bolsa: Bolsa;
  onBolsaClick: (bolsa: Bolsa) => void;
}) => {
  const formatDate = (dateString?: string) => {
    if (!dateString) return "N/A";
    const date = parseDateAsLocal(dateString);
    if (!date) return "N/A";
    return format(date, "dd/MM/yyyy", { locale: ptBR });
  };

  const displayDateStr = bolsa.data_publicacao || bolsa.created_at;
  const dataFim = parseDateAsLocal(bolsa.data_fim_inscricao);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      onClick={() => onBolsaClick(bolsa)}
      className="flex items-center justify-between p-4 mb-3 transition-all duration-300 ease-in-out bg-card/50 backdrop-blur-sm border border-transparent rounded-lg cursor-pointer hover:bg-card hover:border-primary/20"
    >
      <div className="flex flex-col flex-1 min-w-0 pr-4">
        <h3 className="mb-1 text-lg font-semibold truncate text-foreground">
          {formatProjectTitle(bolsa.nome_projeto)}
        </h3>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <User className="w-3 h-3" />
            <span className="truncate">
              {formatPersonName(bolsa.orientador)}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3 h-3" />
            <span>{formatDate(displayDateStr)}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Eye className="w-3 h-3" />
            <span>{bolsa.view_count}</span>
          </div>
          {bolsa.tipo && (
            <div className="flex items-center gap-1.5">
              <Tag className="w-3 h-3" />
              <span className="truncate">{bolsa.tipo}</span>
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-4">
        {bolsa.status === "disponivel" && dataFim && isFuture(dataFim) && (
          <div className="flex items-center gap-1.5 text-xs font-medium">
            <Clock className="w-3 h-3 text-danger" />
            <span className="text-danger">
              Encerra em {format(dataFim, "dd/MM/yy", { locale: ptBR })}
            </span>
          </div>
        )}
        <StatusBadge status={bolsa.status} />
        <ChevronRight className="w-5 h-5 text-muted-foreground" />
      </div>
    </motion.div>
  );
};

export function BolsaList({ bolsas, loading, onBolsaClick }: BolsaListProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="w-full h-20 rounded-lg bg-card/50 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (bolsas.length === 0) {
    return (
      <div className="py-20 text-center text-muted-foreground">
        <p>Nenhuma bolsa encontrada.</p>
        <p>Tente ajustar os filtros ou limpar a busca.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {bolsas.map((bolsa) => (
        <BolsaListItem
          key={bolsa.id}
          bolsa={bolsa}
          onBolsaClick={onBolsaClick}
        />
      ))}
    </div>
  );
}
