// src/components/admin/AdminDashboard.jsx
import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
} from '@mui/material';
import {
  People as PeopleIcon,
  School as SchoolIcon,
  Assignment as AssignmentIcon,
  Payment as PaymentIcon,
} from '@mui/icons-material';
import { adminAPI } from '../../services/api';
import './admin-dashboard.css';

const AdminDashboard = () => {
  const [dashboard, setDashboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCycleId, setSelectedCycleId] = useState('all');
  const [activeTab, setActiveTab] = useState('summary');
  const [selectedCourse, setSelectedCourse] = useState('all');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getDashboard();
      setDashboard(data);
      setError('');
    } catch (err) {
      setError(err.message || 'Error al cargar el dashboard');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box className="admin-loading">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error" className="admin-alert">{error}</Alert>;
  }

  // Derivar lista de ciclos y aplicar filtro por ciclo
  const cycleOptions = Array.from(
    new Map(
      dashboard.map((row) => [row.cycle_id, { id: row.cycle_id, name: row.cycle_name }])
    ).values()
  ).filter(c => c.id != null);

  const filteredDashboard =
    selectedCycleId === 'all'
      ? dashboard
      : dashboard.filter((row) => row.cycle_id === selectedCycleId);

  // Opciones de curso+grupo para pestaña de asistencia (todos los cursos)
  const courseOptions = Array.from(
    new Map(
      filteredDashboard
        .filter((row) => row.enrollment_status === 'aceptado') // Only accepted enrollments
        .map((row) => {
          const label = row.grupo
            ? `${row.enrolled_item} - Grupo ${row.grupo}`
            : row.enrolled_item;
          return [label, { name: label }];
        })
    ).values()
  );

  // Calcular estadísticas
  // Reglas para montos:
  // - Si un alumno tiene un paquete en un ciclo (enrollment_type === 'package'),
  //   solo se cuenta el monto del paquete para ese alumno+ciclo.
  // - Si no tiene paquete en ese ciclo, se suman todos los cursos individuales.

  const packageByStudentCycle = new Set(
    filteredDashboard
      .filter(row => row.enrollment_type === 'package')
      .map(row => `${row.student_id}-${row.cycle_id}`)
  );

  const totalsFromEnrollments = filteredDashboard.reduce(
    (acc, row) => {
      const key = `${row.student_id}-${row.cycle_id}`;
      const paid = parseFloat(row.total_paid || 0) || 0;
      const pending = parseFloat(row.total_pending || 0) || 0;

      if (row.enrollment_type === 'package') {
        // Contar siempre los paquetes (una fila por matrícula de paquete)
        acc.totalPaid += paid;
        acc.totalPending += pending;
        return acc;
      }

      // Matrícula de curso
      if (packageByStudentCycle.has(key)) {
        // Si ya hay paquete en ese alumno+ciclo, los cursos asociados
        // se consideran incluidos en el paquete y no se suman aparte.
        return acc;
      }

      // Cursos individuales (sin paquete en ese ciclo)
      acc.totalPaid += paid;
      acc.totalPending += pending;
      return acc;
    },
    { totalPaid: 0, totalPending: 0 }
  );

  const today = new Date();

  const stats = {
    totalStudents: new Set(filteredDashboard.map(d => d.student_id)).size,
    totalEnrollments: filteredDashboard.length,
    pendingEnrollments: filteredDashboard.filter(d => d.enrollment_status === 'pendiente').length,
    acceptedEnrollments: filteredDashboard.filter(d => d.enrollment_status === 'aceptado').length,
    totalPending: totalsFromEnrollments.totalPending,
    totalPaid: totalsFromEnrollments.totalPaid,
    // Solo contar baja asistencia en ciclos ya iniciados
    lowAttendance: filteredDashboard.filter(d => {
      if (!d.start_date) return false;
      const start = new Date(d.start_date);
      if (start > today) return false;
      return parseFloat(d.attendance_pct || 0) < 75;
    }).length,
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'aceptado':
        return 'success';
      case 'pendiente':
        return 'warning';
      case 'rechazado':
        return 'error';
      default:
        return 'default';
    }
  };

  const getAlertColor = (alert) => {
    if (alert?.includes('Deuda')) return 'error';
    if (alert?.includes('Faltas')) return 'warning';
    if (alert?.includes('Baja asistencia')) return 'warning';
    return 'success';
  };

  return (
    <Box className="admin-dashboard">
      <Typography variant="h4" gutterBottom className="admin-dashboard-title">
        Dashboard Administrativo
      </Typography>

      {/* Filtro por ciclo */}
      <Box mb={3} className="admin-filters">
        <FormControl size="small" sx={{ minWidth: 220 }} className="admin-select">
          <InputLabel id="cycle-filter-label">Ciclo</InputLabel>
          <Select
            labelId="cycle-filter-label"
            value={selectedCycleId}
            label="Ciclo"
            onChange={(e) => setSelectedCycleId(e.target.value)}
          >
            <MenuItem value="all">Todos los ciclos</MenuItem>
            {cycleOptions.map((cycle) => (
              <MenuItem key={cycle.id} value={cycle.id}>
                {cycle.name || `Ciclo ${cycle.id}`}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Estadísticas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="admin-stat-card admin-fade-in">
            <CardContent>
              <Box display="flex" alignItems="center">
                <Box className="admin-stat-icon primary">
                  <PeopleIcon sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Box>
                  <Typography className="admin-stat-label">
                    Estudiantes
                  </Typography>
                  <Typography className="admin-stat-number">{stats.totalStudents}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="admin-stat-card admin-fade-in">
            <CardContent>
              <Box display="flex" alignItems="center">
                <Box className="admin-stat-icon warning">
                  <AssignmentIcon sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Box>
                  <Typography className="admin-stat-label">
                    Matrículas Pendientes
                  </Typography>
                  <Typography className="admin-stat-number">{stats.pendingEnrollments}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="admin-stat-card admin-fade-in">
            <CardContent>
              <Box display="flex" alignItems="center">
                <Box className="admin-stat-icon success">
                  <PaymentIcon sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Box>
                  <Typography className="admin-stat-label">
                    Total Pagado
                  </Typography>
                  <Typography className="admin-stat-number">S/. {stats.totalPaid.toFixed(2)}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="admin-stat-card admin-fade-in">
            <CardContent>
              <Box display="flex" alignItems="center">
                <Box className="admin-stat-icon danger">
                  <PaymentIcon sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Box>
                  <Typography className="admin-stat-label">
                    Total Pendiente
                  </Typography>
                  <Typography className="admin-stat-number">S/. {stats.totalPending.toFixed(2)}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Pestañas para separar vistas */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs
          value={activeTab}
          onChange={(_, value) => setActiveTab(value)}
          className="admin-tabs"
          TabIndicatorProps={{ className: 'admin-tab-indicator' }}
        >
          <Tab label="Resumen" value="summary" className="admin-tab" />
          <Tab label="Pagos" value="payments" className="admin-tab" />
          <Tab label="Asistencia" value="attendance" className="admin-tab" />
        </Tabs>
      </Box>

      {/* Contenido de pestañas */}
      {activeTab === 'summary' && (
        <TableContainer component={Paper} className="admin-table-container">
          <Table className="admin-table">
            <TableHead className="admin-table-head">
              <TableRow>
                <TableCell className="admin-table-head-cell">Estudiante</TableCell>
                <TableCell className="admin-table-head-cell">DNI</TableCell>
                <TableCell className="admin-table-head-cell">Ciclo</TableCell>
                <TableCell className="admin-table-head-cell">Curso/Paquete</TableCell>
                <TableCell className="admin-table-head-cell">Estado</TableCell>
                <TableCell className="admin-table-head-cell">Asistencia</TableCell>
                <TableCell className="admin-table-head-cell">Pagado</TableCell>
                <TableCell className="admin-table-head-cell">Pendiente</TableCell>
                <TableCell className="admin-table-head-cell">Alerta</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredDashboard
                .filter((row) => {
                  const key = `${row.student_id}-${row.cycle_id}`;

                  if (row.enrollment_type === 'package') {
                    // Siempre mostrar la matrícula de paquete
                    return true;
                  }

                  // Si existe paquete para ese alumno+ciclo, ocultar los cursos asociados
                  if (packageByStudentCycle.has(key)) {
                    return false;
                  }

                  // Cursos individuales sin paquete
                  return true;
                })
                .map((row) => (
                  <TableRow key={`${row.student_id}-${row.enrollment_id}`} className="admin-table-row">
                    <TableCell className="admin-table-cell">{row.student_name}</TableCell>
                    <TableCell className="admin-table-cell">{row.dni}</TableCell>
                    <TableCell className="admin-table-cell">{row.cycle_name}</TableCell>
                    <TableCell className="admin-table-cell">{row.enrolled_item}</TableCell>
                    <TableCell className="admin-table-cell">
                      <Chip
                        label={row.enrollment_status}
                        color={getStatusColor(row.enrollment_status)}
                        size="small"
                        className="admin-chip"
                      />
                    </TableCell>
                    <TableCell className="admin-table-cell">
                      {(() => {
                        if (!row.start_date) return '-';
                        const start = new Date(row.start_date);
                        if (start > today) return '-';
                        return `${parseFloat(row.attendance_pct || 0).toFixed(1)}%`;
                      })()}
                    </TableCell>
                    <TableCell className="admin-table-cell">
                      S/. {parseFloat(row.total_paid || 0).toFixed(2)}
                    </TableCell>
                    <TableCell className="admin-table-cell">
                      S/. {parseFloat(row.total_pending || 0).toFixed(2)}
                    </TableCell>
                    <TableCell className="admin-table-cell">
                      {(() => {
                        const label = row.alert_status || 'En regla';

                        if (!row.start_date) {
                          return (
                            <Chip
                              label={label}
                              color={getAlertColor(label)}
                              size="small"
                            />
                          );
                        }

                        const start = new Date(row.start_date);

                        if (start > today) {
                          // Ciclo futuro: mantener alertas de pago/deuda, ocultar las de asistencia
                          const isPaymentAlert =
                            label?.toLowerCase().includes('deuda') ||
                            label?.toLowerCase().includes('pago');

                          if (!isPaymentAlert) return '-';

                          return (
                            <Chip
                              label={label}
                              color={getAlertColor(label)}
                              size="small"
                            />
                          );
                        }

                        // Ciclo ya iniciado: mostrar cualquier alerta normalmente
                        return (
                          <Chip
                            label={label}
                            color={getAlertColor(label)}
                            size="small"
                          />
                        );
                      })()}
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
          {filteredDashboard.length === 0 && (
            <Box p={3} textAlign="center">
              <Typography color="textSecondary">No hay datos para mostrar</Typography>
            </Box>
          )}
        </TableContainer>
      )}

      {activeTab === 'payments' && (
        <TableContainer component={Paper} className="admin-table-container">
          <Table className="admin-table">
            <TableHead className="admin-table-head">
              <TableRow>
                <TableCell className="admin-table-head-cell">Estudiante</TableCell>
                <TableCell className="admin-table-head-cell">Ciclo</TableCell>
                <TableCell className="admin-table-head-cell">Curso/Paquete</TableCell>
                <TableCell className="admin-table-head-cell">Pagado</TableCell>
                <TableCell className="admin-table-head-cell">Pendiente</TableCell>
                <TableCell className="admin-table-head-cell">Cuotas pagadas</TableCell>
                <TableCell className="admin-table-head-cell">Cuotas pendientes</TableCell>
                <TableCell className="admin-table-head-cell">Fecha de Vencimiento</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredDashboard
                .filter((row) => {
                  const key = `${row.student_id}-${row.cycle_id}`;

                  if (row.enrollment_type === 'package') return true;
                  if (packageByStudentCycle.has(key)) return false;
                  return true;
                })
                .map((row) => (
                  <TableRow key={`${row.student_id}-${row.enrollment_id}`} className="admin-table-row">
                    <TableCell className="admin-table-cell">{row.student_name}</TableCell>
                    <TableCell className="admin-table-cell">{row.cycle_name}</TableCell>
                    <TableCell className="admin-table-cell">{row.enrolled_item}</TableCell>
                    <TableCell className="admin-table-cell">S/. {parseFloat(row.total_paid || 0).toFixed(2)}</TableCell>
                    <TableCell className="admin-table-cell">S/. {parseFloat(row.total_pending || 0).toFixed(2)}</TableCell>
                    <TableCell className="admin-table-cell">
                      {(() => {
                        const pending = parseFloat(row.total_pending || 0) || 0;
                        // Mientras no exista pago en partes, considerar solo 0 o 1 cuota pagada
                        return pending > 0 ? 0 : 1;
                      })()}
                    </TableCell>
                    <TableCell className="admin-table-cell">{row.pending_installments}</TableCell>
                    <TableCell className="admin-table-cell">
                      {row.next_due_date
                        ? new Date(row.next_due_date).toLocaleDateString()
                        : '-'}
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
          {filteredDashboard.length === 0 && (
            <Box p={3} textAlign="center">
              <Typography color="textSecondary">No hay datos para mostrar</Typography>
            </Box>
          )}
        </TableContainer>
      )}

      {activeTab === 'attendance' && (
        <>
          {/* Filtros en pestaña de asistencia */}
          <Box mb={2} display="flex" gap={2}>
            <FormControl size="small" sx={{ minWidth: 220 }}>
              <InputLabel id="cycle-filter-attendance-label">Ciclo</InputLabel>
              <Select
                labelId="cycle-filter-attendance-label"
                value={selectedCycleId}
                label="Ciclo"
                onChange={(e) => setSelectedCycleId(e.target.value)}
              >
                <MenuItem value="all">Todos los ciclos</MenuItem>
                {cycleOptions.map((cycle) => (
                  <MenuItem key={cycle.id} value={cycle.id}>
                    {cycle.name || `Ciclo ${cycle.id}`}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 220 }}>
              <InputLabel id="course-filter-label">Curso</InputLabel>
              <Select
                labelId="course-filter-label"
                value={selectedCourse}
                label="Curso"
                onChange={(e) => setSelectedCourse(e.target.value)}
              >
                <MenuItem value="all">Todos los cursos</MenuItem>
                {courseOptions.map((course) => (
                  <MenuItem key={course.name} value={course.name}>
                    {course.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <TableContainer component={Paper} className="admin-table-container">
            <Table className="admin-table">
              <TableHead className="admin-table-head">
                <TableRow>
                  <TableCell className="admin-table-head-cell">Estudiante</TableCell>
                  <TableCell className="admin-table-head-cell">Ciclo</TableCell>
                  <TableCell className="admin-table-head-cell">Curso</TableCell>
                  <TableCell className="admin-table-head-cell">Asistencia</TableCell>
                  <TableCell className="admin-table-head-cell">Alerta</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredDashboard
                  .filter((row) => {
                    // Show all accepted enrollments (course or package)
                    if (row.enrollment_status !== 'aceptado') return false;

                    // Apply course filter if selected
                    if (selectedCourse !== 'all') {
                      const label = row.grupo
                        ? `${row.enrolled_item} - Grupo ${row.grupo}`
                        : row.enrolled_item;
                      return label === selectedCourse;
                    }

                    return true;
                  })
                  .map((row) => (
                    <TableRow key={`${row.student_id}-${row.enrollment_id}`} className="admin-table-row">
                      <TableCell className="admin-table-cell">{row.student_name}</TableCell>
                      <TableCell className="admin-table-cell">{row.cycle_name}</TableCell>
                      <TableCell className="admin-table-cell">
                        {row.grupo
                          ? `${row.enrolled_item} - Grupo ${row.grupo}`
                          : row.enrolled_item}
                      </TableCell>
                      <TableCell>
                        {(() => {
                          if (!row.start_date) return '-';
                          const start = new Date(row.start_date);
                          if (start > today) return '-';
                          return `${parseFloat(row.attendance_pct || 0).toFixed(1)}%`;
                        })()}
                      </TableCell>
                      <TableCell>
                        {(() => {
                          const label = row.alert_status || 'En regla';

                          if (!row.start_date) {
                            return (
                              <Chip
                                label={label}
                                color={getAlertColor(label)}
                                size="small"
                              />
                            );
                          }

                          const start = new Date(row.start_date);

                          if (start > today) {
                            // Ciclo futuro: mantener alertas de pago/deuda, ocultar las de asistencia
                            const isPaymentAlert =
                              label?.toLowerCase().includes('deuda') ||
                              label?.toLowerCase().includes('pago');

                            if (!isPaymentAlert) return '-';

                            return (
                              <Chip
                                label={label}
                                color={getAlertColor(label)}
                                size="small"
                              />
                            );
                          }

                          // Ciclo ya iniciado: mostrar cualquier alerta normalmente
                          return (
                            <Chip
                              label={label}
                              color={getAlertColor(label)}
                              size="small"
                            />
                          );
                        })()}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
            {filteredDashboard.filter(row => row.enrollment_status === 'aceptado').length === 0 && (
              <Box p={3} textAlign="center">
                <Typography color="textSecondary">No hay datos para mostrar</Typography>
              </Box>
            )}
          </TableContainer>
        </>
      )}
    </Box>
  );
}
export default AdminDashboard;
