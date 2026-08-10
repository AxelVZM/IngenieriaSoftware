// src/components/auth/Register.jsx
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

/**
 * Ruta /register.
 *
 * El registro no tiene pantalla propia: vive dentro de Login.jsx como uno de
 * los dos paneles alternables. Este componente solo redirige, pero la forma de
 * hacerlo importa por dos motivos de navegación:
 *
 *  1. Se añade ?mode=register. Sin ese parámetro, Login.jsx abre el panel de
 *     ACCESO, de modo que quien pulsaba un enlace a /register aterrizaba en la
 *     pantalla equivocada (defecto NAV-02).
 *
 *  2. Se usa { replace: true }. Sin él, /register queda en el historial: al
 *     pulsar Atrás el navegador vuelve a /register, que redirige otra vez a
 *     /login, y el usuario no puede retroceder nunca (defecto NAV-03).
 */
const Register = () => {
  const navigate = useNavigate();

  useEffect(() => {
    navigate("/login?mode=register", { replace: true });
  }, [navigate]);

  return null;
};

export default Register;