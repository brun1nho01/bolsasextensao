import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Eye,
  User,
  Calendar,
  FileText,
  Award,
  ExternalLink,
  DollarSign,
  Clock,
} from "lucide-react";
import { format, formatDistanceToNow, isFuture } from "date-fns";
import { ptBR } from "date-fns/locale";
import { Bolsa } from "@/types/api";
import {
  formatPersonName,
  formatProjectTitle,
  parseDateAsLocal,
} from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useState } from "react";

interface BolsaDetailsModalProps {
  bolsa: Bolsa | null;
  isOpen: boolean;
  onClose: () => void;
}

export function BolsaDetailsModal({
  bolsa,
  isOpen,
  onClose,
}: BolsaDetailsModalProps) {
  if (!bolsa) return null;

  const [isResumoExpanded, setIsResumoExpanded] = useState(false);

  // A data a ser exibida agora é a 'data_publicacao', com 'created_at' como fallback
  const displayDateStr = bolsa.data_publicacao || bolsa.created_at;
  const displayDate = parseDateAsLocal(displayDateStr);

  // A lógica de "Novo" agora usa 'data_publicacao' para ser mais precisa.
  // Só considera "recente" se a data de publicação existir e for dos últimos 7 dias.
  const isRecent = bolsa.data_publicacao
    ? Date.now() - (parseDateAsLocal(bolsa.data_publicacao)?.getTime() || 0) <
      7 * 24 * 60 * 60 * 1000
    : false;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="glass max-w-2xl max-h-[90vh] overflow-y-auto border-glass-border">
        <DialogHeader className="relative">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            {/* Header with badges */}
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <DialogTitle className="text-2xl font-bold text-foreground leading-tight">
                  {formatProjectTitle(bolsa.nome_projeto)}
                </DialogTitle>
                <p className="text-muted-foreground mt-1">{bolsa.tipo}</p>
              </div>
              <div className="flex items-center gap-2">
                {isRecent && (
                  <Badge className="badge-success animate-pulse">Novo</Badge>
                )}
                {bolsa.view_count > 50 && (
                  <Badge className="badge-warning">Popular</Badge>
                )}
              </div>
            </div>

            {/* Status and Info */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 flex-wrap">
                <StatusBadge status={bolsa.status} />
                {/* Badge de quantidade de vagas - primeiro */}
                <Badge
                  variant="outline"
                  className={`text-sm font-medium px-3 py-1 rounded-full animate-pulse backdrop-blur-sm ${
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
                    className="text-sm font-medium px-3 py-1 rounded-full animate-pulse bg-secondary/10 text-secondary border-secondary/20 backdrop-blur-sm"
                  >
                    Perfil {bolsa.numero_perfil}
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Eye className="w-5 h-5" />
                <span className="text-lg font-medium">{bolsa.view_count}</span>
                <span className="text-sm">visualizações</span>
              </div>
            </div>
          </motion.div>
        </DialogHeader>

        <Separator className="my-6 bg-glass-border" />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="space-y-8"
        >
          {/* Main Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Orientador */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <User className="w-5 h-5 text-primary" />
                Orientador
              </h3>
              <div className="glass-card p-4">
                <p className="text-foreground font-medium text-lg">
                  {formatPersonName(bolsa.orientador)}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Professor Orientador
                </p>
              </div>
            </div>

            {/* Data de Publicação */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Calendar className="w-5 h-5 text-primary" />
                Datas Importantes
              </h3>
              <div className="glass-card p-4 space-y-3">
                {displayDate && (
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Publicado em
                    </p>
                    <p className="text-foreground font-medium">
                      {format(displayDate, "dd 'de' MMMM 'de' yyyy", {
                        locale: ptBR,
                      })}
                    </p>
                  </div>
                )}
                {bolsa.data_fim_inscricao && (
                  <div>
                    <p
                      className={`text-sm ${
                        bolsa.status === "disponivel"
                          ? "text-danger font-bold"
                          : "text-muted-foreground"
                      }`}
                    >
                      Inscrições até
                    </p>
                    <p
                      className={`font-medium ${
                        bolsa.status === "disponivel"
                          ? "text-danger font-bold"
                          : "text-foreground"
                      }`}
                    >
                      {format(
                        parseDateAsLocal(bolsa.data_fim_inscricao)!,
                        "dd 'de' MMMM 'de' yyyy",
                        {
                          locale: ptBR,
                        }
                      )}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Resumo do Projeto */}
          {bolsa.resumo && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="space-y-3"
            >
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                Resumo do Projeto
              </h3>
              <div className="glass-card p-6 border border-primary/20 bg-primary/5">
                <div className="relative">
                  <div className="absolute top-0 left-0 w-1 h-full bg-primary rounded-full" />
                  <div className="pl-6">
                    <p
                      className={`text-foreground leading-relaxed text-justify text-base transition-all duration-300 ${
                        !isResumoExpanded ? "line-clamp-4" : ""
                      }`}
                    >
                      {bolsa.resumo}
                    </p>
                    {/* Botão de Ler Mais/Menos */}
                    <button
                      onClick={() => setIsResumoExpanded(!isResumoExpanded)}
                      className="text-primary font-semibold mt-3 text-sm hover:underline focus:outline-none"
                    >
                      {isResumoExpanded ? "Ler menos" : "Ler mais"}
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Candidato Aprovado */}
          {bolsa.candidato_aprovado && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="space-y-3"
            >
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Award className="w-5 h-5 text-success" />
                Candidato Aprovado
              </h3>
              <div className="glass-card p-6 border border-success/20 bg-success/5">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-success/20 flex items-center justify-center">
                    <Award className="w-6 h-6 text-success" />
                  </div>
                  <div>
                    <p className="text-foreground font-semibold text-lg">
                      {formatPersonName(bolsa.candidato_aprovado)}
                    </p>
                    <p className="text-success text-sm font-medium">
                      ✓ Selecionado para a bolsa
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Detalhes Técnicos */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="space-y-3"
          >
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              Informações da Bolsa
            </h3>
            <div className="glass-card p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">ID da Bolsa:</span>
                  <p className="font-mono text-xs bg-muted/20 rounded px-2 py-1 mt-1">
                    {bolsa.id}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Tipo:</span>
                  <p className="font-medium">{bolsa.tipo}</p>
                </div>
                {bolsa.numero_perfil && (
                  <div>
                    <span className="text-muted-foreground">Perfil:</span>
                    <p className="font-medium">
                      <Badge variant="secondary" className="text-sm">
                        Perfil {bolsa.numero_perfil}
                      </Badge>
                    </p>
                  </div>
                )}
                {bolsa.remuneracao && bolsa.remuneracao > 0 && (
                  <div>
                    <span className="text-muted-foreground">Remuneração:</span>
                    <p className="font-medium text-success flex items-center gap-1 mt-1">
                      {new Intl.NumberFormat("pt-BR", {
                        style: "currency",
                        currency: "BRL",
                      }).format(bolsa.remuneracao)}
                    </p>
                  </div>
                )}
                <div>
                  <span className="text-muted-foreground">Status Atual:</span>
                  <div className="mt-1">
                    <StatusBadge status={bolsa.status} />
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Interesse:</span>
                  <p className="font-medium flex items-center gap-1 mt-1">
                    <Eye className="w-4 h-4" />
                    {bolsa.view_count} visualizações
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex flex-col sm:flex-row gap-3 pt-6 border-t border-glass-border"
          >
            <Button
              className="flex-1 gradient-primary shadow-glow hover:shadow-glow"
              size="lg"
              onClick={() => {
                if (bolsa.url_edital) {
                  window.open(bolsa.url_edital, "_blank");
                }
              }}
              disabled={!bolsa.url_edital}
            >
              <ExternalLink className="w-5 h-5 mr-2" />
              Ver Edital Completo
            </Button>
            <Button
              variant="outline"
              className="glass hover:bg-primary/20"
              size="lg"
              onClick={onClose}
            >
              Fechar
            </Button>
          </motion.div>
        </motion.div>
      </DialogContent>
    </Dialog>
  );
}
