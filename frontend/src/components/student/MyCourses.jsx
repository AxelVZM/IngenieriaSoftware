// src/components/student/MyCourses.jsx
import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  Chip,
  Paper,
  Divider
} from '@mui/material';
import {
  CalendarMonth as CalendarIcon,
  Schedule as ClockIcon,
  School as CourseIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
import { enrollmentsAPI, schedulesAPI } from '../../services/api';
import './student-dashboard.css';

const DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
const HOURS = Array.from({ length: 15 }, (_, i) => i + 7); // 7:00 - 21:00

const COURSE_COLORS = [
  { bg: '#e0f2fe', border: '#0284c7', text: '#0c4a6e' },
  { bg: '#dcfce7', border: '#16a34a', text: '#14532d' },
  { bg: '#fef9c3', border: '#ca8a04', text: '#713f12' },
  { bg: '#fee2e2', border: '#dc2626', text: '#7f1d1d' },
  { bg: '#f3e8ff', border: '#9333ea', text: '#581c87' },
  { bg: '#ffedd5', border: '#ea580c', text: '#7c2d12' },
];

const MyCourses = () => {
  const [loading, setLoading] = useState(true);
  const [enrollments, setEnrollments] = useState([]);
  const [allSchedules, setAllSchedules] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    loadMyCoursesAndSchedules();
  }, []);

  const loadMyCoursesAndSchedules = async () => {
    try {
      setLoading(true);

      // Obtener matrículas del estudiante
      const enrollmentsData = await enrollmentsAPI.getAll();

      // Filtrar solo matrículas aceptadas con al menos un pago aprobado
      const acceptedEnrollments = enrollmentsData.filter(enrollment => {
        const isAccepted = enrollment.status === 'aceptado';
        const hasPaidInstallment = enrollment.installments &&
          enrollment.installments.some(inst => inst.status === 'paid');
        return isAccepted && hasPaidInstallment;
      });

      setEnrollments(acceptedEnrollments);

      // Cargar horarios para todas las matrículas
      const schedules = [];
      for (const enrollment of acceptedEnrollments) {
        try {
          let scheduleList = [];
          if (enrollment.enrollment_type === 'course') {
            scheduleList = await schedulesAPI.getByCourseOffering(enrollment.course_offering_id);
          } else if (enrollment.enrollment_type === 'package') {
            scheduleList = await schedulesAPI.getByPackageOffering(enrollment.package_offering_id);
          }
          schedules.push(...(scheduleList || []));
        } catch (err) {
          console.error(`Error loading schedules for enrollment ${enrollment.id}:`, err);
        }
      }

      setAllSchedules(schedules);
    } catch (err) {
      console.error('Error cargando cursos y horarios:', err);
      setError('Error al cargar tus cursos');
    } finally {
      setLoading(false);
    }
  };

  const getCourseColor = (courseName) => {
    let hash = 0;
    for (let i = 0; i < courseName.length; i++) hash = courseName.charCodeAt(i) + ((hash << 5) - hash);
    const index = Math.abs(hash) % COURSE_COLORS.length;
    return COURSE_COLORS[index];
  };

  const getPositionStyle = (startTime, endTime) => {
    const startParts = startTime.split(':').map(Number);
    const endParts = endTime.split(':').map(Number);
    const topPixels = startParts[1];
    const durationMinutes = ((endParts[0] * 60 + endParts[1]) - (startParts[0] * 60 + startParts[1]));

    return {
      top: `${topPixels}px`,
      height: `${durationMinutes}px`
    };
  };

  if (loading) {
    return (
      <Box className="student-loading">
        <CircularProgress className="student-loading-spinner" />
      </Box>
    );
  }

  if (enrollments.length === 0) {
    return (
      <Box className="student-content fade-in">
        <Box mb={4}>
          <Typography variant="h4" className="student-page-title">
            Mis Cursos
          </Typography>
          <Typography color="text.secondary">
            Visualiza los horarios de tus cursos matriculados
          </Typography>
        </Box>

        <Box className="empty-search-state">
          <CourseIcon sx={{ fontSize: 60, color: '#e2e8f0', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
            📚 Aún no tienes cursos activos
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Tus cursos aparecerán aquí una vez que se apruebe tu matrícula y pago
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box className="student-content fade-in">
      <Box mb={4}>
        <Typography variant="h4" className="student-page-title">
          📚 Mis Cursos
        </Typography>
        <Typography color="text.secondary">
          Horarios de tus cursos matriculados y aprobados
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" className="student-alert" onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Lado Izquierdo - Lista de cursos */}
        <Grid item xs={12} md={4}>
          <Box sx={{ position: 'sticky', top: 16 }}>
            {enrollments.map((enrollment) => (
              <Card key={enrollment.id} className="student-card course-card" sx={{ mb: 2 }}>
                <CardContent>
                  <Box display="flex" gap={1} mb={1}>
                    <Chip
                      label={enrollment.enrollment_type === 'course' ? '📚 Curso' : '📦 Paquete'}
                      size="small"
                      className="student-badge default"
                    />
                    <Chip
                      icon={<CheckIcon />}
                      label="Activo"
                      size="small"
                      className="student-badge approved"
                    />
                  </Box>
                  <Typography variant="h6" className="course-card-title" sx={{ mb: 1 }}>
                    {enrollment.item_name}
                  </Typography>
                  {enrollment.cycle_name && (
                    <Typography variant="body2" color="text.secondary">
                      {enrollment.cycle_name}
                    </Typography>
                  )}
                  {(enrollment.cycle_start_date || enrollment.cycle_end_date) && (
                    <Typography variant="caption" color="text.secondary" display="block">
                      {enrollment.cycle_start_date && new Date(enrollment.cycle_start_date).toLocaleDateString()}
                      {' - '}
                      {enrollment.cycle_end_date && new Date(enrollment.cycle_end_date).toLocaleDateString()}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            ))}
          </Box>
        </Grid>

        {/* Lado Derecho - Calendario Semanal */}
        <Grid item xs={12} md={8}>
          <Paper className="calendar-container" sx={{ overflowX: 'auto', p: 2, borderRadius: 3 }}>
            <div className="calendar-grid">
              <div className="calendar-header-cell time-col">Hora</div>
              {DAYS.map(day => (
                <div key={day} className="calendar-header-cell day-col">{day.toUpperCase()}</div>
              ))}

              {HOURS.map(hour => (
                <React.Fragment key={hour}>
                  <div className="calendar-time-cell">
                    {`${hour.toString().padStart(2, '0')}:00`}
                  </div>

                  {DAYS.map(day => (
                    <div
                      key={`${day}-${hour}`}
                      className="calendar-cell"
                    >
                      {allSchedules
                        .filter(s => s.day_of_week === day)
                        .filter(s => parseInt(s.start_time.split(':')[0]) === hour)
                        .map(schedule => {
                          const styles = getPositionStyle(schedule.start_time, schedule.end_time);
                          const colors = getCourseColor(schedule.course_name || 'X');

                          return (
                            <div
                              key={schedule.id}
                              className="calendar-event admin-fade-in"
                              style={{
                                ...styles,
                                backgroundColor: colors.bg,
                                borderLeft: `4px solid ${colors.border}`,
                                color: colors.text,
                                cursor: 'default'
                              }}
                              title={`${schedule.course_name} (${schedule.start_time} - ${schedule.end_time})`}
                            >
                              <div className="event-time" style={{ color: colors.border }}>
                                {schedule.start_time.slice(0, 5)} - {schedule.end_time.slice(0, 5)}
                              </div>
                              <div className="event-title">
                                {schedule.course_name}
                              </div>
                              <div className="event-details">
                                {schedule.classroom && <span>Aula {schedule.classroom}</span>}
                              </div>
                            </div>
                          );
                        })
                      }
                    </div>
                  ))}
                </React.Fragment>
              ))}
            </div>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MyCourses;
