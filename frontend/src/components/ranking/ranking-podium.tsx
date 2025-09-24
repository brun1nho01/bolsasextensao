import { motion } from "framer-motion";
import { Trophy, Medal, Award, Eye, TrendingUp } from "lucide-react";
import { useEffect, useRef } from "react";
import { Bolsa } from "@/types/api";
import { formatPersonName, formatProjectTitle } from "@/lib/utils";
import { useIsMobile } from "@/hooks/use-mobile";
import {
  GlassCard,
  GlassCardContent,
  GlassCardHeader,
} from "@/components/ui/glass-card";
import { StatusBadge } from "@/components/ui/status-badge";
import { Badge } from "@/components/ui/badge";

interface RankingPodiumProps {
  topBolsas: Bolsa[];
  onBolsaClick: (bolsa: Bolsa) => void;
}

const podiumIcons = [Trophy, Medal, Award];
const podiumColors = [
  "text-warning",
  "text-muted-foreground",
  "text-amber-600",
];
// Define a altura dos CARDS para criar o efeito de pódio
const podiumCardHeights = ["h-[22rem]", "h-[20rem]", "h-[18rem]"]; // 1º, 2º, 3º

export function RankingPodium({ topBolsas, onBolsaClick }: RankingPodiumProps) {
  const top3 = topBolsas.slice(0, 3);
  const rest = topBolsas.slice(3);
  const isMobile = useIsMobile();
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Centralizar o scroll no mobile após o render
  useEffect(() => {
    if (isMobile && scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      const scrollLeft = (container.scrollWidth - container.clientWidth) / 2;
      container.scrollLeft = scrollLeft;
    }
  }, [isMobile, topBolsas]);

  return (
    <div className="space-y-8">
      {/* Title */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h2 className="text-3xl font-bold mb-2 flex items-center justify-center gap-3">
          <TrendingUp className="w-8 h-8 text-primary" />
          Ranking de Visualizações
        </h2>
        <p className="text-muted-foreground">
          As bolsas mais populares e visualizadas da plataforma
        </p>
      </motion.div>

      {/* Podium */}
      <div
        ref={scrollContainerRef}
        className="flex items-end justify-center gap-2 sm:gap-4 mb-8 overflow-x-auto pb-4 px-4 scroll-smooth"
      >
        {/* Rearrange for podium effect: 2nd, 1st, 3rd */}
        {[top3[1], top3[0], top3[2]].filter(Boolean).map((bolsa, index) => {
          const actualIndex = index === 0 ? 1 : index === 1 ? 0 : 2;
          const Icon = podiumIcons[actualIndex];
          const colorClass = podiumColors[actualIndex];
          const cardHeightClass = podiumCardHeights[actualIndex];
          const position = actualIndex + 1;

          return (
            <motion.div
              key={bolsa.id}
              initial={{ opacity: 0, y: 50, scale: 0.8 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{
                delay: actualIndex * 0.2,
                type: "spring",
                damping: 20,
                stiffness: 300,
              }}
              whileHover={{ scale: 1.05, y: -5 }}
              className="relative flex-shrink-0"
              onClick={() => onBolsaClick(bolsa)}
            >
              <GlassCard
                className={`w-full max-w-[260px] sm:max-w-[280px] md:w-80 ${cardHeightClass} relative flex flex-col cursor-pointer group`}
                hoverable={true}
              >
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 z-10">
                  <Badge
                    className={`${
                      position === 1
                        ? "badge-warning"
                        : position === 2
                        ? "badge-info"
                        : "badge-success"
                    } px-3 py-1 shadow-lg`}
                  >
                    <Icon className="w-3 h-3 mr-1" />
                    {position}º Lugar
                  </Badge>
                </div>

                <GlassCardHeader
                  title={formatProjectTitle(bolsa.nome_projeto)}
                  description={formatPersonName(bolsa.orientador)}
                  className="pt-6"
                  titleClassName="line-clamp-3"
                />
                <GlassCardContent className="flex flex-col flex-grow p-6 pt-3">
                  <div className="mt-auto space-y-3">
                    <div className="flex items-center justify-between">
                      <StatusBadge status={bolsa.status} />
                      <div className="flex items-center gap-1 text-lg font-bold text-primary">
                        <Eye className="w-5 h-5" />
                        {bolsa.view_count}
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground truncate">
                      {bolsa.tipo}
                    </div>
                    {bolsa.candidato_aprovado && (
                      <div className="text-xs text-success font-medium truncate pt-2 border-t border-glass-border">
                        ✓ {formatPersonName(bolsa.candidato_aprovado)}
                      </div>
                    )}
                  </div>
                </GlassCardContent>
              </GlassCard>
            </motion.div>
          );
        })}
      </div>

      {/* Extended Ranking */}
      {rest.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="space-y-4"
        >
          <h3 className="text-xl font-semibold text-center">
            Outros Destaques
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {rest.map((bolsa, index) => (
              <motion.div
                key={bolsa.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1 + index * 0.1 }}
                whileHover={{ scale: 1.02 }}
                className="glass-card p-4 cursor-pointer"
                onClick={() => onBolsaClick(bolsa)}
              >
                <div className="flex items-center justify-between gap-4">
                  {/* Left Side: Number and Text (Flexible) */}
                  <div className="flex flex-1 items-center gap-3 min-w-0">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center text-sm font-bold">
                      {index + 4}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-sm truncate">
                        {formatProjectTitle(bolsa.nome_projeto)}
                      </h4>
                      <p className="text-xs text-muted-foreground truncate">
                        {formatPersonName(bolsa.orientador)}
                      </p>
                    </div>
                  </div>
                  {/* Right Side: Badges (Fixed) */}
                  <div className="flex flex-shrink-0 items-center gap-2 text-sm">
                    <StatusBadge status={bolsa.status} />
                    <div className="flex items-center gap-1 font-medium">
                      <Eye className="w-4 h-4" />
                      {bolsa.view_count}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
