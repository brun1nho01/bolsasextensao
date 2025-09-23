import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface StatusBadgeProps {
  status: "disponivel" | "preenchida" | "aguardando" | "aberta";
  className?: string;
}

const statusConfig = {
  disponivel: {
    label: "Disponível",
    className: "badge-success",
  },
  aberta: {
    label: "Aberta",
    className: "badge-info",
  },
  aguardando: {
    label: "Aguardando",
    className: "badge-warning",
  },
  preenchida: {
    label: "Preenchida",
    className: "badge-danger",
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
