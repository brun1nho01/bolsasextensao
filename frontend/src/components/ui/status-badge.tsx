import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface StatusBadgeProps {
  status: "disponivel" | "preenchida" | "aguardando" | "aberta";
  className?: string;
}

const statusConfig = {
  disponivel: {
    label: "Disponível",
    className: "badge-info", // Azul - bolsas que retornaram após resultado
  },
  aberta: {
    label: "Aberta",
    className: "badge-success", // Verde - inscrições abertas
  },
  aguardando: {
    label: "Aguardando",
    className: "badge-warning", // Amarela - aguardando resultado
  },
  preenchida: {
    label: "Preenchida",
    className: "badge-danger", // Vermelha - já preenchida
  },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <Badge
      variant="outline"
      className={cn(
        config.className,
        "px-3 py-1 text-xs font-medium rounded-full animate-pulse",
        className
      )}
    >
      {config.label}
    </Badge>
  );
}
