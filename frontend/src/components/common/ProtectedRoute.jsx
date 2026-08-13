// src/components/common/ProtectedRoute.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const RUTA_POR_ROL = {
  admin: '/admin/dashboard',
  student: '/student/dashboard',
  teacher: '/teacher/dashboard',
};

const ETIQUETA_ROL = {
  admin: 'administrador',
  student: 'estudiante',
  teacher: 'docente',
};

/**
 * Pantalla completa que explica por qué no se puede ver la ruta pedida.
 *
 * Antes esto redirigia en silencio a /login con <Navigate>: el usuario solo
 * veia el formulario de acceso de nuevo, sin ninguna pista de si le faltaba
 * sesion o si su rol no alcanzaba. Aqui se muestra el codigo de error real
 * (401/403) y el motivo, con un boton para ir a donde corresponda.
 */
const PantallaDeError = ({ status, titulo, mensaje, textoBoton, destino }) => {
  const navigate = useNavigate();
  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', textAlign: 'center',
      padding: 24, gap: 16, backgroundColor: '#fef2f2',
    }}>
      <div style={{ fontSize: 64, fontWeight: 800, color: '#dc2626' }}>
        Error {status}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color: '#1f2937' }}>{titulo}</div>
      <div style={{ fontSize: 16, color: '#4b5563', maxWidth: 480 }}>{mensaje}</div>
      <button
        onClick={() => navigate(destino, { replace: true })}
        style={{
          marginTop: 8, padding: '10px 24px', fontSize: 15, fontWeight: 600,
          color: '#fff', backgroundColor: '#dc2626', border: 'none',
          borderRadius: 8, cursor: 'pointer',
        }}
      >
        {textoBoton}
      </button>
    </div>
  );
};

const ProtectedRoute = ({ children, requiredRole = null }) => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return <div>Cargando...</div>;
  }

  if (!isAuthenticated()) {
    return (
      <PantallaDeError
        status={401}
        titulo="No has iniciado sesión"
        mensaje="Esta sección requiere una cuenta activa. Inicia sesión para continuar."
        textoBoton="Ir a iniciar sesión"
        destino="/login"
      />
    );
  }

  if (requiredRole && user?.role !== requiredRole) {
    const tieneDestinoPropio = user?.role && RUTA_POR_ROL[user.role];
    return (
      <PantallaDeError
        status={403}
        titulo="No tienes permiso para ver esta sección"
        mensaje={
          `Tu cuenta es de ${ETIQUETA_ROL[user?.role] || user?.role || 'rol desconocido'} ` +
          `y esta sección requiere ${ETIQUETA_ROL[requiredRole] || requiredRole}.`
        }
        textoBoton={tieneDestinoPropio ? 'Ir a mi panel' : 'Ir a iniciar sesión'}
        destino={tieneDestinoPropio ? RUTA_POR_ROL[user.role] : '/login'}
      />
    );
  }

  return children;
};

export default ProtectedRoute;

