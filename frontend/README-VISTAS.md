# Vistas del Sistema de Academia

## 📋 Resumen

Se han creado vistas básicas en React para probar el flujo completo del sistema de academia. Las vistas incluyen:

- **Autenticación**: Login y Registro
- **Admin**: Dashboard, Ciclos, Cursos, Docentes, Estudiantes, Matrículas, Pagos, Horarios
- **Estudiante**: Dashboard, Cursos Disponibles, Mis Matrículas
- **Docente**: Dashboard, Mis Estudiantes, Marcar Asistencias

## 🏗️ Estructura

### Servicios
- `src/services/api.js`: Servicio centralizado para todas las peticiones API

### Contextos
- `src/contexts/AuthContext.jsx`: Contexto de autenticación con información del usuario

### Layouts
- `src/components/layouts/AdminLayout.jsx`: Layout para administradores
- `src/components/layouts/StudentLayout.jsx`: Layout para estudiantes
- `src/components/layouts/TeacherLayout.jsx`: Layout para docentes

### Componentes Comunes
- `src/components/common/ProtectedRoute.jsx`: Ruta protegida que verifica autenticación y roles

### Componentes de Autenticación
- `src/components/auth/Login.jsx`: Login de usuarios
- `src/components/auth/Register.jsx`: Registro de estudiantes

### Componentes de Admin
- `src/components/admin/AdminDashboard.jsx`: Dashboard con estadísticas
- `src/components/admin/AdminCycles.jsx`: Gestión de ciclos
- `src/components/admin/AdminCoursesComplete.jsx`: Gestión de cursos y ofertas
- `src/components/admin/AdminPackages.jsx`: Gestión de paquetes
- `src/components/admin/AdminTeachers.jsx`: Gestión de docentes
- `src/components/admin/AdminStudents.jsx`: Gestión de estudiantes
- `src/components/admin/AdminEnrollmentsComplete.jsx`: Gestión de matrículas (aceptar/rechazar)
- `src/components/admin/AdminPaymentsComplete.jsx`: Gestión de pagos
- `src/components/admin/AdminSchedules.jsx`: Gestión de horarios

### Componentes de Estudiante
- `src/components/student/StudentDashboardComplete.jsx`: Dashboard del estudiante
- `src/components/student/StudentAvailableCourses.jsx`: Ver cursos disponibles y matricularse
- `src/components/student/StudentMyEnrollments.jsx`: Ver mis matrículas y cuotas

### Componentes de Docente
- `src/components/teacher/TeacherDashboard.jsx`: Dashboard del docente
- `src/components/teacher/TeacherStudents.jsx`: Ver mis estudiantes
- `src/components/teacher/TeacherAttendance.jsx`: Marcar asistencias

## 🚀 Uso

### Iniciar el servidor de desarrollo

```bash
cd frontend
npm install
npm run dev
```

### Rutas Disponibles

#### Públicas
- `/login`: Login de usuarios
- `/register`: Registro de estudiantes

#### Admin (requiere autenticación como admin)
- `/admin/dashboard`: Dashboard administrativo
- `/admin/cycles`: Gestión de ciclos
- `/admin/courses`: Gestión de cursos y ofertas
- `/admin/packages`: Gestión de paquetes
- `/admin/teachers`: Gestión de docentes
- `/admin/students`: Gestión de estudiantes
- `/admin/enrollments`: Gestión de matrículas
- `/admin/payments`: Gestión de pagos
- `/admin/schedules`: Gestión de horarios

#### Estudiante (requiere autenticación como student)
- `/student/dashboard`: Dashboard del estudiante
- `/student/available-courses`: Ver cursos disponibles y matricularse
- `/student/my-enrollments`: Ver mis matrículas y cuotas

#### Docente (requiere autenticación como teacher)
- `/teacher/dashboard`: Dashboard del docente
- `/teacher/students`: Ver mis estudiantes
- `/teacher/attendance`: Marcar asistencias

## 🔐 Autenticación

El sistema usa JWT tokens almacenados en `localStorage`. El contexto de autenticación (`AuthContext`) maneja:

- Login de usuarios
- Logout
- Verificación de autenticación
- Verificación de roles (admin, student, teacher)
- Redirección según el rol después del login

## 📡 API

Todas las peticiones API se realizan a través del servicio `api.js` que:

- Maneja automáticamente los tokens de autenticación
- Centraliza la URL base de la API
- Proporciona métodos para cada recurso (cursos, estudiantes, matrículas, etc.)

### Configuración

La URL base de la API está definida en `src/services/api.js`:

```javascript
const API_BASE_URL = 'http://localhost:4000/api';
```

Asegúrate de que el backend esté corriendo en `http://localhost:4000`.

## 🎨 Estilos

El proyecto usa Material-UI (MUI) para los componentes de interfaz. El tema se define en `App.jsx` y se puede personalizar según sea necesario.

## 📝 Notas

1. **Protección de Rutas**: Todas las rutas protegidas usan el componente `ProtectedRoute` que verifica la autenticación y el rol del usuario.

2. **Manejo de Errores**: Los componentes muestran mensajes de error cuando las peticiones API fallan.

3. **Loading States**: Los componentes muestran estados de carga mientras se realizan las peticiones.

4. **Responsive**: Los layouts son responsive y se adaptan a diferentes tamaños de pantalla.

5. **Navegación**: Los layouts incluyen menús de navegación con enlaces a las diferentes secciones.

## 🔄 Flujo del Sistema

1. **Admin**:
   - Crear ciclos
   - Agregar cursos y docentes
   - Publicar ofertas
   - Definir horarios
   - Revisar y aceptar matrículas
   - Aprobar pagos

2. **Estudiante**:
   - Registrarse
   - Ver cursos disponibles
   - Matricularse en cursos/paquetes
   - Subir vouchers de pago
   - Ver estado de matrículas y pagos

3. **Docente**:
   - Ver estudiantes asignados
   - Marcar asistencias

## 🐛 Problemas Conocidos

- Algunos componentes pueden necesitar ajustes según la estructura exacta de los datos del backend
- La carga de ofertas de paquetes puede fallar si no hay ofertas disponibles
- Los horarios pueden no cargarse correctamente si no están asociados a ofertas

## 🚧 Mejoras Futuras

- Agregar validación de formularios más robusta
- Implementar paginación en las tablas
- Agregar filtros y búsqueda
- Mejorar el manejo de errores
- Agregar notificaciones en tiempo real
- Implementar carga de imágenes para vouchers
- Agregar gráficos en el dashboard

