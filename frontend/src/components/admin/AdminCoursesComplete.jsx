// src/components/admin/AdminCoursesComplete.jsx
import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Tabs,
  Tab,
  Chip,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { MenuItem } from '@mui/material';
import { coursesAPI, cyclesAPI, teachersAPI } from '../../services/api';
import './admin-dashboard.css';
import { useDialog } from '../../hooks/useDialog';
import DialogWrapper from '../common/DialogWrapper';

const AdminCoursesComplete = () => {
  const [courses, setCourses] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [offerings, setOfferings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0);
  const [openCourseDialog, setOpenCourseDialog] = useState(false);
  const [openOfferingDialog, setOpenOfferingDialog] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [selectedOffering, setSelectedOffering] = useState(null);
  const [openEditOfferingDialog, setOpenEditOfferingDialog] = useState(false);
  const [editOfferingForm, setEditOfferingForm] = useState({ cycle_id: '', group_label: '', teacher_id: '', capacity: '' });
  const [courseForm, setCourseForm] = useState({
    name: '',
    description: '',
    base_price: '',
  });
  const [offeringForm, setOfferingForm] = useState({
    course_id: '',
    cycle_id: '',
    group_label: '',
    teacher_id: '',
    capacity: '',
  });
  const [searchQuery, setSearchQuery] = useState('');

  const { confirmDialog, alertDialog, showConfirm, showAlert, closeConfirm, closeAlert } = useDialog();

  // schedule management moved to AdminSchedules

  useEffect(() => {
    loadData();
  }, []);

  const getFilteredCourses = () => {
    if (!searchQuery) return courses;
    return courses.filter(c =>
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.description && c.description.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  };

  const getFilteredOfferings = () => {
    if (!searchQuery) return offerings;
    return offerings.filter(o =>
      (o.course_name && o.course_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (o.cycle_name && o.cycle_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (o.group_label && o.group_label.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [coursesData, cyclesData, teachersData] = await Promise.all([
        coursesAPI.getAll(),
        cyclesAPI.getAll(),
        teachersAPI.getAll(),
      ]);
      setCourses(coursesData);
      setCycles(cyclesData);
      setTeachers(teachersData);

      // Las ofertas vienen en los cursos, extraerlas
      const offeringsList = [];
      for (const course of coursesData) {
        if (course.offerings && course.offerings.length > 0) {
          for (const offering of course.offerings) {
            offeringsList.push({
              ...offering,
              course_name: course.name,
              base_price: course.base_price,
            });
          }
        }
      }
      setOfferings(offeringsList);
    } catch (err) {
      console.error('Error cargando datos:', err);
      showAlert('Error al cargar datos', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCourse = async () => {
    try {
      await coursesAPI.create(courseForm);
      setOpenCourseDialog(false);
      setCourseForm({ name: '', description: '', base_price: '' });
      await loadData();
    } catch (err) {
      showAlert(err.message || 'Error al crear curso', 'error');
    }
  };

  const handleCreateOffering = async () => {
    try {
      await coursesAPI.createOffering({
        course_id: offeringForm.course_id,
        cycle_id: offeringForm.cycle_id,
        group_label: offeringForm.group_label || null,
        teacher_id: offeringForm.teacher_id || null,
        capacity: offeringForm.capacity || null,
      });
      setOpenOfferingDialog(false);
      setOfferingForm({
        course_id: '',
        cycle_id: '',
        group_label: '',
        teacher_id: '',
        capacity: '',
      });
      await loadData();
    } catch (err) {
      showAlert(err.message || 'Error al crear oferta', 'error');
    }
  };

  // schedule creation removed from this page

  const openEditOffering = (offering) => {
    setSelectedOffering(offering);
    setEditOfferingForm({
      cycle_id: offering.cycle_id || '',
      group_label: offering.group_label || '',
      teacher_id: offering.teacher_id || '',
      capacity: offering.capacity || '',
    });
    setOpenEditOfferingDialog(true);
  };

  const handleUpdateOffering = async () => {
    try {
      if (!selectedOffering) return;
      await coursesAPI.updateOffering(selectedOffering.id, {
        cycle_id: editOfferingForm.cycle_id || null,
        group_label: editOfferingForm.group_label || null,
        teacher_id: editOfferingForm.teacher_id || null,
        capacity: editOfferingForm.capacity || null,
      });
      setOpenEditOfferingDialog(false);
      setSelectedOffering(null);
      await loadData();
    } catch (err) {
      showAlert(err.message || 'Error al actualizar oferta', 'error');
    }
  };

  const handleDeleteCourse = async (id) => {
    const confirmed = await showConfirm({
      title: '¿Eliminar curso?',
      message: 'Esta acción eliminará el curso y todas sus ofertas asociadas.',
      type: 'error',
      confirmText: 'Eliminar'
    });
    if (!confirmed) return;

    try {
      await coursesAPI.delete(id);
      showAlert('Curso eliminado exitosamente', 'success');
      await loadData();
    } catch (err) {
      showAlert(err.message || 'Error al eliminar curso', 'error');
    }
  };

  const handleDeleteOffering = async (id) => {
    const confirmed = await showConfirm({
      title: '¿Eliminar oferta?',
      message: 'Los estudiantes matriculados en esta oferta perderán acceso.',
      type: 'error',
      confirmText: 'Eliminar'
    });
    if (!confirmed) return;

    try {
      await coursesAPI.deleteOffering(id);
      showAlert('Oferta eliminada exitosamente', 'success');
      await loadData();
    } catch (err) {
      showAlert(err.message || 'Error al eliminar oferta', 'error');
    }
  };

  return (
    <Box className="admin-dashboard">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" className="admin-dashboard-title">Gestión de Cursos</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenCourseDialog(true)}
          className="admin-button admin-button-primary"
        >
          Nuevo Curso
        </Button>
      </Box>

      {/* Buscador Común */}
      <Box mb={3} className="admin-filters">
        <TextField
          fullWidth
          placeholder={tabValue === 0 ? "Buscar cursos..." : "Buscar ofertas..."}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
          }}
          className="admin-input"
          size="small"
        />
      </Box>

      <Tabs
        value={tabValue}
        onChange={(e, newValue) => { setTabValue(newValue); setSearchQuery(''); }}
        sx={{ mb: 3 }}
        className="admin-tabs"
        TabIndicatorProps={{ className: 'admin-tab-indicator' }}
      >
        <Tab label="Cursos" className="admin-tab" />
        <Tab label="Ofertas" className="admin-tab" />
      </Tabs>

      {/* Tab de Cursos */}
      {tabValue === 0 && (
        <TableContainer component={Paper} className="admin-table-container">
          <Table className="admin-table">
            <TableHead className="admin-table-head">
              <TableRow>
                <TableCell className="admin-table-head-cell">Nombre</TableCell>
                <TableCell className="admin-table-head-cell">Descripción</TableCell>
                <TableCell className="admin-table-head-cell">Precio Base</TableCell>
                <TableCell className="admin-table-head-cell">Acciones</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {getFilteredCourses().map((course) => (
                <TableRow key={course.id} className="admin-table-row">
                  <TableCell className="admin-table-cell">
                    <Typography variant="subtitle2" fontWeight="bold">{course.name}</Typography>
                  </TableCell>
                  <TableCell className="admin-table-cell">{course.description || '-'}</TableCell>
                  <TableCell className="admin-table-cell">S/. {parseFloat(course.base_price || 0).toFixed(2)}</TableCell>
                  <TableCell className="admin-table-cell">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteCourse(course.id)}
                      className="admin-icon-button"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {getFilteredCourses().length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ py: 3 }}>
                    <Typography color="text.secondary">No se encontraron cursos</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Tab de Ofertas */}
      {tabValue === 1 && (
        <Box>
          <Box mb={2} display="flex" justifyContent="flex-end">
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setOpenOfferingDialog(true)}
              className="admin-button admin-button-primary"
            >
              Nueva Oferta
            </Button>
          </Box>
          <TableContainer component={Paper} className="admin-table-container">
            <Table className="admin-table">
              <TableHead className="admin-table-head">
                <TableRow>
                  <TableCell className="admin-table-head-cell">Curso</TableCell>
                  <TableCell className="admin-table-head-cell">Ciclo</TableCell>
                  <TableCell className="admin-table-head-cell">Grupo</TableCell>
                  <TableCell className="admin-table-head-cell">Docente</TableCell>
                  <TableCell className="admin-table-head-cell">Precio</TableCell>
                  <TableCell className="admin-table-head-cell">Capacidad</TableCell>
                  <TableCell className="admin-table-head-cell">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {getFilteredOfferings().map((offering) => (
                  <TableRow key={offering.id} className="admin-table-row">
                    <TableCell className="admin-table-cell">
                      <Chip label={offering.course_name} size="small" className="admin-chip default" />
                    </TableCell>
                    <TableCell className="admin-table-cell">{offering.cycle_name || '-'}</TableCell>
                    <TableCell className="admin-table-cell">{offering.group_label || '-'}</TableCell>
                    <TableCell className="admin-table-cell">
                      {offering.first_name && offering.last_name
                        ? `${offering.first_name} ${offering.last_name}`
                        : '-'}
                    </TableCell>
                    <TableCell className="admin-table-cell">
                      S/. {parseFloat(offering.base_price || 0).toFixed(2)}
                    </TableCell>
                    <TableCell className="admin-table-cell">{offering.capacity || '-'}</TableCell>
                    <TableCell className="admin-table-cell">
                      {/* Horarios se gestionan en la pestaña de Horarios */}
                      <IconButton size="small" onClick={() => openEditOffering(offering)} title="Editar oferta" className="admin-icon-button">
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteOffering(offering.id)}
                        className="admin-icon-button"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                {getFilteredOfferings().length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                      <Typography color="text.secondary">No se encontraron ofertas</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Dialog Crear Curso */}
      <Dialog open={openCourseDialog} onClose={() => setOpenCourseDialog(false)} maxWidth="sm" fullWidth className="admin-dialog">
        <DialogTitle>Nuevo Curso</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 2 }}>
            <TextField
              label="Nombre del Curso"
              fullWidth
              value={courseForm.name}
              onChange={(e) => setCourseForm({ ...courseForm, name: e.target.value })}
              className="admin-input"
              placeholder="Ej: Aritmética Avanzada"
            />
            <TextField
              label="Descripción"
              fullWidth
              multiline
              rows={3}
              value={courseForm.description}
              onChange={(e) => setCourseForm({ ...courseForm, description: e.target.value })}
              className="admin-input"
              placeholder="Breve descripción del contenido..."
            />
            <TextField
              label="Precio Base (S/.)"
              type="number"
              fullWidth
              value={courseForm.base_price}
              onChange={(e) => setCourseForm({ ...courseForm, base_price: e.target.value })}
              className="admin-input"
              InputProps={{ startAdornment: <InputAdornment position="start">S/.</InputAdornment> }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCourseDialog(false)} className="admin-button admin-button-secondary">Cancelar</Button>
          <Button onClick={handleCreateCourse} variant="contained" className="admin-button admin-button-primary">
            Crear Curso
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog Crear Oferta */}
      <Dialog open={openOfferingDialog} onClose={() => setOpenOfferingDialog(false)} maxWidth="sm" fullWidth className="admin-dialog">
        <DialogTitle>Nueva Oferta de Curso</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 2 }}>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField
                label="Curso"
                select
                fullWidth
                value={offeringForm.course_id}
                onChange={(e) => setOfferingForm({ ...offeringForm, course_id: e.target.value })}
                className="admin-input admin-select"
              >
                {courses.map((course) => (
                  <MenuItem key={course.id} value={course.id}>
                    {course.name}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                label="Ciclo"
                select
                fullWidth
                value={offeringForm.cycle_id}
                onChange={(e) => setOfferingForm({ ...offeringForm, cycle_id: e.target.value })}
                className="admin-input admin-select"
              >
                {cycles.map((cycle) => (
                  <MenuItem key={cycle.id} value={cycle.id}>
                    {cycle.name}
                  </MenuItem>
                ))}
              </TextField>
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField
                label="Grupo (Ej: A, B, Aula 1)"
                fullWidth
                value={offeringForm.group_label}
                onChange={(e) => setOfferingForm({ ...offeringForm, group_label: e.target.value })}
                className="admin-input"
              />
              <TextField
                label="Capacidad de Estudiantes"
                type="number"
                fullWidth
                value={offeringForm.capacity}
                onChange={(e) => setOfferingForm({ ...offeringForm, capacity: e.target.value })}
                className="admin-input"
              />
            </Box>

            <TextField
              label="Docente Encargado"
              select
              fullWidth
              value={offeringForm.teacher_id}
              onChange={(e) => setOfferingForm({ ...offeringForm, teacher_id: e.target.value })}
              className="admin-input admin-select"
            >
              <MenuItem value="">Sin asignar</MenuItem>
              {teachers.map((teacher) => (
                <MenuItem key={teacher.id} value={teacher.id}>
                  {teacher.first_name} {teacher.last_name}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenOfferingDialog(false)} className="admin-button admin-button-secondary">Cancelar</Button>
          <Button onClick={handleCreateOffering} variant="contained" className="admin-button admin-button-primary">
            Crear Oferta
          </Button>
        </DialogActions>
      </Dialog>

      {/* Horarios: gestione en Admin > Horarios */}

      {/* Dialogo: Editar oferta de curso */}
      <Dialog open={openEditOfferingDialog} onClose={() => setOpenEditOfferingDialog(false)} maxWidth="sm" fullWidth className="admin-dialog">
        <DialogTitle>Editar oferta de curso</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 2 }}>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField select label="Ciclo" value={editOfferingForm.cycle_id}
                onChange={(e) => setEditOfferingForm({ ...editOfferingForm, cycle_id: e.target.value })} fullWidth className="admin-input admin-select">
                {cycles.map(c => (
                  <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                ))}
              </TextField>
              <TextField label="Grupo" value={editOfferingForm.group_label}
                onChange={(e) => setEditOfferingForm({ ...editOfferingForm, group_label: e.target.value })} fullWidth className="admin-input" />
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField select label="Docente" value={editOfferingForm.teacher_id}
                onChange={(e) => setEditOfferingForm({ ...editOfferingForm, teacher_id: e.target.value })} fullWidth className="admin-input admin-select">
                {teachers.map(t => (
                  <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>
                ))}
              </TextField>
              <TextField label="Capacidad" type="number" value={editOfferingForm.capacity}
                onChange={(e) => setEditOfferingForm({ ...editOfferingForm, capacity: e.target.value })} fullWidth className="admin-input" />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditOfferingDialog(false)} className="admin-button admin-button-secondary">Cancelar</Button>
          <Button variant="contained" onClick={handleUpdateOffering} className="admin-button admin-button-primary">Guardar</Button>
        </DialogActions>
      </Dialog>

      <DialogWrapper
        confirmDialog={confirmDialog}
        alertDialog={alertDialog}
        closeConfirm={closeConfirm}
        closeAlert={closeAlert}
      />
    </Box>
  );
};

export default AdminCoursesComplete;

