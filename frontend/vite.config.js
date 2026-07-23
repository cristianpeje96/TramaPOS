import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Permite que el POS sea accesible desde otras cajas en la red local
    // de la tienda si algún día se necesita (ej: revisar ventas desde otro PC).
    host: true,
    // En producción el backend sirve el frontend ya compilado (mismo origen,
    // por eso api.js usa una ruta relativa '/api/v1'). En desarrollo
    // (npm run dev, puerto aparte) hace falta este proxy para que esa
    // misma ruta relativa llegue al backend real en el puerto 8000.
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});