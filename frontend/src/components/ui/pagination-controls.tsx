import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationControlsProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string; // Adiciona a propriedade className
}

export function PaginationControls({
  currentPage,
  totalPages,
  onPageChange,
  className = "", // Valor padrão
}: PaginationControlsProps) {
  if (totalPages <= 1) {
    return null;
  }

  const handlePrevious = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };

  return (
    <div className={`flex items-center justify-end gap-2 ${className}`}>
      <Button
        variant="outline"
        size="icon"
        onClick={handlePrevious}
        disabled={currentPage === 1}
        className="glass h-8 w-8"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>
      <div className="text-sm font-medium text-muted-foreground tabular-nums">
        {currentPage}/{totalPages}
      </div>
      <Button
        variant="outline"
        size="icon"
        onClick={handleNext}
        disabled={currentPage === totalPages}
        className="glass h-8 w-8"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
}
