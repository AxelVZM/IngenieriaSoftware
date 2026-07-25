// src/components/teacher/TeacherAttendance.jsx
import React, { useEffect, useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  TextField,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  Grid,
  Collapse,
  Checkbox,
  IconButton,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import { teachersAPI, coursesAPI, cyclesAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import ConfirmDialog from '../common/ConfirmDialog';
import './teacher-dashboard.css';

// Configure dayjs to use Spanish locale
dayjs.locale('es');

const TeacherAttendance = () => {
  const { user } = useAuth();
  const [schedules, setSchedules] = useState([]);
  const [students, setStudents] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [courses, setCourses] = useState([]);
  const [filterCycle, setFilterCycle] = useState('all');
  const [filterCourse, setFilterCourse] = useState('all');
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [expandedSchedule, setExpandedSchedule] = useState(null);
  const [attendanceData, setAttendanceData] = useState({});
  const [loading, setLoading] = useState(true);
  const [errorDialog, setErrorDialog] = useState({ open: false, message: '' });
  const [successDialog, setSuccessDialog] = useState({ open: false, message: '' });

  useEffect(() => {
    if (user?.related_id) {
      loadData();
    }
  }, [user]);

  useEffect(() => {
    if (expandedSchedule && selectedDate) {
      loadAttendanceData(expandedSchedule, selectedDate.format('YYYY-MM-DD'));
    }
  }, [selectedDate]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [coursesData, cyclesData] = await Promise.all([
        coursesAPI.getAll(),
        cyclesAPI.getAll(),
      ]);

      setCycles(cyclesData);
      setCourses(coursesData);

      const allSchedules = [];
      for (const course of coursesData) {
        if (course.offerings) {
          for (const offering of course.offerings) {
            if (offering.teacher_id === user.related_id && offering.schedules) {
              for (const schedule of offering.schedules) {
                allSchedules.push({
                  ...schedule,
                  courseName: course.name,
                  courseId: course.id,
                  offeringId: offering.id,
                  cycleId: offering.cycle_id,
                  groupLabel: offering.group_label,
                });
              }
            }
          }
        }
      }
      setSchedules(allSchedules);
    } catch (err) {
      console.error('Error cargando datos:', err);
      setErrorDialog({
        open: true,
        message: 'Error al cargar datos'
      });
    } finally {
      setLoading(false);
    }
  };

  const filteredSchedules = useMemo(() => {
    return schedules.filter(s => {
      const matchCycle = filterCycle === 'all' || s.cycleId === parseInt(filterCycle);
      const matchCourse = filterCourse === 'all' || s.courseId === parseInt(filterCourse);
      return matchCycle && matchCourse;
    });
  }, [schedules, filterCycle, filterCourse]);

  const dateRange = useMemo(() => {
    if (filterCycle === 'all') return { min: null, max: null };
    const cycle = cycles.find(c => c.id === parseInt(filterCycle));
    if (!cycle) return { min: null, max: null };
    return {
      min: dayjs(cycle.start_date),
      max: dayjs(cycle.end_date)
    };
  }, [filterCycle, cycles]);

  const handleToggleSchedule = async (scheduleId) => {
    // Require cycle filter
    if (filterCycle === 'all') {
      setErrorDialog({
        open: true,
        message: 'Debes seleccionar un ciclo específico antes de marcar asistencia'
      });
      return;
    }

    if (expandedSchedule === scheduleId) {
      setExpandedSchedule(null);
      setAttendanceData({});
      setStudents([]);
    } else {
      setExpandedSchedule(scheduleId);

      // Load students for this specific course offering
      const schedule = schedules.find(s => s.id === scheduleId);
      if (schedule) {
        try {
          const courseStudents = await teachersAPI.getStudentsByCourse(
            user.related_id,
            schedule.course_offering_id
          );
          setStudents(courseStudents);
          await loadAttendanceData(scheduleId, selectedDate.format('YYYY-MM-DD'));
        } catch (err) {
          console.error('Error loading students:', err);
          setStudents([]);
        }
      }
    }
  };

  const loadAttendanceData = async (scheduleId, date) => {
    try {
      const records = await teachersAPI.getAttendance(user.related_id, scheduleId, date);
      const data = {};
      students.forEach(s => {
        const record = records.find(r => r.student_id === s.id);
        data[s.id] = record ? record.status === 'presente' : true;
      });
      setAttendanceData(data);
    } catch (err) {
      // If no records, initialize all as present
      const initial = {};
      students.forEach(s => { initial[s.id] = true; });
      setAttendanceData(initial);
    }
  };

  const handleSelectAll = () => {
    const all = {};
    students.forEach(s => { all[s.id] = true; });
    setAttendanceData(all);
  };

  const handleSelectNone = () => {
    const none = {};
    students.forEach(s => { none[s.id] = false; });
    setAttendanceData(none);
  };

  const handleSaveAttendance = async (scheduleId) => {
    const schedule = schedules.find(s => s.id === scheduleId);
    if (!schedule) return;

    // Validate date is not in the future
    const today = dayjs().endOf('day');
    if (selectedDate.isAfter(today)) {
      setErrorDialog({
        open: true,
        message: 'No puedes marcar asistencia para fechas futuras'
      });
      return;
    }

    // Validate weekday matches schedule
    const dayNames = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
    const selectedDayName = dayNames[selectedDate.day()];

    if (selectedDayName !== schedule.day_of_week) {
      setErrorDialog({
        open: true,
        message: `La fecha seleccionada es ${selectedDayName}, pero este horario es para ${schedule.day_of_week}`
      });
      return;
    }

    // Validate date is within cycle range
    if (dateRange.min && selectedDate.isBefore(dateRange.min)) {
      setErrorDialog({
        open: true,
        message: 'La fecha está fuera del rango del ciclo'
      });
      return;
    }
    if (dateRange.max && selectedDate.isAfter(dateRange.max)) {
      setErrorDialog({
        open: true,
        message: 'La fecha está fuera del rango del ciclo'
      });
      return;
    }

    try {
      const promises = students.map(student =>
        teachersAPI.markAttendance(user.related_id, {
          schedule_id: scheduleId,
          student_id: student.id,
          status: attendanceData[student.id] ? 'presente' : 'ausente',
          date: selectedDate.format('YYYY-MM-DD'),
        })
      );
      await Promise.all(promises);
      setExpandedSchedule(null);
      setAttendanceData({});
      setSuccessDialog({
        open: true,
        message: `Asistencia guardada correctamente para ${students.length} estudiantes`
      });
    } catch (err) {
      setErrorDialog({
        open: true,
        message: err.message || 'Error al guardar asistencia'
      });
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
        Gestión de Asistencias
      </Typography>

      <Paper sx={{ p: 3, mb: 4, borderRadius: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={3}>
            <TextField
              select
              fullWidth
              label="Filtrar por Ciclo"
              value={filterCycle}
              onChange={(e) => setFilterCycle(e.target.value)}
              size="small"
            >
              <MenuItem value="all">Todos los Ciclos</MenuItem>
              {cycles.map(c => (
                <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              select
              fullWidth
              label="Filtrar por Curso"
              value={filterCourse}
              onChange={(e) => setFilterCourse(e.target.value)}
              size="small"
            >
              <MenuItem value="all">Todos los Cursos</MenuItem>
              {courses.map(c => (
                <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} md={3}>
            <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="es">
              <DatePicker
                label="Fecha de Asistencia"
                value={selectedDate}
                onChange={(newValue) => {
                  if (newValue) {
                    setSelectedDate(newValue);
                  }
                }}
                format="DD/MM/YYYY"
                minDate={dateRange.min}
                maxDate={dateRange.max ? (dateRange.max.isBefore(dayjs()) ? dateRange.max : dayjs()) : dayjs()}
                slotProps={{
                  textField: {
                    size: 'small',
                    fullWidth: true,
                  },
                }}
              />
            </LocalizationProvider>
          </Grid>
        </Grid>
      </Paper>

      <Typography className="teacher-section-header">
        Horarios Disponibles ({filteredSchedules.length})
      </Typography>
      <TableContainer component={Paper} className="teacher-table-container">
        <Table className="teacher-table">
          <TableHead className="teacher-table-head">
            <TableRow>
              <TableCell className="teacher-table-head-cell">Curso / Grupo</TableCell>
              <TableCell className="teacher-table-head-cell">Ciclo</TableCell>
              <TableCell className="teacher-table-head-cell">Horario</TableCell>
              <TableCell className="teacher-table-head-cell">Aula</TableCell>
              <TableCell className="teacher-table-head-cell">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredSchedules.map((schedule) => (
              <React.Fragment key={schedule.id}>
                <TableRow className="teacher-table-row">
                  <TableCell className="teacher-table-cell">
                    <Typography variant="subtitle2" fontWeight="bold">
                      {schedule.courseName}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Grupo: {schedule.groupLabel || 'A'}
                    </Typography>
                  </TableCell>
                  <TableCell className="teacher-table-cell">
                    {cycles.find(c => c.id === schedule.cycleId)?.name || 'N/A'}
                  </TableCell>
                  <TableCell className="teacher-table-cell">
                    <Chip
                      label={`${schedule.day_of_week}: ${schedule.start_time} - ${schedule.end_time}`}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell className="teacher-table-cell">{schedule.classroom || '-'}</TableCell>
                  <TableCell className="teacher-table-cell">
                    <IconButton
                      size="small"
                      onClick={() => handleToggleSchedule(schedule.id)}
                    >
                      {expandedSchedule === schedule.id ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell colSpan={5} sx={{ p: 0, border: 0 }}>
                    <Collapse in={expandedSchedule === schedule.id} timeout="auto" unmountOnExit>
                      <Box sx={{ p: 3, bgcolor: '#f5f5f5' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h6">
                            Estudiantes - {selectedDate.format('DD/MM/YYYY')}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Button size="small" variant="outlined" onClick={handleSelectAll}>
                              Marcar Todos
                            </Button>
                            <Button size="small" variant="outlined" onClick={handleSelectNone}>
                              Desmarcar Todos
                            </Button>
                          </Box>
                        </Box>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>DNI</TableCell>
                              <TableCell>Estudiante</TableCell>
                              <TableCell>Teléfono</TableCell>
                              <TableCell>Apoderado</TableCell>
                              <TableCell>Tel. Apoderado</TableCell>
                              <TableCell align="center">Presente</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {students.map(student => (
                              <TableRow key={student.id}>
                                <TableCell>{student.dni}</TableCell>
                                <TableCell>{student.first_name} {student.last_name}</TableCell>
                                <TableCell>{student.phone || '-'}</TableCell>
                                <TableCell>{student.parent_name || '-'}</TableCell>
                                <TableCell>{student.parent_phone || '-'}</TableCell>
                                <TableCell align="center">
                                  <Checkbox
                                    checked={attendanceData[student.id] || false}
                                    onChange={(e) => setAttendanceData({
                                      ...attendanceData,
                                      [student.id]: e.target.checked
                                    })}
                                    color="success"
                                  />
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                          <Button
                            variant="contained"
                            color="primary"
                            onClick={() => handleSaveAttendance(schedule.id)}
                          >
                            Guardar Asistencias
                          </Button>
                        </Box>
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
        {filteredSchedules.length === 0 && (
          <Box className="teacher-empty-state">
            <Typography className="teacher-empty-state-text">
              No se encontraron horarios con los filtros seleccionados
            </Typography>
          </Box>
        )}
      </TableContainer>

      <ConfirmDialog
        open={errorDialog.open}
        onClose={() => setErrorDialog({ open: false, message: '' })}
        onConfirm={() => setErrorDialog({ open: false, message: '' })}
        title="Error de Validación"
        message={errorDialog.message}
        type="error"
        confirmText="Aceptar"
        cancelText=""
      />

      <ConfirmDialog
        open={successDialog.open}
        onClose={() => setSuccessDialog({ open: false, message: '' })}
        onConfirm={() => setSuccessDialog({ open: false, message: '' })}
        title="Éxito"
        message={successDialog.message}
        type="success"
        confirmText="Aceptar"
        cancelText=""
      />
    </Box >
  );
};

export default TeacherAttendance;
