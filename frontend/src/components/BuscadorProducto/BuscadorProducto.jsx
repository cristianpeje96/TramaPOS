import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import { Search, PackageSearch } from "lucide-react";

import { productosApi } from "../../services/api";
import "./BuscadorProducto.scss";

/**
 * BuscadorProducto
 * Foco de F2. Dos formas de uso, pensadas para no frenar la fila:
 *  1. Cajero escribe texto -> autocompletado contra GET /productos/buscar,
 *     y elige la variante (color/grosor) exacta con un click o Enter.
 *  2. Cajero usa lector de código de barras -> el lector "escribe" el
 *     código muy rápido y termina con Enter -> se intenta primero
 *     GET /productos/codigo/{codigo} (match exacto de SKU o barras) antes
 *     de tratarlo como texto de búsqueda libre.
 *
 * Expone `focus()` vía ref para que PosScreen lo enfoque con F2
 * (ver nota de integración en CheckoutPanel.jsx sobre atajos centralizados).
 */
const BuscadorProducto = forwardRef(function BuscadorProducto(
  { onSeleccionarVariante },
  ref,
) {
  const [texto, setTexto] = useState("");
  const [resultados, setResultados] = useState([]);
  const [buscando, setBuscando] = useState(false);
  const [error, setError] = useState(null);
  const [abierto, setAbierto] = useState(true);
  const inputRef = useRef(null);
  const contenedorRef = useRef(null);

  useImperativeHandle(ref, () => ({
    focus: () => {
      setAbierto(true);
      inputRef.current?.focus();
    },
  }));

  // --- Cierra el dropdown de resultados al hacer click fuera del buscador ---
  useEffect(() => {
    const manejarClickFuera = (evento) => {
      if (
        contenedorRef.current &&
        !contenedorRef.current.contains(evento.target)
      ) {
        setAbierto(false);
      }
    };
    document.addEventListener("mousedown", manejarClickFuera);
    return () => document.removeEventListener("mousedown", manejarClickFuera);
  }, []);

  // --- Autocompletado con debounce ---
  useEffect(() => {
    if (texto.trim().length < 1) {
      setResultados([]);
      return;
    }
    setAbierto(true);
    const temporizador = setTimeout(async () => {
      setBuscando(true);
      setError(null);
      try {
        const encontrados = await productosApi.buscar(texto.trim());
        setResultados(encontrados);
      } catch (err) {
        setError(err.message);
        setResultados([]);
      } finally {
        setBuscando(false);
      }
    }, 250);
    return () => clearTimeout(temporizador);
  }, [texto]);

  const seleccionarVariante = (producto, variante) => {
    onSeleccionarVariante?.({
      variante_id: variante.id,
      cantidad: 1,
      precio_unitario: variante.precio_venta,
      nombre: producto.nombre,
      color: variante.color,
      grosor: variante.grosor,
      sku: variante.sku,
      unidad_medida: producto.unidad_medida,
    });
    setTexto("");
    setResultados([]);
    setAbierto(true);
    inputRef.current?.focus();
  };

  const manejarEnter = async (evento) => {
    if (evento.key !== "Enter" || !texto.trim()) return;
    evento.preventDefault();

    // Intento 1: match exacto por SKU o código de barras (lector físico)
    try {
      const producto = await productosApi.buscarPorCodigo(texto.trim());
      if (producto.variantes.length === 1) {
        seleccionarVariante(producto, producto.variantes[0]);
        return;
      }
      // Si el producto tiene varias variantes, se muestran para elegir
      setResultados([producto]);
      return;
    } catch {
      // No fue un código exacto — se deja que el autocompletado normal
      // (que ya corrió por el debounce) muestre los resultados de texto libre.
    }
  };

  return (
    <div className="buscador-producto" ref={contenedorRef}>
      <div className="buscador-producto__input-wrap">
        <Search size={16} strokeWidth={2} className="buscador-producto__icon" />
        <input
          ref={inputRef}
          type="text"
          className="buscador-producto__input"
          placeholder="Buscar producto o escanear código (F2)"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onFocus={() => setAbierto(true)}
          onKeyDown={manejarEnter}
        />
      </div>

      {error && abierto && <p className="buscador-producto__error">{error}</p>}

      {abierto && resultados.length > 0 && (
        <div className="buscador-producto__resultados">
          {resultados.map((producto) => (
            <div key={producto.id} className="buscador-producto__producto">
              <p className="buscador-producto__producto-nombre">
                {producto.nombre}
              </p>
              <div className="buscador-producto__variantes">
                {producto.variantes.map((variante) => {
                  const sinStock = variante.stock_actual <= 0;
                  return (
                    <button
                      key={variante.id}
                      type="button"
                      className="buscador-producto__variante"
                      disabled={sinStock}
                      onClick={() => seleccionarVariante(producto, variante)}
                    >
                      <span className="buscador-producto__variante-nombre">
                        {[variante.color, variante.grosor]
                          .filter(Boolean)
                          .join(" · ") || variante.sku}
                      </span>
                      <span className="buscador-producto__variante-precio u-cifra">
                        ${variante.precio_venta.toLocaleString("es-CO")}
                      </span>
                      {sinStock && (
                        <span className="buscador-producto__variante-agotado">
                          Agotado
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {abierto &&
        !buscando &&
        texto.trim().length > 0 &&
        resultados.length === 0 &&
        !error && (
          <div className="buscador-producto__vacio">
            <PackageSearch size={16} strokeWidth={2} />
            <span>Sin resultados para "{texto}"</span>
          </div>
        )}
    </div>
  );
});

export default BuscadorProducto;
