import { useCallback, useEffect, useRef, useState } from "react";

const INTERVALO_RECONEXION_MS = 3000;

/**
 * useHardwareAgent
 * Mantiene la conexión WebSocket con hardware_agent.py (el script Python
 * que corre local en el PC de la caja y habla con la ticketera/cajón).
 *
 * OJO: esto se conecta a VITE_HARDWARE_AGENT_WS_URL (ws://localhost:9100),
 * que es DISTINTO de VITE_BACKEND_WS_URL (el hub de notificaciones del
 * backend). Este hook nunca debe apuntar al backend — el agente de
 * hardware es un proceso local independiente.
 *
 * Reconexión automática: si el POS se abre ANTES de arrancar el agente
 * (o si el agente se cae un momento), este hook reintenta cada 3s en
 * vez de quedarse desconectado hasta que alguien refresque la página
 * manualmente.
 */
export function useHardwareAgent() {
  const [conectado, setConectado] = useState(false);
  const socketRef = useRef(null);
  const timeoutReconexionRef = useRef(null);
  const montadoRef = useRef(true);

  const conectar = useCallback(() => {
    const url =
      import.meta.env.VITE_HARDWARE_AGENT_WS_URL || "ws://localhost:9100";
    const socket = new WebSocket(url);

    socket.onopen = () => {
      if (!montadoRef.current) return;
      setConectado(true);
    };

    const programarReconexion = () => {
      if (!montadoRef.current) return;
      setConectado(false);
      clearTimeout(timeoutReconexionRef.current);
      timeoutReconexionRef.current = setTimeout(
        conectar,
        INTERVALO_RECONEXION_MS,
      );
    };

    socket.onclose = programarReconexion;
    socket.onerror = programarReconexion;

    socketRef.current = socket;
  }, []);

  useEffect(() => {
    montadoRef.current = true;
    conectar();

    return () => {
      montadoRef.current = false;
      clearTimeout(timeoutReconexionRef.current);
      // Evita que el reintento programado dispare un setState después
      // de que el componente se desmontó, y cierra la conexión activa.
      if (socketRef.current) {
        socketRef.current.onclose = null;
        socketRef.current.onerror = null;
        socketRef.current.close();
      }
    };
  }, [conectar]);

  const enviarComando = useCallback((payload) => {
    if (socketRef.current?.readyState !== WebSocket.OPEN) {
      console.warn(
        "Agente de hardware no conectado — no se pudo enviar el comando",
        payload,
      );
      return false;
    }
    socketRef.current.send(JSON.stringify(payload));
    return true;
  }, []);

  /** Ctrl+Shift+O — abre el cajón SIN imprimir ticket. */
  const abrirCajonManual = useCallback(
    () => enviarComando({ accion: "abrir_cajon_manual" }),
    [enviarComando],
  );

  /** F10 — imprime el ticket de la venta y abre el cajón. */
  const procesarVenta = useCallback(
    (ticketTexto) =>
      enviarComando({ accion: "procesar_venta", ticket_texto: ticketTexto }),
    [enviarComando],
  );

  return { conectado, abrirCajonManual, procesarVenta };
}
