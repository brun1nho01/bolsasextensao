import { cn } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { motion } from "framer-motion";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hoverable?: boolean;
  animated?: boolean;
  onClick?: () => void;
}

export function GlassCard({
  children,
  className,
  hoverable = true,
  animated = true,
  onClick,
}: GlassCardProps) {
  const CardComponent = animated ? motion.div : "div";

  return (
    <CardComponent
      {...(animated && {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        whileHover: hoverable ? { y: -2, scale: 1.02 } : undefined,
        transition: { type: "spring", damping: 25, stiffness: 300 },
      })}
      className={cn("glass-card", hoverable && "cursor-pointer", className)}
      onClick={onClick}
    >
      {children}
    </CardComponent>
  );
}

interface GlassCardHeaderProps {
  title: string;
  description?: string;
  className?: string;
  titleClassName?: string; // Adiciona a nova propriedade
}

export function GlassCardHeader({
  title,
  description,
  className,
  titleClassName, // Recebe a nova propriedade
}: GlassCardHeaderProps) {
  return (
    <CardHeader className={cn("pb-3", className)}>
      <CardTitle
        className={cn("text-lg font-semibold text-foreground", titleClassName)}
      >
        {title}
      </CardTitle>
      {description && (
        <CardDescription className="text-muted-foreground">
          {description}
        </CardDescription>
      )}
    </CardHeader>
  );
}

export function GlassCardContent({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <CardContent className={cn("pt-0", className)}>{children}</CardContent>
  );
}
