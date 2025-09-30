import React, { useState } from "react";
import { useViewSession } from "@/hooks/useViewSession";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Eye, Clock, Hash, RefreshCw, X } from "lucide-react";

/**
 * Componente de debug para monitorar o sistema de view tracking
 * Apenas para desenvolvimento - remover em produção
 */
export const ViewSessionDebug: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { sessionId, getSessionStats, clearViewedBolsas } = useViewSession();
  const [stats, setStats] = useState(getSessionStats());

  const refreshStats = () => {
    setStats(getSessionStats());
  };

  const handleClearViews = () => {
    clearViewedBolsas();
    refreshStats();
  };

  if (!isOpen) {
    return (
      <Button
        onClick={() => setIsOpen(true)}
        size="sm"
        variant="outline"
        className="fixed bottom-20 right-4 z-[9998] bg-muted/80 backdrop-blur"
        title="Debug: View Session"
      >
        <Eye className="w-4 h-4" />
        Debug
      </Button>
    );
  }

  return (
    <Card className="fixed bottom-4 right-4 z-[9998] w-80 bg-background/95 backdrop-blur border-2">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Eye className="w-4 h-4" />
            View Session Debug
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsOpen(false)}
            className="h-6 w-6 p-0"
          >
            <X className="w-3 h-3" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 text-xs">
        {/* Session Info */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Hash className="w-3 h-3 text-muted-foreground" />
            <span className="text-muted-foreground">Session ID:</span>
          </div>
          <code className="text-[10px] bg-muted p-1 rounded block break-all">
            {sessionId}
          </code>
        </div>

        {/* Duration */}
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-muted-foreground">
            <Clock className="w-3 h-3" />
            Duração:
          </span>
          <Badge variant="secondary" className="text-xs">
            {stats.durationFormatted}
          </Badge>
        </div>

        {/* View Count */}
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-muted-foreground">
            <Eye className="w-3 h-3" />
            Bolsas vistas:
          </span>
          <Badge variant="secondary" className="text-xs">
            {stats.viewedCount}
          </Badge>
        </div>

        {/* Viewed Bolsas */}
        {stats.viewedBolsas.length > 0 && (
          <div className="space-y-2">
            <span className="text-muted-foreground">IDs Visualizados:</span>
            <div className="max-h-24 overflow-y-auto space-y-1">
              {stats.viewedBolsas.map((bolsaId, index) => (
                <code
                  key={bolsaId}
                  className="text-[9px] bg-success/10 text-success p-1 rounded block"
                >
                  {index + 1}. {bolsaId.slice(0, 8)}...
                </code>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button
            onClick={refreshStats}
            size="sm"
            variant="outline"
            className="flex-1 h-7 text-xs"
          >
            <RefreshCw className="w-3 h-3 mr-1" />
            Refresh
          </Button>
          <Button
            onClick={handleClearViews}
            size="sm"
            variant="destructive"
            className="flex-1 h-7 text-xs"
            disabled={stats.viewedCount === 0}
          >
            <X className="w-3 h-3 mr-1" />
            Limpar
          </Button>
        </div>

        {/* Usage Info */}
        <div className="text-[10px] text-muted-foreground bg-muted/50 p-2 rounded">
          <strong>Como funciona:</strong>
          <br />• Primeira view na sessão = incrementa contador
          <br />• Views repetidas = não incrementa
          <br />• Reset automático quando fecha navegador
        </div>
      </CardContent>
    </Card>
  );
};
