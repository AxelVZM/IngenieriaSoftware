// src/services/api.js
// Servicio centralizado para manejar todas las peticiones API

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:4000/api";

// Códigos que significan "la sesión ya no sirve" -> cerrar sesión local
const SESSION_ERROR_CODES = [
  "TOKEN_EXPIRED",
  "TOKEN_INVALID",
  "TOKEN_MISSING",
  "USER_NOT_FOUND",
];

/**
 * Error enriquecido: además del mensaje trae el código del backend
 * y el status HTTP, para que los componentes puedan reaccionar.
 */
export class ApiError extends Error {
  constructor(message, { code = "UNKNOWN_ERROR", status = 0, fields = [] } = {}) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.fields = fields;
  }
}

function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

/**
 * Extrae el mensaje del cuerpo de error, soportando:
 *  - Formato nuevo: { detail: { code, message, fields } }
 *  - Formato antiguo: { detail: "texto" } o { error: "texto" }
 */
function parseErrorBody(body, status) {
  const detail = body?.detail;

  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    return new ApiError(detail.message || "Error en la petición", {
      code: detail.code || "HTTP_ERROR",
      status,
      fields: detail.fields || [],
    });
  }

  const message =
    (typeof detail === "string" && detail) ||
    body?.message ||
    body?.error ||
    "Error en la petición";

  return new ApiError(message, { code: "HTTP_ERROR", status });
}

// Función helper para hacer peticiones
async function request(endpoint, options = {}) {
  const token = localStorage.getItem("token");

  const config = {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  };

  // Si hay FormData, eliminar Content-Type para que el browser lo establezca
  if (options.body instanceof FormData) {
    delete config.headers["Content-Type"];
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  } catch (networkError) {
    // fetch solo falla así cuando no hay red o el servidor no responde
    console.error("Network Error:", networkError);
    throw new ApiError(
      "No se pudo conectar con el servidor. Revisa tu conexión.",
      { code: "NETWORK_ERROR" }
    );
  }

  // 204 No Content u otras respuestas sin cuerpo
  if (response.status === 204) return null;

  let body = null;
  const raw = await response.text();
  if (raw) {
    try {
      body = JSON.parse(raw);
    } catch {
      body = null;
    }
  }

  if (!response.ok) {
    // Si el backend devolvió algo que no es JSON (ej. HTML de un 502)
    if (body === null) {
      throw new ApiError(
        `Error del servidor (${response.status}). Intenta más tarde.`,
        { code: "SERVER_ERROR", status: response.status }
      );
    }

    const error = parseErrorBody(body, response.status);

    // Sesión inválida o expirada: limpiar y mandar al login
    if (response.status === 401 && SESSION_ERROR_CODES.includes(error.code)) {
      clearSession();
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }

    console.error("API Error:", error.code, error.message);
    throw error;
  }

  // Red de seguridad para endpoints aún NO migrados al formato estándar.
  // Algunos responden 200/201 pero con {"error": "..."} en el cuerpo, es decir,
  // un fallo disfrazado de éxito (defecto BG-U1 en create_teacher). Sin esta
  // comprobación la interfaz mostraría "creado correctamente" en un error.
  // Cuando todos los controladores usen api_error(), este bloque sobra.
  if (body && typeof body === "object" && typeof body.error === "string") {
    const legacy = new ApiError(body.error, {
      code: "LEGACY_ERROR",
      status: response.status,
    });
    console.error("API Error (formato antiguo):", body.error);
    throw legacy;
  }

  return body;
}

// API de autenticación
export const authAPI = {
  login: (dni, password) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ dni, password }),
    }),
  register: (data) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// API de estudiantes
export const studentsAPI = {
  // Se apunta a /auth/register para usar las validaciones reforzadas.
  register: (data) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getAll: () => request("/students"),
};

