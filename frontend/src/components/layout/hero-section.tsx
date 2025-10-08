import { motion } from "framer-motion";
import { Search, Sparkles, Package, CheckCircle } from "lucide-react";
import { useState, useEffect } from "react";
import { useDebounce } from "@/hooks/use-debounce";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";

interface HeroSectionProps {
  onSearch: (query: string) => void;
  searchQuery: string;
  totalProjetos?: number;
  bolsasPreenchidas?: number;
}

export function HeroSection({
  onSearch,
  searchQuery,
  totalProjetos,
  bolsasPreenchidas,
}: HeroSectionProps) {
  const [inputValue, setInputValue] = useState(searchQuery);
  const debouncedSearchQuery = useDebounce(inputValue, 300); // 300ms de atraso

  useEffect(() => {
    // Sincroniza o input se a busca for limpa por um filtro externo
    setInputValue(searchQuery);
  }, [searchQuery]);

  useEffect(() => {
    // Dispara a busca apenas quando o valor debounced muda
    // Remove onSearch das dependências para evitar loops infinitos
    onSearch(debouncedSearchQuery);
  }, [debouncedSearchQuery]);

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden">
      {/* Hero Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 py-20 sm:py-32">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center"
        >
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="text-2xl sm:text-4xl md:text-6xl lg:text-7xl font-bold mb-6 px-4"
          >
            <br />
            Descubra Oportunidades de Extensão
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
            className="text-base sm:text-lg md:text-xl text-muted-foreground mb-12 max-w-2xl mx-auto leading-relaxed px-4"
          >
            Explore as bolsas de extensão da UENF com nossa interface moderna.
            Filtros avançados, visualizações detalhadas e atualizações em tempo
            real.
          </motion.p>

          {/* Search Bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8 }}
            className="max-w-2xl mx-auto"
          >
            <div className="relative glass-card p-2">
              <div className="flex items-center gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
                  <Input
                    placeholder="Buscar por projeto, orientador, palavra-chave..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    className="pl-12 pr-4 py-6 bg-transparent border-0 text-lg placeholder:text-muted-foreground focus-visible:ring-0"
                  />
                </div>
                <Button
                  size="lg"
                  className="px-8 py-6 gradient-primary border-0 shadow-glow hover:shadow-glow"
                >
                  <Search className="w-5 h-5 mr-2" />
                  Buscar
                </Button>
              </div>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.8 }}
            className="mt-16 grid grid-cols-1 gap-4 sm:gap-8 sm:grid-cols-2 max-w-md mx-auto px-4"
          >
            <GlassCard className="flex items-center gap-4 p-6 text-left">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/20 flex-shrink-0">
                <Package className="h-6 w-6 text-primary" />
              </div>
              <div>
                <div className="text-3xl font-bold text-primary">
                  {totalProjetos ?? "..."}
                </div>
                <div className="text-sm text-muted-foreground">
                  Vagas Totais
                </div>
              </div>
            </GlassCard>

            <GlassCard className="flex items-center gap-4 p-6 text-left">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-500/20 flex-shrink-0">
                <CheckCircle className="h-6 w-6 text-green-400" />
              </div>
              <div>
                <div className="text-3xl font-bold text-success">
                  {bolsasPreenchidas ?? "..."}
                </div>
                <div className="text-sm text-muted-foreground">Preenchidas</div>
              </div>
            </GlassCard>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
