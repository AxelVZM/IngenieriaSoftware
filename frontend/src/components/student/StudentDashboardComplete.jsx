// src/components/student/StudentDashboardComplete.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  CircularProgress,
  IconButton,
  Avatar
} from '@mui/material';
import {
  School as SchoolIcon,
  Book as BookIcon,
  Payment as PaymentIcon,
  ArrowForward as ArrowIcon,
  TrendingUp as TrendingUpIcon,
  EventNote as EventIcon,
  AccessTime as TimeIcon
} from '@mui/icons-material';
import { enrollmentsAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import './student-dashboard.css';

const StudentDashboardComplete = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fecha actual para el saludo
  const today = new Date().toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

  useEffect(() => {
    if (user) {
      loadEnrollments();
    }
  }, [user]);

  const loadEnrollments = async () => {
    try {
      setLoading(true);
      const data = await enrollmentsAPI.getAll();
      setEnrollments(data);
    } catch (err) {
      console.error('Error cargando matrículas:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box className="student-loading">
        <CircularProgress className="student-loading-spinner" />
      </Box>
    );
  }

  // Filtros de lógica de negocio
  const visibleEnrollments = enrollments.filter((e) => {
    if (e.status === 'cancelado') return false;
    if (e.enrollment_type === 'course' && e.package_offering_id) return false;
    return true;
  });

  const stats = {
    total: visibleEnrollments.length,
    accepted: visibleEnrollments.filter(e => e.status === 'aceptado').length,
    pending: visibleEnrollments.filter(e => e.status === 'pendiente').length,
  };

  return (
    <Box className="student-content fade-in">
      
      {/* 1. BANNER DE BIENVENIDA */}
      <Box className="student-welcome-card">
        <Box>
            <Typography variant="subtitle2" className="welcome-date">
                {today}
            </Typography>
            <Typography variant="h4" className="welcome-title">
                ¡Hola de nuevo, {user?.first_name || 'Estudiante'}! 👋
            </Typography>
            <Typography variant="body1" className="welcome-subtitle">
                Tienes {stats.pending > 0 ? `${stats.pending} pagos pendientes` : 'todo al día'} en tu actividad académica.
            </Typography>
        </Box>
        <Box className="welcome-icon-container">
            <SchoolIcon sx={{ fontSize: 80, opacity: 0.2, color: 'white' }} />
        </Box>
      </Box>

      {/* 2. ESTADÍSTICAS (KPIs) */}
      <Grid container spacing={3} sx={{ mb: 4, mt: -4 }}>
        <Grid item xs={12} sm={4}>
          <Card className="student-stat-card primary">
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="overline" sx={{ opacity: 0.8 }}>Total Cursos</Typography>
                  <Typography variant="h3" sx={{ fontWeight: 'bold' }}>{stats.total}</Typography>
                </Box>
                <Avatar className="stat-icon-bg primary">
                  <BookIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card className="student-stat-card success">
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="overline" sx={{ opacity: 0.8 }}>Activos</Typography>
                  <Typography variant="h3" sx={{ fontWeight: 'bold' }}>{stats.accepted}</Typography>
                </Box>
                <Avatar className="stat-icon-bg success">
                  <TrendingUpIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card className="student-stat-card warning">
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="overline" sx={{ opacity: 0.8 }}>Pendientes</Typography>
                  <Typography variant="h3" sx={{ fontWeight: 'bold' }}>{stats.pending}</Typography>
                </Box>
                <Avatar className="stat-icon-bg warning">
                  <AccessTimeIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 3. GRID PRINCIPAL: ACCIONES Y LISTA */}
      <Grid container spacing={4}>
        
        {/* COLUMNA IZQUIERDA: ACCIONES */}
        <Grid item xs={12} md={4}>
            <Typography variant="h6" className="section-header" gutterBottom>
                Acciones Rápidas
            </Typography>
            
            <Card className="action-card" onClick={() => navigate('/student/available-courses')}>
                <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>Explorar Cursos</Typography>
                        <Typography variant="body2" color="text.secondary">Ver catálogo y matricularme</Typography>
                    </Box>
                    <IconButton className="action-button">
                        <ArrowIcon />
                    </IconButton>
                </CardContent>
            </Card>

            <Card className="action-card mt-2" onClick={() => navigate('/student/my-enrollments')}>
                <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>Mis Pagos</Typography>
                        <Typography variant="body2" color="text.secondary">Subir vouchers y revisar estado</Typography>
                    </Box>
                    <IconButton className="action-button">
                        <PaymentIcon />
                    </IconButton>
                </CardContent>
            </Card>
        </Grid>

        {/* COLUMNA DERECHA: MATRÍCULAS RECIENTES */}
        <Grid item xs={12} md={8}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" className="section-header">
                    Mis Cursos Recientes
                </Typography>
                <Button size="small" onClick={() => navigate('/student/my-enrollments')}>
                    Ver todos
                </Button>
            </Box>

            {visibleEnrollments.length > 0 ? (
                <Grid container spacing={2}>
                    {visibleEnrollments.slice(0, 3).map((enrollment) => (
                        <Grid item xs={12} key={enrollment.id}>
                            <Card className="student-card horizontal-card">
                                <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 2, '&:last-child': { pb: 2 } }}>
                                    <Avatar variant="rounded" sx={{ bgcolor: enrollment.enrollment_type === 'course' ? '#e0f2fe' : '#f3e8ff', color: enrollment.enrollment_type === 'course' ? '#0284c7' : '#9333ea', width: 56, height: 56 }}>
                                        {enrollment.enrollment_type === 'course' ? <BookIcon /> : <SchoolIcon />}
                                    </Avatar>
                                    
                                    <Box sx={{ flexGrow: 1 }}>
                                        <Typography variant="subtitle1" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
                                            {enrollment.item_name}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary" display="flex" alignItems="center" gap={0.5} mt={0.5}>
                                            <EventIcon sx={{ fontSize: 14 }} /> 
                                            {enrollment.cycle_name || 'Ciclo General'}
                                        </Typography>
                                    </Box>

                                    <Box sx={{ textAlign: 'right', display: { xs: 'none', sm: 'block' } }}>
                                        <Chip 
                                            label={enrollment.status} 
                                            size="small"
                                            className={`student-badge ${enrollment.status === 'aceptado' ? 'approved' : enrollment.status === 'pendiente' ? 'pending' : 'default'}`}
                                            sx={{ mb: 0.5 }}
                                        />
                                        <Typography variant="subtitle2" className="student-price-small">
                                            S/. {parseFloat(enrollment.item_price).toFixed(2)}
                                        </Typography>
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            ) : (
                <Box className="empty-state-box">
                    <SchoolIcon sx={{ fontSize: 48, color: '#ccc', mb: 2 }} />
                    <Typography color="text.secondary">Aún no te has matriculado en ningún curso.</Typography>
                    <Button variant="outlined" sx={{ mt: 2 }} onClick={() => navigate('/student/available-courses')}>
                        Empezar ahora
                    </Button>
                </Box>
            )}
        </Grid>
      </Grid>
    </Box>
  );
};

// Icono auxiliar que faltaba en imports
const AccessTimeIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"></path>
    </svg>
);

export default StudentDashboardComplete;