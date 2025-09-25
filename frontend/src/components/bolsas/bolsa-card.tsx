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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface BolsaCardProps {
  bolsa: Bolsa;
  onClick: (bolsa: Bolsa) => void;
  index: number;
}

export function BolsaCard({ bolsa, onClick, index }: BolsaCardProps) {
  const { isMobile, isTablet, isDesktop } = useDeviceType();
  const displayDateStr = bolsa.data_publicacao || bolsa.created_at;
  const displayDate = parseDateAsLocal(displayDateStr);
  const dataFim = parseDateAsLocal(bolsa.data_fim_inscricao);

  const isRecent = bolsa.data_publicacao
    ? Date.now() - (parseDateAsLocal(bolsa.data_publicacao)?.getTime() || 0) <
      7 * 24 * 60 * 60 * 1000
    : false;

  const card = (
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

          {/* Type badge and Vagas count */}
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className="w-fit text-xs">
              {bolsa.tipo}
            </Badge>
            {/* 🆕 MOSTRA QUANTIDADE DE VAGAS NO MOBILE */}
            {bolsa.vagas_total && bolsa.vagas_total > 1 && (
              <Badge
                variant="outline"
                className={`text-xs font-semibold ${
                  bolsa.status === "disponivel"
                    ? "border-green-500 text-green-700"
                    : "border-blue-500 text-blue-700"
                }`}
              >
                {bolsa.status === "disponivel"
                  ? `${bolsa.vagas_disponiveis || bolsa.vagas_total} vagas`
                  : `${bolsa.vagas_total} vagas`}
              </Badge>
            )}
          </div>

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
                  <span>{format(displayDate, "dd/MM", { locale: ptBR })}</span>
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
              <div className="flex items-center gap-2">
                <StatusBadge status={bolsa.status} />
                {/* 🆕 MOSTRA QUANTIDADE DE VAGAS NO CARD */}
                {bolsa.vagas_total && bolsa.vagas_total > 1 && (
                  <Badge
                    variant="outline"
                    className={`text-xs font-semibold ${
                      bolsa.status === "disponivel"
                        ? "border-green-500 text-green-700"
                        : "border-blue-500 text-blue-700"
                    }`}
                  >
                    {bolsa.status === "disponivel"
                      ? `${bolsa.vagas_disponiveis || bolsa.vagas_total} vagas`
                      : `${bolsa.vagas_total} vagas (${
                          bolsa.vagas_preenchidas || 0
                        } preenchidas)`}
                  </Badge>
                )}
              </div>
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
            {bolsa.status === "disponivel" && dataFim && isFuture(dataFim) && (
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
  );

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
      {/* Desktop: Card with tooltip preview */}
      {isDesktop ? (
        <TooltipProvider>
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>{card}</TooltipTrigger>
            <TooltipContent side="right" className="max-w-sm p-4 glass">
              <div className="space-y-3">
                <div>
                  <h4 className="font-semibold text-sm mb-1">
                    {formatProjectTitle(bolsa.nome_projeto)}
                  </h4>
                  <p className="text-xs text-muted-foreground">
                    {formatPersonName(bolsa.orientador)}
                  </p>
                </div>

                {bolsa.resumo && (
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {bolsa.resumo.length > 120
                      ? `${bolsa.resumo.substring(0, 120)}...`
                      : bolsa.resumo}
                  </p>
                )}

                <div className="flex items-center gap-4 text-xs">
                  {bolsa.remuneracao && (
                    <span className="flex items-center gap-1 text-green-600">
                      💰 R$ {bolsa.remuneracao.toLocaleString("pt-BR")}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Eye className="w-3 h-3" />
                    {bolsa.view_count} views
                  </span>
                </div>

                <div className="pt-1 border-t border-border/50">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-xs">
                      {bolsa.centro?.toUpperCase()}
                    </Badge>
                    <StatusBadge status={bolsa.status} />
                  </div>
                </div>
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      ) : (
        /* Mobile/Tablet: Card without tooltip */
        card
      )}
    </motion.div>
  );
}
