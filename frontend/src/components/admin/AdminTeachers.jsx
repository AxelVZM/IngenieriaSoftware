// src/components/admin/AdminTeachers.jsx
import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TableContainer,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Tooltip,
  InputAdornment
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  RestartAlt as RestartAltIcon,
  Search as SearchIcon
} from '@mui/icons-material';
import { teachersAPI } from '../../services/api';
import './admin-dashboard.css';
import { useDialog } from '../../hooks/useDialog';
import DialogWrapper from '../common/DialogWrapper';

const AdminTeachers = () => {
  const [teachers, setTeachers] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [form, setForm] = useState({ first_name: '', last_name: '', dni: '', phone: '', email: '', specialization: '' });
  const [searchQuery, setSearchQuery] = useState('');

  const { confirmDialog, alertDialog, showConfirm, showAlert, closeConfirm, closeAlert } = useDialog();

  const fetchTeachers = async () => {
    try {
      const data = await teachersAPI.getAll();
      setTeachers(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreate = async () => {
    try {
      await teachersAPI.create(form);
      setOpenDialog(false);
      setForm({ first_name: '', last_name: '', dni: '', phone: '', email: '', specialization: '' });
      await fetchTeachers();
    } catch (err) {
      showAlert(err.message || 'Error al crear docente', 'error');
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm({
      title: '¿Eliminar docente?',
      message: 'Esta acción eliminará permanentemente al docente del sistema.',
      type: 'error',
      confirmText: 'Eliminar'
    });
    if (!confirmed) return;

    try {
      await teachersAPI.delete(id);
      showAlert('Docente eliminado exitosamente', 'success');
      await fetchTeachers();
    } catch (err) {
      showAlert(err.message || 'Error al eliminar docente', 'error');
    }
  };

  const handleResetPassword = async (id) => {
    const confirmed = await showConfirm({
      title: '¿Reiniciar contraseña?',
      message: 'La contraseña del docente será restablecida a su número de DNI.',
      type: 'warning',
      confirmText: 'Reiniciar'
    });
    if (!confirmed) return;

    try {
      await teachersAPI.resetPassword(id);
      showAlert('Contraseña restablecida al DNI exitosamente', 'success');
    } catch (err) {
      showAlert(err.message || 'Error al restablecer contraseña', 'error');
    }
  };

  const getFilteredTeachers = () => {
    if (!searchQuery) return teachers;
    return teachers.filter(t =>
      (t.name && t.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (t.dni && t.dni.includes(searchQuery)) ||
      (t.email && t.email.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  };

  useEffect(() => { fetchTeachers(); }, []);

  return (
    <Box className="admin-dashboard">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" className="admin-dashboard-title">Gestión de Docentes</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
          className="admin-button admin-button-primary"
        >
          Nuevo Docente
        </Button>
      </Box>

      {/* Search Bar */}
      <Box mb={3} className="admin-filters">
        <TextField
          fullWidth
          placeholder="Buscar docentes por nombre, DNI o email..."
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

      <TableContainer component={Paper} className="admin-table-container">
        <Table className="admin-table">
          <TableHead className="admin-table-head">
            <TableRow>
              <TableCell className="admin-table-head-cell">Nombre</TableCell>
              <TableCell className="admin-table-head-cell">DNI</TableCell>
              <TableCell className="admin-table-head-cell">Teléfono</TableCell>
              <TableCell className="admin-table-head-cell">Email</TableCell>
              <TableCell className="admin-table-head-cell">Especialidad</TableCell>
              <TableCell className="admin-table-head-cell">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {getFilteredTeachers().map(t => (
              <TableRow key={t.id} className="admin-table-row">
                <TableCell className="admin-table-cell">
                  <Typography variant="subtitle2" fontWeight="bold">{t.name}</Typography>
                </TableCell>
                <TableCell className="admin-table-cell">{t.dni}</TableCell>
                <TableCell className="admin-table-cell">{t.phone}</TableCell>
                <TableCell className="admin-table-cell">{t.email}</TableCell>
                <TableCell className="admin-table-cell">{t.specialization || '-'}</TableCell>
                <TableCell className="admin-table-cell">
                  <Tooltip title="Reiniciar contraseña a DNI">
                    <IconButton size="small" onClick={() => handleResetPassword(t.id)} className="admin-icon-button">
                      <RestartAltIcon />
                    </IconButton>
                  </Tooltip>
                  <IconButton size="small" color="error" onClick={() => handleDelete(t.id)} className="admin-icon-button">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {getFilteredTeachers().length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                  <Typography color="text.secondary">
                    {searchQuery ? 'No se encontraron docentes' : 'No hay docentes registrados'}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth className="admin-dialog">
        <DialogTitle>Nuevo Docente</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 3, pt: 2 }}>
            <TextField
              label="Nombres"
              value={form.first_name}
              onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              fullWidth
              className="admin-input"
              placeholder="Ej: Juan Carlos"
            />
            <TextField
              label="Apellidos"
              value={form.last_name}
              onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              fullWidth
              className="admin-input"
              placeholder="Ej: Pérez López"
            />
            <TextField
              label="DNI"
              value={form.dni}
              onChange={(e) => setForm({ ...form, dni: e.target.value })}
              fullWidth
              className="admin-input"
              placeholder="Ej: 12345678"
            />
            <TextField
              label="Teléfono"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              fullWidth
              className="admin-input"
              placeholder="Ej: 987654321"
            />
            <TextField
              label="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              fullWidth
              className="admin-input"
              placeholder="Ej: profesor@academia.com"
              sx={{ gridColumn: '1 / -1' }}
            />
            <TextField
              label="Especialidad"
              value={form.specialization}
              onChange={(e) => setForm({ ...form, specialization: e.target.value })}
              fullWidth
              className="admin-input"
              placeholder="Ej: Matemáticas"
              sx={{ gridColumn: '1 / -1' }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)} className="admin-button admin-button-secondary">
            Cancelar
          </Button>
          <Button variant="contained" onClick={handleCreate} className="admin-button admin-button-primary">
            Crear Docente
          </Button>
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

export default AdminTeachers;
