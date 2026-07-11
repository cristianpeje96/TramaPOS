import React from "react";
import "./Skeleton.scss";

/**
 * Skeleton
 * Placeholder gris con animación de "shimmer", reutilizable en toda la
 * app en vez de que cada pantalla tenga su propio texto "Cargando…".
 *
 * Uso:
 *   <Skeleton width="60%" height={16} />                    // una línea
 *   <SkeletonFilas filas={4} columnas={5} />                 // tabla completa
 *   <SkeletonTarjetas cantidad={3} />                        // tarjetas tipo grid
 */
export function Skeleton({
  width = "100%",
  height = 14,
  radius = 6,
  style = {},
}) {
  return (
    <span
      className="skeleton"
      style={{ width, height, borderRadius: radius, ...style }}
      aria-hidden="true"
    />
  );
}

export function SkeletonFilas({ filas = 4, columnas = 4 }) {
  return (
    <div className="skeleton-filas">
      {Array.from({ length: filas }).map((_, f) => (
        <div key={f} className="skeleton-filas__fila">
          {Array.from({ length: columnas }).map((_, c) => (
            <Skeleton key={c} width={c === 0 ? "80%" : "60%"} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonTarjetas({ cantidad = 3 }) {
  return (
    <div className="skeleton-tarjetas">
      {Array.from({ length: cantidad }).map((_, i) => (
        <div key={i} className="skeleton-tarjetas__item">
          <Skeleton width="70%" height={12} />
          <Skeleton width="45%" height={10} />
          <Skeleton width="35%" height={14} />
        </div>
      ))}
    </div>
  );
}
