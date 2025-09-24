import React, { useState } from "react";
import { X, Send, Check, AlertCircle, Loader2, Info } from "lucide-react";

interface TelegramFloatingButtonProps {
  apiUrl?: string;
}

export default function TelegramFloatingButton({
  apiUrl = "/api",
}: TelegramFloatingButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [telegram, setTelegram] = useState("");
  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!telegram.trim()) {
      setStatus("error");
      setMessage("Digite seu ID do Telegram");
      return;
    }

    setStatus("loading");
    setMessage("Cadastrando...");

    try {
      const response = await fetch(`${apiUrl}/alertas/telegram`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ telegram: telegram.trim() }),
      });

      const result = await response.json();

      if (response.ok && result.status === "success") {
        setStatus("success");
        setMessage(result.message || "Cadastrado com sucesso!");
        setTelegram("");

        // Fechar automaticamente após 4 segundos
        setTimeout(() => {
          setIsOpen(false);
          setStatus("idle");
          setMessage("");
        }, 4000);
      } else {
        setStatus("error");
        setMessage(result.message || "Erro ao cadastrar. Tente novamente.");
      }
    } catch (error) {
      setStatus("error");
      setMessage("Erro de conexão. Verifique sua internet.");
      console.error("Erro ao cadastrar Telegram:", error);
    }
  };

  const formatTelegramId = (value: string) => {
    // Remove espaços e caracteres especiais
    let formatted = value.trim().replace(/[^a-zA-Z0-9_@]/g, "");

    // Se for só números, manter assim (chat_id) - PREFERIDO
    if (/^\d+$/.test(formatted)) {
      return formatted.length > 15 ? formatted.substring(0, 15) : formatted;
    }

    // Se não for números, tratar como username
    // Se não começar com @, adicionar
    if (formatted && !formatted.startsWith("@")) {
      formatted = "@" + formatted;
    }

    // Limitar a 33 caracteres (@ + 32 caracteres máximos do Telegram)
    if (formatted.length > 33) {
      formatted = formatted.substring(0, 33);
    }

    return formatted;
  };

  const handleTelegramChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatTelegramId(e.target.value);
    setTelegram(formatted);
    console.log(
      "Telegram digitado:",
      e.target.value,
      "→ Formatado:",
      formatted
    );
  };

  return (
    <>
      {/* Botão Flutuante */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-[9999] bg-blue-500 hover:bg-blue-600 text-white rounded-full shadow-lg transition-all duration-200 hover:scale-110 focus:outline-none focus:ring-4 focus:ring-blue-300 flex items-center justify-center"
        title="Receber alertas no Telegram"
        aria-label="Cadastrar Telegram para alertas"
        style={{
          zIndex: 9999,
          width: "56px",
          height: "56px",
        }}
      >
        <Send size={20} />
      </button>

      {/* Modal/Popup */}
      {isOpen && (
        <div className="fixed inset-0 z-[9999] overflow-y-auto">
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
                  <div className="bg-blue-100 p-2 rounded-full">
                    <Send className="text-blue-600" size={20} />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Alertas Telegram
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

              {/* Como Encontrar ID */}
              <div className="mb-4 p-3 bg-blue-50 rounded-md">
                <div className="flex items-start space-x-2">
                  <Info
                    className="text-blue-500 flex-shrink-0 mt-0.5"
                    size={14}
                  />
                  <div>
                    <p className="text-xs text-blue-800 font-medium mb-1">
                      Como pegar seu Chat ID:
                    </p>
                    <ol className="text-xs text-blue-700 space-y-1 list-decimal list-inside">
                      <li>
                        Procure <code>@uenf_alertas_bot</code> no Telegram
                      </li>
                      <li>
                        Envie <code>/start</code>
                      </li>
                      <li>O bot responderá com seu Chat ID</li>
                      <li>Copie o número e cole aqui</li>
                    </ol>
                    <p className="text-xs text-blue-600 mt-1 font-medium">
                      💡 Use sempre números (ex: 123456789) - é mais confiável
                    </p>
                  </div>
                </div>
              </div>

              {/* Formulário */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label
                    htmlFor="telegram"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    ID do Telegram
                  </label>
                  <input
                    type="text"
                    id="telegram"
                    value={telegram}
                    onChange={handleTelegramChange}
                    placeholder="123456789"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors text-gray-900 bg-white"
                    disabled={status === "loading"}
                    maxLength={33}
                    autoComplete="username"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Use seu Chat ID numérico (ex: 1917031847)
                  </p>
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
                      : "bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                100% gratuito e seguro. Digite "/stop" para cancelar.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
