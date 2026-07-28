// src/components/auth/Login.jsx
import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useFormik } from "formik";
import * as yup from "yup";
import { useAuth } from "../../contexts/AuthContext";
import "./Auth.css";

// Nombre oficial de la institución. Se usa una sola constante para evitar
// variantes del nombre en distintas pantallas (defecto SEM-05).
const NOMBRE_ACADEMIA = "Academia Unión de Nuevos Inteligentes";

// Mensaje único para credenciales inválidas. Debe coincidir con el del backend
// (defecto SEM-07) y mantenerse genérico a propósito: un texto que distinga si
// el DNI existe permitiría enumerar las cuentas de la academia (defecto BG-A5).
const MSG_CREDENCIALES = "DNI o contraseña incorrectos. Inténtalo de nuevo.";

const LETRAS = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]+$/;

// Esquemas de validación. Redacción homogénea y alineada con el backend
// (defectos SIN-04, SIN-05, SIN-07 y SEM-04).
const loginSchema = yup.object({
  dni: yup.string().trim().required("El DNI es requerido"),
  password: yup.string().required("La contraseña es requerida"),
});

const registerSchema = yup.object({
  dni: yup
    .string()
    .trim()
    .matches(/^\d{8}$/, "El DNI debe tener exactamente 8 dígitos")
    .required("El DNI es requerido"),
  first_name: yup
    .string()
    .trim()
    .min(2, "Los nombres deben tener al menos 2 caracteres")
    .matches(LETRAS, "Los nombres solo pueden contener letras")
    .required("Los nombres son requeridos"),
  last_name: yup
    .string()
    .trim()
    .min(2, "Los apellidos deben tener al menos 2 caracteres")
    .matches(LETRAS, "Los apellidos solo pueden contener letras")
    .required("Los apellidos son requeridos"),
  phone: yup
    .string()
    .trim()
    .matches(/^9\d{8}$/, "El teléfono debe tener 9 dígitos y empezar con 9")
    .required("El teléfono es requerido"),
  parent_name: yup
    .string()
    .trim()
    .min(2, "El nombre del apoderado debe tener al menos 2 caracteres")
    .matches(LETRAS, "El nombre del apoderado solo puede contener letras")
    .required("El nombre del apoderado es requerido"),
  parent_phone: yup
    .string()
    .trim()
    .matches(/^9\d{8}$/, "El teléfono debe tener 9 dígitos y empezar con 9")
    .required("El teléfono del apoderado es requerido"),
  password: yup
    .string()
    .min(8, "La contraseña debe tener al menos 8 caracteres")
    .max(72, "La contraseña no puede superar los 72 caracteres")
    .matches(/[A-Za-z]/, "La contraseña debe incluir al menos una letra")
    .matches(/\d/, "La contraseña debe incluir al menos un número")
    .required("La contraseña es requerida"),
});

// Etiquetas legibles de cada campo, para nombrarlos en el resumen de errores.
const ETIQUETAS = {
  dni: "DNI",
  password: "Contraseña",
  first_name: "Nombres",
  last_name: "Apellidos",
  phone: "Teléfono",
  parent_name: "Nombre del apoderado",
  parent_phone: "Teléfono del apoderado",
};

/**
 * Campo de formulario.
 *
 * No lleva texto de ayuda debajo: al tenerlo unos campos sí y otros no, la
 * rejilla de dos columnas quedaba descuadrada. Los requisitos de formato se
 * indican una sola vez encima del formulario y los fallos se agrupan en un
 * resumen junto al botón (defecto SEM-07). Aquí el campo solo se marca en rojo.
 */
const Campo = ({ formik, name, placeholder, type = "text", fullWidth = false }) => {
  const hayError = Boolean(
    (formik.touched[name] || formik.submitCount > 0) && formik.errors[name]
  );

  return (
    <div style={fullWidth ? { gridColumn: "1 / -1" } : undefined}>
      <input
        type={type}
        placeholder={placeholder}
        name={name}
        aria-invalid={hayError || undefined}
        {...formik.getFieldProps(name)}
        className={hayError ? "input-error" : ""}
      />
    </div>
  );
};

