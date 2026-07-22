import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import { Search, PackageSearch, Plus } from "lucide-react";

import { categoriasApi, productosApi } from "../../services/api";
import { useToast } from "../Toast/ToastProvider";
import "./BuscadorProducto.scss";

/**
 * BuscadorProducto
 * Foco de F2. Tres formas de uso, pensadas para no frenar la fila:
 *  1. Cajero escribe texto -> autocompletado contra GET /productos/buscar,
 *     y elige la variante (color/grosor) exacta con un click o Enter.
 *  2. Cajero usa lector de código de barras -> match exacto por SKU o
 *     código de barras antes de caer a texto libre.
 *  3. Si NO existe (típico de artículos pequeños: botones, agujas, y
 *     demás mercería que nunca se catalogó) -> "Alta rápida": nombre +
 *     precio + cantidad, sin salir de la pantalla de cobro, para que
 *     nunca termine vendiéndose como "genérico" sin quedar en el
 *     inventario real.
 *
 * Expone `focus()` vía ref para que PosScreen lo enfoque con F2.
 */
const BuscadorProducto = forwardRef(function BuscadorProducto(
  { onSeleccionarVariante },
  ref,
) {
  const { mostrarToast } = useToast();
  const [texto, setTexto] = useState("");
  const [resultados, setResultados] = useState([]);
  const [buscando, setBuscando] = useState(false);
  const [error, setError] = useState(null);
  const [abierto, setAbierto] = useState(true);
  const inputRef = useRef(null);
  const contenedorRef = useRef(null);

  // --- Alta rápida ---
  const [categorias, setCategorias] = useState([]);
  const [mostrarAltaRapida, setMostrarAltaRapida] = useState(false);
  const [precioRapido, setPrecioRapido] = useState("");
  const [cantidadRapida, setCantidadRapida] = useState("1");
  const [categoriaRapidaId, setCategoriaRapidaId] = useState("");
  const [guardandoRapido, setGuardandoRapido] = useState(false);

  useImperativeHandle(ref, () => ({
    focus: () => {
      setAbierto(true);
      inputRef.current?.focus();
    },
  }));

  useEffect(() => {
    categoriasApi
      .listar()
      .then(setCategorias)
      .catch(() => setCategorias([]));
  }, []);

  // --- Cierra el dropdown de resultados al hacer click fuera del buscador ---
  useEffect(() => {
    const manejarClickFuera = (evento) => {
      if (
        contenedorRef.current &&
        !contenedorRef.current.contains(evento.target)
      ) {
        setAbierto(false);
        setMostrarAltaRapida(false);
      }
    };
    document.addEventListener("mousedown", manejarClickFuera);
    return () => document.removeEventListener("mousedown", manejarClickFuera);
  }, []);

  // --- Autocompletado con debounce ---
  useEffect(() => {
    setMostrarAltaRapida(false);
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

    try {
      const producto = await productosApi.buscarPorCodigo(texto.trim());
      if (producto.variantes.length === 1) {
        seleccionarVariante(producto, producto.variantes[0]);
        return;
      }
      setResultados([producto]);
    } catch {
      // No fue un código exacto — se deja que el autocompletado normal
      // (que ya corrió por el debounce) muestre los resultados de texto libre.
    }
  };

  const crearAltaRapida = async () => {
    if (!texto.trim() || !precioRapido) return;
    setGuardandoRapido(true);
    setError(null);
    try {
      const producto = await productosApi.altaRapida({
        nombre: texto.trim(),
        precio_venta: Number(precioRapido),
        stock_inicial: Number(cantidadRapida) || 1,
        categoria_id: categoriaRapidaId ? Number(categoriaRapidaId) : null,
      });
      mostrarToast(
        `"${producto.nombre}" creado y agregado a la venta`,
        "exito",
      );
      seleccionarVariante(producto, producto.variantes[0]);
      setPrecioRapido("");
      setCantidadRapida("1");
      setMostrarAltaRapida(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardandoRapido(false);
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
            {!mostrarAltaRapida ? (
              <>
                <PackageSearch size={16} strokeWidth={2} />
                <span>Sin resultados para "{texto}"</span>
                <button
                  type="button"
                  className="buscador-producto__boton-alta-rapida"
                  onClick={() => setMostrarAltaRapida(true)}
                >
                  <Plus size={13} strokeWidth={2} />
                  Crear "{texto}" ahora
                </button>
              </>
            ) : (
              <div className="buscador-producto__alta-rapida">
                <p className="buscador-producto__alta-rapida-titulo">
                  Nuevo producto: <strong>{texto}</strong>
                </p>
                <div className="buscador-producto__alta-rapida-campos">
                  <input
                    type="number"
                    min="0"
                    placeholder="Precio"
                    value={precioRapido}
                    onChange={(e) => setPrecioRapido(e.target.value)}
                    autoFocus
                  />
                  <input
                    type="number"
                    min="0"
                    placeholder="Cantidad"
                    value={cantidadRapida}
                    onChange={(e) => setCantidadRapida(e.target.value)}
                  />
                  <select
                    value={categoriaRapidaId}
                    onChange={(e) => setCategoriaRapidaId(e.target.value)}
                  >
                    <option value="">Sin categoría</option>
                    {categorias.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nombre}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="button"
                  className="buscador-producto__alta-rapida-guardar"
                  disabled={guardandoRapido || !precioRapido}
                  onClick={crearAltaRapida}
                >
                  {guardandoRapido ? "Creando…" : "Crear y agregar a la venta"}
                </button>
              </div>
            )}
          </div>
        )}
    </div>
  );
});

export default BuscadorProducto;
