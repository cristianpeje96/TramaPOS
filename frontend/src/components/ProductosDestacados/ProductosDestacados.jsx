import React, { useEffect, useState } from "react";
import { Star, TrendingUp } from "lucide-react";

import { productosApi } from "../../services/api";
import { SkeletonTarjetas } from "../Skeleton/Skeleton";
import "./ProductosDestacados.scss";

/**
 * ProductosDestacados
 * Ocupa el espacio libre debajo de "Venta actual" en el POS. Dos pestañas:
 *  - Favoritos: los que el cajero marcó con la estrella en Administración.
 *  - Más vendidos: top variantes por cantidad vendida en los últimos 30 días
 *    (GET /productos/mas-vendidos), sin que nadie tenga que marcarlos.
 * Un click agrega la variante directo a la venta actual — mismo formato
 * de línea que usa BuscadorProducto, para que PosScreen no necesite
 * distinguir el origen.
 */
export default function ProductosDestacados({ onSeleccionarVariante }) {
  const [pestana, setPestana] = useState("favoritos");
  const [favoritos, setFavoritos] = useState([]);
  const [masVendidos, setMasVendidos] = useState([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    Promise.all([
      productosApi.favoritos(),
      productosApi.masVendidos({ limite: 6 }),
    ])
      .then(([f, m]) => {
        setFavoritos(f);
        setMasVendidos(m);
      })
      .catch(() => {
        setFavoritos([]);
        setMasVendidos([]);
      })
      .finally(() => setCargando(false));
  }, []);

  const lista = pestana === "favoritos" ? favoritos : masVendidos;

  const seleccionar = (item) => {
    onSeleccionarVariante?.({
      variante_id: item.variante_id,
      cantidad: 1,
      precio_unitario: item.precio_venta,
      nombre: item.producto_nombre,
      color: item.color,
      grosor: item.grosor,
      sku: item.sku,
      unidad_medida: item.unidad_medida,
    });
  };

  if (!cargando && favoritos.length === 0 && masVendidos.length === 0) {
    return null; // nada que mostrar todavía (tienda nueva, sin ventas ni favoritos)
  }

  return (
    <div className="productos-destacados">
      <div className="productos-destacados__tabs">
        <button
          type="button"
          className={
            pestana === "favoritos" ? "productos-destacados__tab--activa" : ""
          }
          onClick={() => setPestana("favoritos")}
        >
          <Star size={14} strokeWidth={2} />
          Favoritos
        </button>
        <button
          type="button"
          className={
            pestana === "mas-vendidos"
              ? "productos-destacados__tab--activa"
              : ""
          }
          onClick={() => setPestana("mas-vendidos")}
        >
          <TrendingUp size={14} strokeWidth={2} />
          Más vendidos
        </button>
      </div>

      {cargando ? (
        <SkeletonTarjetas cantidad={6} />
      ) : lista.length === 0 ? (
        <p className="productos-destacados__estado">
          {pestana === "favoritos"
            ? "Aún no marcaste favoritos (Administración → Productos → ⭐)"
            : "Todavía no hay ventas suficientes para calcular esto"}
        </p>
      ) : (
        <div className="productos-destacados__grid">
          {lista.map((item) => (
            <button
              key={item.variante_id}
              type="button"
              className="productos-destacados__item"
              disabled={item.stock_actual <= 0}
              onClick={() => seleccionar(item)}
            >
              <span className="productos-destacados__item-nombre">
                {item.producto_nombre}
              </span>
              {(item.color || item.grosor) && (
                <span className="productos-destacados__item-variante">
                  {[item.color, item.grosor].filter(Boolean).join(" · ")}
                </span>
              )}
              <span className="productos-destacados__item-precio u-cifra">
                ${item.precio_venta.toLocaleString("es-CO")}
              </span>
              {item.stock_actual <= 0 && (
                <span className="productos-destacados__item-agotado">
                  Agotado
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