/**
 * Devuelve la lista de errores visibles, en el orden de los campos del
 * formulario, para que el resumen sea predecible.
 */
const erroresVisibles = (formik) =>
  Object.keys(ETIQUETAS)
    .filter(
      (name) =>
        formik.errors[name] && (formik.touched[name] || formik.submitCount > 0)
    )
    .map((name) => ({
      name,
      etiqueta: ETIQUETAS[name],
      mensaje: formik.errors[name],
    }));

/** Cuántos errores se listan como máximo, para que el bloque no crezca y
 *  descoloque la tarjeta. El resto se resume en un contador. */
const MAX_ERRORES_LISTADOS = 3;

/** Resumen de errores. Solo se dibuja si hay alguno. */
const ResumenErrores = ({ errores }) => {
  if (!errores.length) return null;

  const visibles = errores.slice(0, MAX_ERRORES_LISTADOS);
  const restantes = errores.length - visibles.length;

  // Con un solo fallo no hace falta título ni viñeta: cabe en una línea.
  if (errores.length === 1) {
    const e = errores[0];
    return (
      <div className="error-summary" role="alert">
        <span className="error-summary-single">
          <strong>{e.etiqueta}:</strong> {e.mensaje}
        </span>
      </div>
    );
  }

  return (
    <div className="error-summary" role="alert">
      <p className="error-summary-title">Revisa {errores.length} campos:</p>
      <ul>
        {visibles.map((e) => (
          <li key={e.name}>
            <strong>{e.etiqueta}:</strong> {e.mensaje}
          </li>
        ))}
      </ul>
      {restantes > 0 && (
        <p className="error-summary-more">
          y {restantes} campo{restantes > 1 ? "s" : ""} más por revisar
        </p>
      )}
    </div>
  );
};

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [isActive, setIsActive] = useState(false); // Toggle entre Login/Register
  const [showRules, setShowRules] = useState(false); // Modal de normas
  const [notification, setNotification] = useState(null); // Notificaciones
  const [datosPendientes, setDatosPendientes] = useState(null); // Registro en espera
  const [enviando, setEnviando] = useState(false);

  // Función para mostrar notificaciones temporales
  const showNotification = (type, title, message) => {
    setNotification({ type, title, message });
    setTimeout(() => {
      setNotification(null);
    }, 4000);
  };

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get("mode") === "register") {
      setIsActive(true);
    }
  }, [location]);

  // Formulario de Login
  const loginFormik = useFormik({
    initialValues: { dni: "", password: "" },
    validationSchema: loginSchema,
    onSubmit: async (values) => {
      try {
        const data = await login(values.dni, values.password);
        showNotification("success", "¡Bienvenido!", "Iniciando sesión…");

        // Pequeño delay para ver la animación antes de redirigir
        setTimeout(() => {
          const role = data.user.role;
          if (role === "admin") navigate("/admin/dashboard");
          else if (role === "student") navigate("/student/dashboard");
          else if (role === "teacher") navigate("/teacher/dashboard");
        }, 1000);
      } catch (err) {
        // El backend bloquea temporalmente tras varios intentos fallidos
        const titulo =
          err.code === "TOO_MANY_ATTEMPTS"
            ? "Cuenta bloqueada temporalmente"
            : "Error de acceso";

        showNotification("error", titulo, err.message || MSG_CREDENCIALES);
      }
    },
  });

  // Formulario de Registro.
  // El envío NO crea la cuenta: guarda los datos y muestra los términos. La
  // cuenta se crea solo si el usuario los acepta, de modo que el consentimiento
  // sea previo al tratamiento de sus datos (defecto SEM-03, Ley N.º 29733).
  const registerFormik = useFormik({
    initialValues: {
      dni: "",
      first_name: "",
      last_name: "",
      phone: "",
      parent_name: "",
      parent_phone: "",
      password: "",
    },
    validationSchema: registerSchema,
    onSubmit: (values) => {
      setDatosPendientes(values);
      setShowRules(true);
    },
  });

  // El usuario acepta los términos: recién aquí se crea la cuenta.
  const handleAcceptRules = async () => {
    if (!datosPendientes || enviando) return;
    setEnviando(true);
    try {
      const { studentsAPI } = await import("../../services/api");
      await studentsAPI.register(datosPendientes);

      setShowRules(false);
      setDatosPendientes(null);
      registerFormik.resetForm();
      setIsActive(false); // Cambiar a panel de Login
      showNotification(
        "success",
        "¡Registro exitoso!",
        "Ahora puedes iniciar sesión"
      );
    } catch (err) {
      setShowRules(false);
      showNotification(
        "error",
        err.code === "DNI_ALREADY_REGISTERED"
          ? "DNI ya registrado"
          : "Error de registro",
        err.message || "No se pudo crear la cuenta"
      );
    } finally {
      setEnviando(false);
    }
  };

  // El usuario rechaza los términos: no se crea ninguna cuenta.
  const handleRejectRules = () => {
    setShowRules(false);
    setDatosPendientes(null);
    showNotification(
      "error",
      "Registro cancelado",
      "Para crear tu cuenta es necesario aceptar los términos"
    );
  };

  return (
    <div className="auth-page">
      <a href="/" className="back-to-home">
        ← Volver al inicio
      </a>

      {/* Componente de Notificación Flotante */}
      {notification && (
        <div className="notification-container">
          <div className={`notification-card ${notification.type}`}>
            <div className="notification-icon">
              {notification.type === "success" ? "✅" : "⛔"}
            </div>
            <div className="notification-content">
              <h4>{notification.title}</h4>
              <p>{notification.message}</p>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Normas Institucionales */}
      {showRules && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>⚖️ Términos y Protección de Datos</h2>
            </div>
            <div className="modal-body">
              <p>
                ¡Bienvenido a la {NOMBRE_ACADEMIA}! Antes de crear tu cuenta,
                necesitamos que leas y aceptes lo siguiente. Tu cuenta se creará
                únicamente si aceptas estos términos.
              </p>

              <h3>1. Normas de convivencia</h3>
              <ul>
                <li>
                  <strong>Asistencia:</strong> la academia establece una
                  tolerancia de ingreso de 10 minutos. Las inasistencias se
                  reportan a tu apoderado. (Norma institucional; el control
                  horario lo realiza el docente en aula.)
                </li>
                <li>
                  <strong>Respeto:</strong> mantenemos un ambiente de respeto
                  mutuo entre estudiantes y docentes.
                </li>
                <li>
                  <strong>Compromiso:</strong> debes cumplir con las
                  evaluaciones y mantener el orden en las instalaciones.
                </li>
              </ul>

              <h3>2. Protección de datos (Ley N.º 29733)</h3>
              <ul>
                <li>
                  <strong>Privacidad:</strong> tus datos personales (DNI,
                  nombres, apellidos y teléfonos) se tratan de forma
                  confidencial y no se venden ni se ceden con fines
                  comerciales.
                </li>
                <li>
                  <strong>Encargados del tratamiento:</strong> para funcionar,
                  el sistema procesa tus datos a través de dos proveedores de
                  servicio: WhatsApp, para enviar las notificaciones, y
                  Cloudinary, para almacenar los comprobantes de pago que subas.
                </li>
                <li>
                  <strong>Uso:</strong> tus datos se utilizan exclusivamente
                  para la gestión académica, el control de asistencia y el
                  seguimiento de pagos.
                </li>
                <li>
                  <strong>Consentimiento:</strong> al aceptar, autorizas el
                  envío de notificaciones sobre asistencia y pagos al número de
                  WhatsApp del apoderado que registraste.
                </li>
                <li>
                  <strong>Tus derechos:</strong> puedes solicitar el acceso, la
                  rectificación o la supresión de tus datos dirigiéndote a la
                  administración de la academia.
                </li>
              </ul>
            </div>
            <div className="modal-footer">
              <button
                className="btn-cancel"
                onClick={handleRejectRules}
                disabled={enviando}
              >
                No acepto
              </button>
              <button
                className="btn-accept"
                onClick={handleAcceptRules}
                disabled={enviando}
              >
                {enviando ? "Creando cuenta…" : "He leído y acepto los términos"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className={`auth-container ${isActive ? "active" : ""}`}>
        {/* Sign In Form */}
        <div className="form-container sign-in">
          <form onSubmit={loginFormik.handleSubmit}>
            <h1>Iniciar sesión</h1>
            <Campo
              formik={loginFormik}
              name="dni"
              placeholder="DNI o usuario"
              fullWidth
            />

            <Campo
              formik={loginFormik}
              name="password"
              type="password"
              placeholder="Contraseña"
              fullWidth
            />

            {/* Resumen de fallos, justo antes del botón */}
            <ResumenErrores errores={erroresVisibles(loginFormik)} />

            {/* El DNI es también el usuario de acceso, y no hay recuperación
                de contraseña: ambas cosas deben decirse (defecto SEM-08). */}
            <p className="field-note">
              Los estudiantes ingresan con su DNI; docentes y administración,
              con el usuario que les asignó la academia. Si olvidaste tu
              contraseña, solicita una nueva en administración: el sistema no
              permite restablecerla por tu cuenta.
            </p>

            <button type="submit">Iniciar sesión</button>

            {/* OPCIÓN: NO TENGO CUENTA */}
            <div className="switch-text-container">
              <p>¿No tienes una cuenta?</p>
              <span className="switch-link" onClick={() => setIsActive(true)}>
                Regístrate aquí
              </span>
            </div>
          </form>
        </div>

        {/* Sign Up Form */}
        <div className="form-container sign-up">
          <form onSubmit={registerFormik.handleSubmit}>
            <h1>Crear cuenta de estudiante</h1>

            {/* El DNI es además el usuario de acceso, así que se aclara aquí.
                El formato del resto de campos va en su marcador de posición y,
                si el envío falla, en el resumen de errores (SEM-07). */}
            <p className="form-requisitos">
              DNI de 8 dígitos (será tu usuario)
            </p>

            <div className="form-grid">
              <Campo formik={registerFormik} name="dni" placeholder="DNI" />

              <Campo
                formik={registerFormik}
                name="password"
                type="password"
                placeholder="Contraseña (mín. 8)"
              />

              <Campo
                formik={registerFormik}
                name="first_name"
                placeholder="Nombres"
              />

              <Campo
                formik={registerFormik}
                name="last_name"
                placeholder="Apellidos"
              />

              <Campo
                formik={registerFormik}
                name="phone"
                placeholder="Teléfono (9 dígitos)"
              />

              <Campo
                formik={registerFormik}
                name="parent_name"
                placeholder="Nombre del apoderado"
              />

              <Campo
                formik={registerFormik}
                name="parent_phone"
                placeholder="Teléfono del apoderado (9 dígitos)"
                fullWidth
              />
            </div>

            {/* Resumen de fallos, justo antes del botón. Solo aparece si hay
                errores, y nombra cada campo con su regla concreta (SEM-07). */}
            <ResumenErrores errores={erroresVisibles(registerFormik)} />

            <button type="submit">Continuar</button>

            {/* OPCIÓN: YA TENGO CUENTA */}
            <div className="switch-text-container">
              <p>¿Ya tienes una cuenta?</p>
              <span className="switch-link" onClick={() => setIsActive(false)}>
                Inicia sesión
              </span>
            </div>
          </form>
        </div>

        {/* Toggle Container */}
        <div className="toggle-container">
          <div className="toggle">
            <div className="toggle-panel toggle-left">
              <h1>¡Bienvenido de nuevo!</h1>
              <p>
                Estudiantes, docentes y personal administrativo ingresan por
                aquí con sus credenciales.
              </p>
              <button className="hidden" onClick={() => setIsActive(false)}>
                Iniciar sesión
              </button>
            </div>
            <div className="toggle-panel toggle-right">
              <h1>¿Eres estudiante nuevo?</h1>
              <p>
                Regístrate con tus datos personales para matricularte en los
                cursos de la {NOMBRE_ACADEMIA}. Los docentes y el personal
                administrativo reciben sus credenciales de la administración.
              </p>
              <button className="hidden" onClick={() => setIsActive(true)}>
                Registrarse
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;