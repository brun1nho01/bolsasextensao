import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Corrige a data que vem da API (em formato YYYY-MM-DD) para evitar problemas de fuso horário.
 * A string de data é tratada como se estivesse no fuso horário local, e não em UTC.
 * @param dateString A data no formato "YYYY-MM-DD" ou uma string de data completa.
 * @returns Um objeto Date corrigido.
 */
export function parseDateAsLocal(
  dateString: string | null | undefined
): Date | null {
  if (!dateString) return null;
  // Adiciona a hora para garantir que seja interpretado como local e não UTC
  const correctedDateString = `${dateString.substring(0, 10)}T00:00:00`;
  const date = new Date(correctedDateString);
  return date;
}

/**
 * Formata um título de projeto para capitalização adequada (primeira letra de cada palavra em maiúsculo).
 * @param title O título a ser formatado.
 * @returns O título formatado.
 */
export function formatProjectTitle(title: string): string {
  if (!title) return "";
  return title
    .toLowerCase()
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Formata um nome de pessoa para capitalização adequada, tratando nomes compostos.
 * @param name O nome a ser formatado.
 * @returns O nome formatado.
 */
export function formatPersonName(name: string): string {
  if (!name) return "";
  const exceptions = ["de", "da", "do", "dos", "das"];
  return name
    .toLowerCase()
    .split(" ")
    .map((word) =>
      exceptions.includes(word)
        ? word
        : word.charAt(0).toUpperCase() + word.slice(1)
    )
    .join(" ");
}
