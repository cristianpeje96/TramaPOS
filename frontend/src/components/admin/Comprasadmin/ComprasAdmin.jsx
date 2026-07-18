import React, { useEffect, useState } from "react";
import { ShoppingBag, Search, Trash2, Plus } from "lucide-react";

import {
  comprasApi,
  productosApi,
  proveedoresApi,
} from "../../../services/api";
import { SkeletonFilas } from "../../Skeleton/Skeleton";
import "./ComprasAdmin.scss";

const hoyISO = () => new Date().toISOString().slice(0, 10);

export default function ComprasAdmin() {
  const [proveedores, setProveedores] = useState([]);
  const [proveedorId, setProveedorId] = useState("");
  const [numeroFactura, setNumeroFactura] = useState("");
  const [fechaCompra, setFechaCompra] = useState(hoyISO());
  const [actualizarCosto, setActualizarCosto] = useState(true);

  const [textoBusqueda, setTextoBusqueda] = useState("");
  const [resultados, setResultados] = useState([]);
  const [lineas, setLineas] = useState([]);

  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);
  const [resultado, setResultado] = useState(null);

  const [compras, setCompras] = useState([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(true);

  const cargarProveedores = async () => {
    try {
      setProveedores(await proveedoresApi.listar());
    } catch (err) {
      setError(err.message);
    }
  };

  const cargarHistorial = async () => {
    setCargandoHistorial(true);
    try {
      setCompras(await comprasApi.listar());
    } catch (err) {
      setError(err.message);
    } finally {
      setCargandoHistorial(false);
    }
  };

  useEffect(() => {
    cargarProveedores();
    cargarHistorial();
  }, []);

  useEffect(() => {
    if (textoBusqueda.trim().length < 1) {
      setResultados([]);
      return;
    }
    const temporizador = setTimeout(async () => {
      try {
        setResultados(await productosApi.buscar(textoBusqueda.trim()));
      } catch {
        setResultados([]);
      }
    }, 250);
    return () => clearTimeout(temporizador);
  }, [textoBusqueda]);

  const agregarLinea = (producto, variante) => {
    setLineas((prev) => {
      if (prev.some((l) => l.variante_id === variante.id)) return prev;
      return [
        ...prev,
        {
          variante_id: variante.id,
          producto_nombre: producto.nombre,
          color: variante.color,
          grosor: variante.grosor,
          sku: variante.sku,
          cantidad: 1,
          costo_unitario: variante.costo_unitario || 0,
        },
      ];
    });
    setTextoBusqueda("");
    setResultados([]);
  };

  const actualizarLinea = (varianteId, campo, valor) => {
    setLineas((prev) =>
      prev.map((l) =>
        l.variante_id === varianteId
          ? { ...l, [campo]: Number(valor) || 0 }
          : l,
      ),
    );
  };

  const quitarLinea = (varianteId) => {
    setLineas((prev) => prev.filter((l) => l.variante_id !== varianteId));
  };

  const totalCompra = lineas.reduce(
    (s, l) => s + l.cantidad * l.costo_unitario,
    0,
  );

  const registrarCompra = async () => {
    if (!proveedorId || lineas.length === 0) {
      setError("Elige un proveedor y agrega al menos un producto");
      return;
    }
    setGuardando(true);
    setError(null);
    setResultado(null);
    try {
      const compra = await comprasApi.crear({
        proveedor_id: Number(proveedorId),
        numero_factura_proveedor: numeroFactura.trim() || null,
        fecha_compra: fechaCompra,
        actualizar_costo_producto: actualizarCosto,
        lineas: lineas.map((l) => ({
          variante_id: l.variante_id,
          cantidad: l.cantidad,
          costo_unitario: l.costo_unitario,
        })),
      });
      setResultado(compra);
      setLineas([]);
      setNumeroFactura("");
      await cargarHistorial();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="compras-admin">
      <h2 className="compras-admin__titulo">
        <ShoppingBag size={18} strokeWidth={2} />
        Registrar compra
      </h2>
      <p className="compras-admin__ayuda">
        Al registrar una compra, el stock de cada producto sube automáticamente.
      </p>

      {error && <p className="compras-admin__error">{error}</p>}
      {resultado && (
        <p className="compras-admin__exito">
          Compra #{resultado.id} registrada — total{" "}
          <span className="u-cifra">
            ${resultado.total.toLocaleString("es-CO")}
          </span>
        </p>
      )}

      <div className="compras-admin__campos">
        <select
          value={proveedorId}
          onChange={(e) => setProveedorId(e.target.value)}
        >
          <option value="">Elige un proveedor…</option>
          {proveedores.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nombre_comercial}
            </option>
          ))}
        </select>
        <input
          type="text"
          placeholder="N.º factura del proveedor (opcional)"
          value={numeroFactura}
          onChange={(e) => setNumeroFactura(e.target.value)}
        />
        <input
          type="date"
          value={fechaCompra}
          onChange={(e) => setFechaCompra(e.target.value)}
        />
      </div>

      <label className="compras-admin__checkbox">
        <input
          type="checkbox"
          checked={actualizarCosto}
          onChange={(e) => setActualizarCosto(e.target.checked)}
        />
        Actualizar el costo de cada producto al de esta compra
      </label>

      <div className="compras-admin__buscador">
        <Search size={16} strokeWidth={2} />
        <input
          type="text"
          placeholder="Buscar producto para agregar…"
          value={textoBusqueda}
          onChange={(e) => setTextoBusqueda(e.target.value)}
        />
        {resultados.length > 0 && (
          <div className="compras-admin__resultados">
            {resultados.map((producto) => (
              <div
                key={producto.id}
                className="compras-admin__resultado-producto"
              >
                <p>{producto.nombre}</p>
                <div className="compras-admin__resultado-variantes">
                  {producto.variantes.map((v) => (
                    <button
                      key={v.id}
                      type="button"
                      onClick={() => agregarLinea(producto, v)}
                    >
                      {[v.color, v.grosor].filter(Boolean).join(" · ") || v.sku}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {lineas.length > 0 && (
        <table className="compras-admin__lineas">
          <thead>
            <tr>
              <th>Producto</th>
              <th>Cantidad</th>
              <th>Costo unitario</th>
              <th>Subtotal</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {lineas.map((l) => (
              <tr key={l.variante_id}>
                <td>
                  {l.producto_nombre}
                  {l.color ? ` · ${l.color}` : ""}
                </td>
                <td>
                  <input
                    type="number"
                    min="0"
                    value={l.cantidad}
                    onChange={(e) =>
                      actualizarLinea(l.variante_id, "cantidad", e.target.value)
                    }
                  />
                </td>
                <td>
                  <input
                    type="number"
                    min="0"
                    value={l.costo_unitario}
                    onChange={(e) =>
                      actualizarLinea(
                        l.variante_id,
                        "costo_unitario",
                        e.target.value,
                      )
                    }
                  />
                </td>
                <td className="u-cifra">
                  ${(l.cantidad * l.costo_unitario).toLocaleString("es-CO")}
                </td>
                <td>
                  <button
                    type="button"
                    onClick={() => quitarLinea(l.variante_id)}
                  >
                    <Trash2 size={14} strokeWidth={2} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {lineas.length > 0 && (
        <div className="compras-admin__total">
          Total:{" "}
          <span className="u-cifra">
            ${totalCompra.toLocaleString("es-CO")}
          </span>
        </div>
      )}

      <button
        type="button"
        className="compras-admin__registrar"
        disabled={guardando || lineas.length === 0}
        onClick={registrarCompra}
      >
        <Plus size={14} strokeWidth={2} />
        {guardando ? "Registrando…" : "Registrar compra"}
      </button>

      <h3 className="compras-admin__subtitulo">Historial de compras</h3>
      {cargandoHistorial ? (
        <SkeletonFilas filas={3} columnas={5} />
      ) : compras.length === 0 ? (
        <p className="compras-admin__vacio">Aún no hay compras registradas.</p>
      ) : (
        <table className="compras-admin__historial">
          <thead>
            <tr>
              <th>#</th>
              <th>Fecha</th>
              <th>Proveedor</th>
              <th>Total</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {compras.map((c) => {
              const proveedor = proveedores.find(
                (p) => p.id === c.proveedor_id,
              );
              return (
                <tr
                  key={c.id}
                  className={
                    c.estado === "ANULADA" ? "compras-admin__fila--anulada" : ""
                  }
                >
                  <td className="u-cifra">{c.id}</td>
                  <td className="u-cifra">{c.fecha_compra}</td>
                  <td>{proveedor?.nombre_comercial || "—"}</td>
                  <td className="u-cifra">
                    ${c.total.toLocaleString("es-CO")}
                  </td>
                  <td>{c.estado === "ANULADA" ? "Anulada" : "Recibida"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
