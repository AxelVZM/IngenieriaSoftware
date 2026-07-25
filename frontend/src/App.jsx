// src/App.jsx
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { createTheme } from '@mui/material/styles';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import ScrollToTop from './components/common/ScrollToTop';

// Landing
// Landing
import LandingPage from './components/landing/LandingPage';
import {
  AboutPage,
  CoursesPage,
  TeachersPage,
  TestimonialsPage,
  TermsPage,
  PrivacyPage,
  CookiesPage
} from './components/landing/InfoPages';

// Auth
import Login from './components/auth/Login';
import Register from './components/auth/Register';

// Layouts
import AdminLayout from './components/layouts/AdminLayout';
import StudentLayout from './components/layouts/StudentLayout';
import TeacherLayout from './components/layouts/TeacherLayout';

// Admin Components
import AdminDashboard from './components/admin/AdminDashboard';
import AdminCycles from './components/admin/AdminCycles';
import AdminCoursesComplete from './components/admin/AdminCoursesComplete';
import AdminPackages from './components/admin/AdminPackages';
import AdminTeachers from './components/admin/AdminTeachers';
import AdminUsers from './components/admin/AdminUsers';
import AdminStudents from './components/admin/AdminStudents';
import AdminEnrollmentsComplete from './components/admin/AdminEnrollmentsComplete';
import AdminPaymentsComplete from './components/admin/AdminPaymentsComplete';
import AdminSchedules from './components/admin/AdminSchedules';
import AdminNotifications from './components/admin/AdminNotifications';

// Student Components
import StudentDashboardComplete from './components/student/StudentDashboardComplete';
import StudentAvailableCourses from './components/student/StudentAvailableCourses';
import StudentMyEnrollments from './components/student/StudentMyEnrollments';
import MyCourses from './components/student/MyCourses';

// Teacher Components
import TeacherDashboard from './components/teacher/TeacherDashboard';
import TeacherStudents from './components/teacher/TeacherStudents';
import TeacherAttendance from './components/teacher/TeacherAttendance';

import './App.css';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <ScrollToTop />
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Admin Routes */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AdminLayout />
                </ProtectedRoute>
              }
            >
              <Route path="dashboard" element={<AdminDashboard />} />
              <Route path="cycles" element={<AdminCycles />} />
              <Route path="courses" element={<AdminCoursesComplete />} />
              <Route path="packages" element={<AdminPackages />} />
              <Route path="teachers" element={<AdminTeachers />} />
              <Route path="users" element={<AdminUsers />} />
              <Route path="students" element={<AdminStudents />} />
              <Route path="enrollments" element={<AdminEnrollmentsComplete />} />
              <Route path="payments" element={<AdminPaymentsComplete />} />
              <Route path="schedules" element={<AdminSchedules />} />
              <Route path="notifications" element={<AdminNotifications />} />
            </Route>

            {/* Student Routes */}
            <Route
              path="/student"
              element={
                <ProtectedRoute requiredRole="student">
                  <StudentLayout />
                </ProtectedRoute>
              }
            >
              <Route path="dashboard" element={<StudentDashboardComplete />} />
              <Route path="available-courses" element={<StudentAvailableCourses />} />
              <Route path="my-enrollments" element={<StudentMyEnrollments />} />
              <Route path="my-courses" element={<MyCourses />} />
            </Route>

            {/* Teacher Routes */}
            <Route
              path="/teacher"
              element={
                <ProtectedRoute requiredRole="teacher">
                  <TeacherLayout />
                </ProtectedRoute>
              }
            >
              <Route path="dashboard" element={<TeacherDashboard />} />
              <Route path="students" element={<TeacherStudents />} />
              <Route path="attendance" element={<TeacherAttendance />} />
            </Route>

            {/* Info Pages */}
            <Route path="/acerca-de" element={<AboutPage />} />
            <Route path="/nuestros-cursos" element={<CoursesPage />} />
            <Route path="/docentes" element={<TeachersPage />} />
            <Route path="/testimonios" element={<TestimonialsPage />} />
            <Route path="/terminos-y-condiciones" element={<TermsPage />} />
            <Route path="/politica-de-privacidad" element={<PrivacyPage />} />
            <Route path="/politica-de-cookies" element={<CookiesPage />} />

            {/* Landing Page */}
            <Route path="/" element={<LandingPage />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
