import { motion } from "framer-motion";
import {
  Eye,
  User,
  Calendar,
  ExternalLink,
  TrendingUp,
  Clock,
} from "lucide-react";
import { format, formatDistanceToNow, isFuture } from "date-fns";
import { ptBR } from "date-fns/locale";
import { Bolsa } from "@/types/api";
import { useDeviceType } from "@/hooks/use-mobile";
import {
  formatPersonName,
  formatProjectTitle,
  parseDateAsLocal,
} from "@/lib/utils";
import {
  GlassCard,
  GlassCardContent,
  GlassCardHeader,
} from "@/components/ui/glass-card";
import { StatusBadge } from "@/components/ui/status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface BolsaCardProps {
  bolsa: Bolsa;
  onClick: (bolsa: Bolsa) => void;
  index: number;
}

export function BolsaCard({ bolsa, onClick, index }: BolsaCardProps) {
  const { isMobile, isTablet } = useDeviceType();
  const displayDateStr = bolsa.data_publicacao || bolsa.created_at;
  const displayDate = parseDateAsLocal(displayDateStr);
  const dataFim = parseDateAsLocal(bolsa.data_fim_inscricao);

  const isRecent = bolsa.data_publicacao
    ? Date.now() - (parseDateAsLocal(bolsa.data_publicacao)?.getTime() || 0) <
      7 * 24 * 60 * 60 * 1000
    : false;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: index * 0.1,
        duration: 0.5,
        type: "spring",
        damping: 25,
      }}
      whileHover={{ scale: 1.02, y: -4 }}
      className="group"
    >
      <GlassCard
        hoverable={true}
        className="h-full relative overflow-hidden cursor-pointer"
        onClick={() => onClick(bolsa)}
      >
        {/* Mobile/Tablet Layout */}
        {isMobile || isTablet ? (
          <div className="space-y-3 relative">
            {/* Top badges */}
            <div className="flex items-start justify-between">
              <div className="flex gap-1">
                {isRecent && (
                  <Badge className="badge-success px-2 py-1 text-xs animate-glow">
                    Novo
                  </Badge>
                )}
                {bolsa.view_count > 50 && (
                  <Badge className="badge-warning px-2 py-1 text-xs animate-pulse">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    Popular
                  </Badge>
                )}
              </div>
              <StatusBadge status={bolsa.status} />
            </div>

            {/* Title */}
            <h3 className="text-lg font-semibold text-foreground leading-tight">
              {formatProjectTitle(bolsa.nome_projeto)}
            </h3>

            {/* Type badge */}
            <Badge variant="outline" className="w-fit text-xs">
              {bolsa.tipo}
            </Badge>

            {/* Orientador */}
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-foreground">
                  {formatPersonName(bolsa.orientador)}
                </p>
                <p className="text-xs text-muted-foreground">Orientador</p>
              </div>
            </div>

            {/* Stats row */}
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <Eye className="w-3 h-3" />
                  <span>{bolsa.view_count}</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Calendar className="w-3 h-3" />
                  {displayDate ? (
                    <span>
                      {format(displayDate, "dd/MM", { locale: ptBR })}
                    </span>
                  ) : (
                    <span>N/A</span>
                  )}
                </div>
              </div>
            </div>

            {/* Deadline warning */}
            {bolsa.status === "disponivel" && dataFim && isFuture(dataFim) && (
              <div className="p-2 rounded-md bg-danger/10 border border-danger/20">
                <div className="flex items-center gap-2">
                  <Clock className="w-3 h-3 text-danger" />
                  <div>
                    <p className="text-xs font-medium text-danger">
                      Encerra em {format(dataFim, "dd/MM", { locale: ptBR })}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Candidato Aprovado */}
            {bolsa.candidato_aprovado && (
              <div className="p-2 rounded-md bg-success/10 border border-success/20">
                <p className="text-xs text-success font-medium">
                  ✓ {formatPersonName(bolsa.candidato_aprovado)}
                </p>
              </div>
            )}

            {/* Action button */}
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-center gap-2 hover:bg-primary/20 mt-2"
            >
              <ExternalLink className="w-4 h-4" />
              Ver Detalhes
            </Button>
          </div>
        ) : (
          /* Desktop Layout - Original */
          <>
            {/* Trending Indicator */}
            {bolsa.view_count > 50 && (
              <div className="absolute top-4 right-4 z-10">
                <Badge className="badge-warning px-2 py-1 text-xs animate-pulse">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  Popular
                </Badge>
              </div>
            )}

            {/* New Badge */}
            {isRecent && (
              <div className="absolute top-4 left-4 z-10">
                <Badge className="badge-success px-2 py-1 text-xs animate-glow">
                  Novo
                </Badge>
              </div>
            )}

            <GlassCardHeader
              title={formatProjectTitle(bolsa.nome_projeto)}
              description={bolsa.tipo}
              className="pb-4"
            />

            <GlassCardContent className="space-y-4">
              {/* Status */}
              <div className="flex items-center justify-between">
                <StatusBadge status={bolsa.status} />
                <div className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Eye className="w-4 h-4" />
                  <motion.span
                    key={bolsa.view_count}
                    initial={{ scale: 1.2, color: "hsl(var(--primary))" }}
                    animate={{
                      scale: 1,
                      color: "hsl(var(--muted-foreground))",
                    }}
                    transition={{ duration: 0.3 }}
                  >
                    {bolsa.view_count}
                  </motion.span>
                </div>
              </div>

              {/* Orientador */}
              <div className="flex items-start gap-2">
                <User className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                    {formatPersonName(bolsa.orientador)}
                  </p>
                  <p className="text-xs text-muted-foreground">Orientador</p>
                </div>
              </div>

              {/* Data Fim Inscrição (Apenas se disponível) */}
              {bolsa.status === "disponivel" &&
                dataFim &&
                isFuture(dataFim) && (
                  <div className="p-3 rounded-lg bg-danger/10 border border-danger/20 mt-2">
                    <p className="text-xs text-danger font-bold mb-1 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Inscrições Encerram
                    </p>
                    <p className="text-sm text-foreground font-semibold">
                      {format(dataFim, "dd 'de' MMMM'", { locale: ptBR })}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(dataFim, {
                        addSuffix: true,
                        locale: ptBR,
                      })}
                    </p>
                  </div>
                )}

              {/* Candidato Aprovado */}
              {bolsa.candidato_aprovado && (
                <div className="p-3 rounded-lg bg-success/10 border border-success/20">
                  <p className="text-xs text-success font-medium mb-1">
                    Candidato Aprovado
                  </p>
                  <p className="text-sm text-foreground">
                    {formatPersonName(bolsa.candidato_aprovado)}
                  </p>
                </div>
              )}

              {/* Data */}
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Calendar className="w-3 h-3" />
                {displayDate ? (
                  <>
                    <span>
                      {formatDistanceToNow(displayDate, {
                        addSuffix: true,
                        locale: ptBR,
                      })}
                    </span>
                    <span className="text-muted-foreground/50">•</span>
                    <span>
                      {format(displayDate, "dd/MM/yyyy", { locale: ptBR })}
                    </span>
                  </>
                ) : (
                  <span>Data indisponível</span>
                )}
              </div>

              {/* Hover Action */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                whileHover={{ opacity: 1, y: 0 }}
                className="pt-3 border-t border-glass-border opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-center gap-2 hover:bg-primary/20"
                >
                  <ExternalLink className="w-4 h-4" />
                  Ver Detalhes
                </Button>
              </motion.div>
            </GlassCardContent>

            {/* Gradient Overlay on Hover */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
              initial={false}
            />
          </>
        )}
      </GlassCard>
    </motion.div>
  );
}