// API de ciclos
export const cyclesAPI = {
  getAll: () => request("/cycles"),
  getActive: () => request("/cycles/active"),
  getOne: (id) => request(`/cycles/${id}`),
  create: (data) =>
    request("/cycles", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id, data) =>
    request(`/cycles/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id) =>
    request(`/cycles/${id}`, {
      method: "DELETE",
    }),
};

// API de cursos
export const coursesAPI = {
  getAll: () => request("/courses"),
  getOne: (id) => request(`/courses/${id}`),
  create: (data) =>
    request("/courses", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id, data) =>
    request(`/courses/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id) =>
    request(`/courses/${id}`, {
      method: "DELETE",
    }),
  getOfferings: () => request("/courses/offerings"),
  createOffering: (data) =>
    request("/courses/offerings", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateOffering: (id, data) =>
    request(`/courses/offerings/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteOffering: (id) =>
    request(`/courses/offerings/${id}`, {
      method: "DELETE",
    }),
};

// API de paquetes
export const packagesAPI = {
  getAll: () => request("/packages"),
  getOne: (id) => request(`/packages/${id}`),
  create: (data) =>
    request("/packages", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id, data) =>
    request(`/packages/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id) =>
    request(`/packages/${id}`, {
      method: "DELETE",
    }),
  addCourse: (packageId, courseId) =>
    request(`/packages/${packageId}/courses`, {
      method: "POST",
      body: JSON.stringify({ course_id: courseId }),
    }),
  removeCourse: (packageId, courseId) =>
    request(`/packages/${packageId}/courses/${courseId}`, {
      method: "DELETE",
    }),
  getOfferings: () => request("/packages/offerings"),
  createOffering: (data) =>
    request("/packages/offerings", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateOffering: (id, data) =>
    request(`/packages/offerings/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteOffering: (id) =>
    request(`/packages/offerings/${id}`, {
      method: "DELETE",
    }),
  // Mapping: package_offering -> course_offerings
  addOfferingCourse: (packageOfferingId, courseOfferingId) =>
    request(`/packages/offerings/${packageOfferingId}/courses`, {
      method: "POST",
      body: JSON.stringify({ course_offering_id: courseOfferingId }),
    }),
  removeOfferingCourse: (packageOfferingId, courseOfferingId) =>
    request(
      `/packages/offerings/${packageOfferingId}/courses/${courseOfferingId}`,
      {
        method: "DELETE",
      }
    ),
  getOfferingCourses: (packageOfferingId) =>
    request(`/packages/offerings/${packageOfferingId}/courses`),
};

// API de docentes
export const teachersAPI = {
  getAll: () => request("/teachers"),
  getOne: (id) => request(`/teachers/${id}`),
  create: (data) =>
    request("/teachers", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id, data) =>
    request(`/teachers/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id) =>
    request(`/teachers/${id}`, {
      method: "DELETE",
    }),
  resetPassword: (id) =>
    request(`/teachers/${id}/reset-password`, {
      method: "POST",
    }),
  getStudents: (id) => request(`/teachers/${id}/students`),
  getStudentsByCourse: (teacherId, courseOfferingId) =>
    request(`/teachers/${teacherId}/students/course/${courseOfferingId}`),
  markAttendance: (teacherId, data) =>
    request(`/teachers/${teacherId}/attendance`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getAttendance: (teacherId, scheduleId, date) =>
    request(`/teachers/${teacherId}/attendance/${scheduleId}/${date}`),
};

// API de matrículas
export const enrollmentsAPI = {
  getAll: (studentId = null) => {
    const url = studentId
      ? `/enrollments?student_id=${studentId}`
      : "/enrollments";
    return request(url);
  },
  getAllAdmin: () => request("/enrollments/admin"),
  create: (items) =>
    request("/enrollments", {
      method: "POST",
      body: JSON.stringify({ items }),
    }),
  updateStatus: (enrollmentId, status) =>
    request("/enrollments/status", {
      method: "PUT",
      body: JSON.stringify({ enrollment_id: enrollmentId, status }),
    }),
  cancel: (enrollmentId) =>
    request("/enrollments/cancel", {
      method: "POST",
      body: JSON.stringify({ enrollment_id: enrollmentId }),
    }),
  getByOffering: (type, id, status = "aceptado") => {
    const params = new URLSearchParams({ type, id, status });
    return request(`/enrollments/by-offering?${params.toString()}`);
  },
};

// API de pagos
export const paymentsAPI = {
  getAll: (status = null) => {
    const url = status ? `/payments?status=${status}` : "/payments";
    return request(url);
  },
  uploadVoucher: (installmentId, file) => {
    const formData = new FormData();
    formData.append("voucher", file);
    formData.append("installment_id", installmentId);
    return request("/payments/upload", {
      method: "POST",
      body: formData,
    });
  },
  approveInstallment: (installmentId) =>
    request("/payments/approve", {
      method: "POST",
      body: JSON.stringify({ installment_id: installmentId }),
    }),
  rejectInstallment: (installmentId, reason = null) =>
    request("/payments/reject", {
      method: "POST",
      body: JSON.stringify({ installment_id: installmentId, reason }),
    }),
};

// API de horarios
export const schedulesAPI = {
  getAll: () => request("/schedules"),
  // Alias for backward compatibility with AdminSchedules component
  getByOffering: (courseOfferingId) =>
    request(`/schedules/offering/${courseOfferingId}`),
  getByCourseOffering: (courseOfferingId) =>
    request(`/schedules/offering/${courseOfferingId}`),
  getByPackageOffering: (packageOfferingId) =>
    request(`/schedules/package-offering/${packageOfferingId}`),
  create: (data) =>
    request("/schedules", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id, data) =>
    request(`/schedules/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id) =>
    request(`/schedules/${id}`, {
      method: "DELETE",
    }),
};

// API de admin
export const adminAPI = {
  getDashboard: () => request("/admin/dashboard"),
  getAnalytics: (cycleId = null, studentId = null) => {
    const params = new URLSearchParams();
    if (cycleId) params.append("cycle_id", cycleId);
    if (studentId) params.append("student_id", studentId);
    const url = `/admin/analytics${
      params.toString() ? "?" + params.toString() : ""
    }`;
    return request(url);
  },
  getNotifications: (studentId = null, type = null, limit = 50) => {
    const params = new URLSearchParams();
    if (studentId) params.append("student_id", studentId);
    if (type) params.append("type", type);
    params.append("limit", limit);
    return request(`/admin/notifications?${params.toString()}`);
  },
  getAttendanceNotifications: (cycleId, date, group) => {
    const params = new URLSearchParams({
      cycle_id: cycleId,
      date: date,
      group: group,
    });
    return request(`/admin/attendance-notifications?${params.toString()}`);
  },
  sendAttendanceNotifications: (cycleId, date, groupLabel) =>
    request("/admin/send-attendance-notifications", {
      method: "POST",
      body: JSON.stringify({
        cycle_id: cycleId,
        date: date,
        group_label: groupLabel,
      }),
    }),
};

// API de notificaciones
export const notificationsAPI = {
  // WhatsApp session
  initWhatsApp: () =>
    request("/notifications/whatsapp/init", { method: "POST" }),
  verifyWhatsApp: () =>
    request("/notifications/whatsapp/verify", { method: "POST" }),
  testWhatsApp: (phone = "969728039") =>
    request(`/notifications/whatsapp/test?phone=${phone}`, { method: "POST" }),
  closeWhatsApp: () =>
    request("/notifications/whatsapp/close", { method: "POST" }),

  // Payment notifications
  getPaymentsRejected: () => request("/notifications/payments/rejected"),
  getPaymentsAccepted: () => request("/notifications/payments/accepted"),
  sendPaymentNotifications: (type, payments) =>
    request("/notifications/payments/send", {
      method: "POST",
      body: JSON.stringify({ type, payments }),
    }),
};

export default {
  authAPI,
  studentsAPI,
  cyclesAPI,
  coursesAPI,
  packagesAPI,
  teachersAPI,
  enrollmentsAPI,
  paymentsAPI,
  schedulesAPI,
  adminAPI,
  notificationsAPI,
};