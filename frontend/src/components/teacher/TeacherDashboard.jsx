// src/components/teacher/TeacherDashboard.jsx
import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material';
import {
  People as PeopleIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { teachersAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import './teacher-dashboard.css';

const TeacherDashboard = () => {
  const { user } = useAuth();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.related_id) {
      loadStudents();
    }
  }, [user]);

  const loadStudents = async () => {
    try {
      setLoading(true);
      const data = await teachersAPI.getStudents(user.related_id);
      setStudents(data);
    } catch (err) {
      console.error('Error cargando estudiantes:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box className="teacher-loading">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box className="teacher-dashboard">
      <Typography variant="h4" gutterBottom className="teacher-dashboard-title">
        Dashboard Docente
      </Typography>
      <Typography className="teacher-subtitle">
        Bienvenido, {user?.name || 'Docente'}
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card className="teacher-stat-card">
            <CardContent>
              <Box display="flex" alignItems="center">
                <Box className="teacher-stat-icon primary">
                  <PeopleIcon sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Box>
                  <Typography className="teacher-stat-label">
                    Mis Estudiantes
                  </Typography>
                  <Typography className="teacher-stat-number">{students.length}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card className="teacher-stat-card">
            <CardContent>
              <Box display="flex" alignItems="center">
                <Box className="teacher-stat-icon info">
                  <AssignmentIcon sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Box>
                  <Typography className="teacher-stat-label">
                    Gestión de Asistencias
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'var(--teacher-text-secondary)', mt: 1 }}>
                    Marca las asistencias de tus estudiantes
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default TeacherDashboard;

