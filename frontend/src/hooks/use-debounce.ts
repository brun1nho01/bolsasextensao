import { useState, useEffect } from "react";

/**
 * Hook customizado para "debounce" de um valor.
 * Ele atrasa a atualização de um valor até que um certo tempo tenha passado
 * sem que o valor original tenha sido modificado.
 *
 * @param value O valor a ser debounced (ex: o texto de um input de busca).
 * @param delay O tempo de atraso em milissegundos (ex: 500).
 * @returns O valor debounced.
 */
export function useDebounce<T>(value: T, delay: number): T {
  // Estado para armazenar o valor debounced
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Cria um temporizador que só vai atualizar o valor debounced
    // após o 'delay' especificado.
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Função de limpeza do useEffect:
    // Isso é crucial. Se o 'value' mudar (o usuário digitar de novo),
    // o temporizador anterior é cancelado e um novo é criado.
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]); // O efeito só roda de novo se o valor ou o delay mudarem

  return debouncedValue;
}
