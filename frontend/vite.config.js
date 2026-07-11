import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Permite que el POS sea accesible desde otras cajas en la red local
    // de la tienda si algún día se necesita (ej: revisar ventas desde otro PC).
    host: true,
  },
});
