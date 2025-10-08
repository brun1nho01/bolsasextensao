import { motion } from "framer-motion";
import { GlassCard } from "@/components/ui/glass-card";

export function BolsaCardSkeleton({ index = 0 }: { index?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
    >
      <GlassCard className="h-full p-4 space-y-3">
        {/* Top badges */}
        <div className="flex justify-between items-start">
          <div className="flex gap-2">
            <div className="h-5 w-12 rounded-full bg-muted animate-pulse"></div>
          </div>
          <div className="h-6 w-24 rounded-full bg-muted animate-pulse"></div>
        </div>

        {/* Title */}
        <div className="space-y-2 pt-2">
          <div className="h-5 w-full rounded-md bg-muted animate-pulse"></div>
          <div className="h-5 w-3/4 rounded-md bg-muted animate-pulse"></div>
        </div>

        {/* Info badges */}
        <div className="flex items-center gap-2 pt-2">
          <div className="h-6 w-20 rounded-full bg-muted animate-pulse"></div>
          <div className="h-6 w-24 rounded-full bg-muted animate-pulse"></div>
        </div>

        {/* Orientador */}
        <div className="flex items-center gap-2 pt-4">
          <div className="h-4 w-4 rounded-full bg-muted animate-pulse"></div>
          <div className="flex-1 space-y-2">
            <div className="h-4 w-1/2 rounded-md bg-muted animate-pulse"></div>
            <div className="h-3 w-1/4 rounded-md bg-muted animate-pulse"></div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4">
          <div className="h-4 w-16 rounded-md bg-muted animate-pulse"></div>
          <div className="h-4 w-16 rounded-md bg-muted animate-pulse"></div>
        </div>
      </GlassCard>
    </motion.div>
  );
}
