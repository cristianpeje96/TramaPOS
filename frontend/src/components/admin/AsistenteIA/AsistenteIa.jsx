import React, { useEffect, useRef, useState } from "react";
import { Sparkles, Send, Bot, User } from "lucide-react";

import { asistenteIaApi } from "../../../services/api";
import "./AsistenteIA.scss";

const PREGUNTAS_SUGERIDAS = [
  "¿Cuánto vendí en los últimos 7 días?",
  "¿Qué productos tienen stock bajo ahora mismo?",
  "¿Cuáles son mis 5 productos más vendidos este mes?",
  "Compara mis ventas de este mes con el anterior",
];

export default function AsistenteIA() {
  const [mensajes, setMensajes] = useState([
    {
      rol: "assistant",
      contenido:
        "Hola, soy el asistente de TramaPos. Puedo consultar tus ventas, stock y productos más vendidos para darte respuestas basadas en tus datos reales — nunca invento cifras. ¿En qué te ayudo?",
    },
  ]);
  const [entrada, setEntrada] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState(null);
  const finRef = useRef(null);

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes]);

  const enviarMensaje = async (texto) => {
    const mensaje = (texto ?? entrada).trim();
    if (!mensaje || enviando) return;

    const historialParaApi = mensajes.map((m) => ({
      rol: m.rol,
      contenido: m.contenido,
    }));
    setMensajes((prev) => [...prev, { rol: "user", contenido: mensaje }]);
    setEntrada("");
    setEnviando(true);
    setError(null);

    try {
      const { respuesta } = await asistenteIaApi.consultar(
        mensaje,
        historialParaApi,
      );
      setMensajes((prev) => [
        ...prev,
        { rol: "assistant", contenido: respuesta },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  };

  const manejarSubmit = (evento) => {
    evento.preventDefault();
    enviarMensaje();
  };

  return (
    <div className="asistente-ia">
      <h2 className="asistente-ia__titulo">
        <Sparkles size={18} strokeWidth={2} />
        Asistente de IA
      </h2>
      <p className="asistente-ia__ayuda">
        Consulta tus datos reales de ventas e inventario en lenguaje natural. Es
        de solo lectura — nunca crea ni modifica nada por sí solo.
      </p>

      <div className="asistente-ia__chat">
        {mensajes.map((m, i) => (
          <div
            key={i}
            className={`asistente-ia__mensaje asistente-ia__mensaje--${m.rol}`}
          >
            <span className="asistente-ia__mensaje-icono">
              {m.rol === "assistant" ? (
                <Bot size={14} strokeWidth={2} />
              ) : (
                <User size={14} strokeWidth={2} />
              )}
            </span>
            <span className="asistente-ia__mensaje-texto">{m.contenido}</span>
          </div>
        ))}
        {enviando && (
          <div className="asistente-ia__mensaje asistente-ia__mensaje--assistant">
            <span className="asistente-ia__mensaje-icono">
              <Bot size={14} strokeWidth={2} />
            </span>
            <span className="asistente-ia__mensaje-texto asistente-ia__pensando">
              Consultando tus datos…
            </span>
          </div>
        )}
        <div ref={finRef} />
      </div>

      {error && <p className="asistente-ia__error">{error}</p>}

      {mensajes.length <= 1 && (
        <div className="asistente-ia__sugeridas">
          {PREGUNTAS_SUGERIDAS.map((p) => (
            <button key={p} type="button" onClick={() => enviarMensaje(p)}>
              {p}
            </button>
          ))}
        </div>
      )}

      <form className="asistente-ia__form" onSubmit={manejarSubmit}>
        <input
          type="text"
          placeholder="Pregunta sobre tus ventas, stock o finanzas…"
          value={entrada}
          onChange={(e) => setEntrada(e.target.value)}
          disabled={enviando}
        />
        <button type="submit" disabled={enviando || !entrada.trim()}>
          <Send size={16} strokeWidth={2} />
        </button>
      </form>
    </div>
  );
}
