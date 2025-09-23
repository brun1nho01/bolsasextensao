import React, { useState } from "react";
import { X, MessageCircle, Check, AlertCircle, Loader2 } from "lucide-react";

interface WhatsAppFloatingButtonProps {
  apiUrl?: string;
}

export default function WhatsAppFloatingButton({
  apiUrl = "/api",
}: WhatsAppFloatingButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [whatsapp, setWhatsapp] = useState("");
  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!whatsapp.trim()) {
      setStatus("error");
      setMessage("Digite seu número de WhatsApp");
      return;
    }

    setStatus("loading");
    setMessage("Cadastrando...");

    try {
      const response = await fetch(`${apiUrl}/alertas/whatsapp`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ whatsapp: whatsapp.trim() }),
      });

      const result = await response.json();

      if (response.ok && result.status === "success") {
        setStatus("success");
        setMessage(result.message || "Cadastrado com sucesso!");
        setWhatsapp("");

        // Fechar automaticamente após 3 segundos
        setTimeout(() => {
          setIsOpen(false);
          setStatus("idle");
          setMessage("");
        }, 3000);
      } else {
        setStatus("error");
        setMessage(result.message || "Erro ao cadastrar");
      }
    } catch (error) {
      setStatus("error");
      setMessage("Erro de conexão. Tente novamente.");
    }
  };

  const formatPhoneNumber = (value: string) => {
    // Remove tudo que não é dígito
    const numbers = value.replace(/\D/g, "");

    // Aplica máscara brasileira
    if (numbers.length <= 2) return numbers;
    if (numbers.length <= 7)
      return `(${numbers.slice(0, 2)}) ${numbers.slice(2)}`;
    if (numbers.length <= 11)
      return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(
        7
      )}`;
    return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(
      7,
      11
    )}`;
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneNumber(e.target.value);
    setWhatsapp(formatted);
  };

  return (
    <>
      {/* Botão Flutuante */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 bg-green-500 hover:bg-green-600 text-white p-4 rounded-full shadow-lg transition-all duration-200 hover:scale-110 focus:outline-none focus:ring-4 focus:ring-green-300"
        title="Receber alertas no WhatsApp"
        aria-label="Cadastrar WhatsApp para alertas"
      >
        <MessageCircle size={24} />
      </button>

      {/* Modal/Popup */}
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          {/* Overlay */}
          <div
            className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
            onClick={() => setIsOpen(false)}
          />

          {/* Modal */}
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative transform overflow-hidden rounded-lg bg-white px-6 py-6 shadow-xl transition-all sm:w-full sm:max-w-md">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <div className="bg-green-100 p-2 rounded-full">
                    <MessageCircle className="text-green-600" size={20} />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Alertas WhatsApp
                  </h3>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-500 transition-colors"
                  aria-label="Fechar"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Descrição */}
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  Receba alertas instantâneos quando:
                </p>
                <ul className="text-xs text-gray-500 space-y-1 pl-4">
                  <li>
                    🎓 Novos editais de <strong>extensão</strong> são publicados
                  </li>
                  <li>
                    🏆 <strong>Resultados</strong> de seleções são divulgados
                  </li>
                </ul>
              </div>

              {/* Formulário */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label
                    htmlFor="whatsapp"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Número do WhatsApp
                  </label>
                  <input
                    type="tel"
                    id="whatsapp"
                    value={whatsapp}
                    onChange={handlePhoneChange}
                    placeholder="(22) 99999-9999"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                    disabled={status === "loading"}
                    maxLength={15}
                  />
                </div>

                {/* Status Message */}
                {message && (
                  <div
                    className={`flex items-center space-x-2 p-3 rounded-md text-sm ${
                      status === "success"
                        ? "bg-green-50 text-green-800 border border-green-200"
                        : status === "error"
                        ? "bg-red-50 text-red-800 border border-red-200"
                        : "bg-blue-50 text-blue-800 border border-blue-200"
                    }`}
                  >
                    {status === "success" && <Check size={16} />}
                    {status === "error" && <AlertCircle size={16} />}
                    {status === "loading" && (
                      <Loader2 size={16} className="animate-spin" />
                    )}
                    <span>{message}</span>
                  </div>
                )}

                {/* Botão Submit */}
                <button
                  type="submit"
                  disabled={status === "loading" || status === "success"}
                  className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
                    status === "success"
                      ? "bg-green-100 text-green-800 cursor-not-allowed"
                      : status === "loading"
                      ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                      : "bg-green-600 text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
                  }`}
                >
                  {status === "loading" && (
                    <Loader2 size={16} className="animate-spin inline mr-2" />
                  )}
                  {status === "success"
                    ? "✅ Cadastrado!"
                    : status === "loading"
                    ? "Cadastrando..."
                    : "📱 Receber Alertas"}
                </button>
              </form>

              {/* Footer */}
              <p className="text-xs text-gray-400 text-center mt-4">
                Seus dados são seguros. Responda "PARAR" para cancelar.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
