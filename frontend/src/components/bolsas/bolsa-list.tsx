import { motion } from "framer-motion";
import { Bolsa } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Eye, Calendar, User, ChevronRight, Tag, Clock } from "lucide-react";
import { StatusBadge } from "@/components/ui/status-badge";
import { useDeviceType } from "@/hooks/use-mobile";
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
  const { isMobile, isTablet } = useDeviceType();

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
      className="glass-card hover:border-primary/30 cursor-pointer transition-all duration-300"
    >
      {/* Mobile/Tablet Layout */}
      {isMobile || isTablet ? (
        <div className="space-y-3">
          {/* Header with title and status */}
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-lg font-semibold text-foreground flex-1 leading-tight">
              {formatProjectTitle(bolsa.nome_projeto)}
            </h3>
            <StatusBadge status={bolsa.status} />
          </div>

          {/* Orientador */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <User className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">
              {formatPersonName(bolsa.orientador)}
            </span>
          </div>

          {/* Info row */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <Eye className="w-3 h-3" />
                <span>{bolsa.view_count}</span>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                <span>{formatDate(displayDateStr)}</span>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          </div>

          {/* Info badges */}
          <div className="flex items-center gap-2 flex-wrap">
            {bolsa.tipo && (
              <Badge variant="outline" className="w-fit text-xs">
                {bolsa.tipo}
              </Badge>
            )}
            {/* Badge de quantidade de vagas - primeiro */}
            <Badge
              variant="outline"
              className={`text-xs font-medium px-3 py-1 rounded-full animate-pulse backdrop-blur-sm ${
                bolsa.status === "disponivel"
                  ? "bg-success/10 text-success border-success/20"
                  : bolsa.status === "aberta"
                  ? "bg-info/10 text-info border-info/20"
                  : "bg-danger/10 text-danger border-danger/20"
              }`}
            >
              {bolsa.vagas_total || 1}{" "}
              {(bolsa.vagas_total || 1) === 1 ? "vaga" : "vagas"}
            </Badge>
            {/* Badge de perfil - segundo */}
            {bolsa.numero_perfil && (
              <Badge
                variant="outline"
                className="text-xs font-medium px-3 py-1 rounded-full animate-pulse bg-secondary/10 text-secondary border-secondary/20 backdrop-blur-sm"
              >
                Perfil {bolsa.numero_perfil}
              </Badge>
            )}
          </div>

          {/* Deadline warning */}
          {bolsa.status === "disponivel" && dataFim && isFuture(dataFim) && (
            <div className="flex items-center gap-2 p-2 rounded-md bg-danger/10 border border-danger/20">
              <Clock className="w-3 h-3 text-danger" />
              <span className="text-xs font-medium text-danger">
                Encerra em {format(dataFim, "dd/MM/yy", { locale: ptBR })}
              </span>
            </div>
          )}
        </div>
      ) : (
        /* Desktop Layout - Original */
        <div className="flex items-center justify-between">
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
        </div>
      )}
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
