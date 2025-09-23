import { motion } from "framer-motion";
import {
  Calendar,
  Clock,
  CheckCircle,
  AlertCircle,
  FileText,
  ExternalLink,
} from "lucide-react";
import { format, formatDistanceToNow, isPast, isFuture } from "date-fns";
import { ptBR } from "date-fns/locale";
import { Edital } from "@/types/api";
import {
  GlassCard,
  GlassCardContent,
  GlassCardHeader,
} from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { parseDateAsLocal } from "@/lib/utils";

interface EditaisTimelineProps {
  editais: Edital[];
}

// A lógica de status agora é derivada dos dados reais do edital
const getStatusConfig = (edital: Edital) => {
  if (
    edital.data_fim_inscricao &&
    isPast(parseDateAsLocal(edital.data_fim_inscricao)!)
  ) {
    return {
      icon: CheckCircle,
      color: "text-muted-foreground",
      bgColor: "bg-muted/20",
      label: "Inscrições Encerradas",
      badge: "badge-danger",
    };
  }
  // Se não tem data de fim, ou a data é no futuro, consideramos ativo
  return {
    icon: Clock,
    color: "text-success",
    bgColor: "bg-success/20",
    label: "Inscrições Abertas",
    badge: "badge-success",
  };
};

export function EditaisTimeline({ editais }: EditaisTimelineProps) {
  return (
    <div className="space-y-8">
      {/* Title */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h2 className="text-3xl font-bold mb-2 flex items-center justify-center gap-3">
          <Calendar className="w-8 h-8 text-primary" />
          Timeline de Editais
        </h2>
        <p className="text-muted-foreground">
          Acompanhe os editais de bolsas e suas datas importantes
        </p>
      </motion.div>

      {/* Timeline */}
      <div className="relative">
        {/* Timeline Line */}
        <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary via-info to-success transform md:-translate-x-1/2" />

        <div className="space-y-8">
          {editais.map((edital, index) => {
            const config = getStatusConfig(edital);
            const Icon = config.icon;
            const isLeft = index % 2 === 0;
            const dataFim = parseDateAsLocal(edital.data_fim_inscricao);
            // Removemos o '!' e vamos tratar o caso de 'dataPublicacao' ser nula
            const dataPublicacao = parseDateAsLocal(edital.data_publicacao);

            // Um edital é considerado "urgente" se o prazo final for em menos de 7 dias
            const isUrgent =
              dataFim &&
              isFuture(dataFim) &&
              dataFim.getTime() - Date.now() < 7 * 24 * 60 * 60 * 1000;

            return (
              <motion.div
                key={edital.id}
                initial={{ opacity: 0, x: isLeft ? -50 : 50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.2 }}
                className={`relative flex items-center ${
                  isLeft ? "md:justify-start" : "md:justify-end"
                }`}
              >
                {/* Timeline Dot */}
                <div
                  className={`absolute left-8 md:left-1/2 w-4 h-4 rounded-full border-2 border-background transform md:-translate-x-1/2 z-10 ${config.bgColor}`}
                >
                  <div
                    className={`w-2 h-2 rounded-full ${config.color.replace(
                      "text-",
                      "bg-"
                    )} absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2`}
                  />
                </div>

                {/* Content Card */}
                <motion.div
                  whileHover={{ scale: 1.02, y: -2 }}
                  className={`ml-16 md:ml-0 md:w-5/12 ${
                    isLeft ? "md:pr-8" : "md:pl-8"
                  }`}
                >
                  <a
                    href={edital.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="outline-none focus:ring-2 focus:ring-primary rounded-lg"
                  >
                    <GlassCard
                      hoverable={true}
                      className={`relative ${
                        isUrgent ? "ring-2 ring-warning/50 animate-glow" : ""
                      }`}
                    >
                      {/* Urgent Badge */}
                      {isUrgent && (
                        <div className="absolute -top-2 -right-2 z-10">
                          <Badge className="badge-warning animate-pulse">
                            Urgente!
                          </Badge>
                        </div>
                      )}

                      <GlassCardHeader title={edital.titulo} className="pb-2" />

                      <GlassCardContent className="space-y-4">
                        {/* Status Badge */}
                        <div className="flex items-center gap-2">
                          <Badge className={config.badge}>
                            <Icon className="w-3 h-3 mr-1" />
                            {config.label}
                          </Badge>
                        </div>
                        {/* Dates */}
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-sm">
                            <FileText className="w-4 h-4 text-muted-foreground" />
                            <span className="text-muted-foreground">
                              Publicado:
                            </span>
                            <span className="font-medium">
                              {dataPublicacao
                                ? format(dataPublicacao, "dd/MM/yyyy", {
                                    locale: ptBR,
                                  })
                                : "Não informada"}
                            </span>
                          </div>

                          {dataFim && (
                            <div className="flex items-center gap-2 text-sm">
                              <Clock className="w-4 h-4 text-muted-foreground" />
                              <span className="text-muted-foreground">
                                Prazo:
                              </span>
                              <span
                                className={`font-medium ${
                                  isUrgent ? "text-warning" : ""
                                }`}
                              >
                                {format(dataFim, "dd/MM/yyyy", {
                                  locale: ptBR,
                                })}
                              </span>
                            </div>
                          )}

                          {dataFim && isFuture(dataFim) && (
                            <div className="text-xs text-muted-foreground">
                              Faltam{" "}
                              {formatDistanceToNow(dataFim, {
                                locale: ptBR,
                                addSuffix: false,
                              })}
                            </div>
                          )}
                        </div>

                        {/* Action Button */}
                        <div className="pt-2 border-t border-glass-border">
                          <Button
                            variant="link"
                            className="text-primary hover:text-primary-glow transition-colors p-0 h-auto"
                            asChild
                          >
                            <span className="flex items-center">
                              Ver edital completo
                              <ExternalLink className="w-3 h-3 ml-1" />
                            </span>
                          </Button>
                        </div>
                      </GlassCardContent>
                    </GlassCard>
                  </a>
                </motion.div>

                {/* Timeline Connector Line */}
                {index < editais.length - 1 && (
                  <div className="absolute left-8 md:left-1/2 top-16 w-0.5 h-8 bg-gradient-to-b from-transparent to-muted transform md:-translate-x-1/2" />
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
