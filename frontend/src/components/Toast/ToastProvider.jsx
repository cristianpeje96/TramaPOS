import React, {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
} from "react";
import { CheckCircle2, AlertTriangle, Info, X } from "lucide-react";
import "./Toast.scss";

const ToastContext = createContext(null);

const ICONOS = {
  exito: CheckCircle2,
  error: AlertTriangle,
  info: Info,
};

let idIncremental = 0;

/**
 * ToastProvider
 * Envuelve la app UNA vez (en main.jsx). Reemplaza alert() nativo y los
 * banners de error/éxito ad-hoc que había repartidos por componente —
 * ahora cualquier componente llama a useToast() y usa mostrarToast(),
 * y la notificación se ve igual en toda la app.
 */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timersRef = useRef({});

  const quitarToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    clearTimeout(timersRef.current[id]);
    delete timersRef.current[id];
  }, []);

  const mostrarToast = useCallback(
    (mensaje, tipo = "info", duracionMs = 4000) => {
      const id = ++idIncremental;
      setToasts((prev) => [...prev, { id, mensaje, tipo }]);
      timersRef.current[id] = setTimeout(() => quitarToast(id), duracionMs);
    },
    [quitarToast],
  );

  return (
    <ToastContext.Provider value={{ mostrarToast }}>
      {children}
      <div className="toast-stack">
        {toasts.map(({ id, mensaje, tipo }) => {
          const Icono = ICONOS[tipo] || Info;
          return (
            <div
              key={id}
              className={`toast-stack__item toast-stack__item--${tipo}`}
            >
              <Icono size={16} strokeWidth={2} />
              <span>{mensaje}</span>
              <button
                type="button"
                onClick={() => quitarToast(id)}
                aria-label="Cerrar"
              >
                <X size={14} strokeWidth={2} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

/**
 * useToast() — devuelve { mostrarToast }.
 * Uso: const { mostrarToast } = useToast();
 *      mostrarToast('Venta creada', 'exito');
 *      mostrarToast(error.message, 'error');
 */
export function useToast() {
  const contexto = useContext(ToastContext);
  if (!contexto) {
    throw new Error("useToast debe usarse dentro de <ToastProvider>");
  }
  return contexto;
}
