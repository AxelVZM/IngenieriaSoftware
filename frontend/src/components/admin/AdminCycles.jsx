// src/components/admin/AdminCycles.jsx
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
  MenuItem,
  IconButton,
  Chip,
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { cyclesAPI } from '../../services/api';
import './admin-dashboard.css';
import { useDialog } from '../../hooks/useDialog';
import DialogWrapper from '../common/DialogWrapper';

const AdminCycles = () => {
  const [cycles, setCycles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingCycle, setEditingCycle] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    start_date: '',
    end_date: '',
    duration_months: '',
    status: 'open',
  });

  const { confirmDialog, alertDialog, showConfirm, showAlert, closeConfirm, closeAlert } = useDialog();

  useEffect(() => {
    loadCycles();
  }, []);

  const loadCycles = async () => {
    try {
      setLoading(true);
      const data = await cyclesAPI.getAll();
      setCycles(data);
    } catch (err) {
      console.error('Error cargando ciclos:', err);
      showAlert('Error al cargar ciclos', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (cycle = null) => {
    if (cycle) {
      setEditingCycle(cycle);
      setFormData({
        name: cycle.name || '',
        start_date: cycle.start_date || '',
        end_date: cycle.end_date || '',
        duration_months: cycle.duration_months || '',
        status: cycle.status || 'open',
      });
    } else {
      setEditingCycle(null);
      setFormData({
        name: '',
        start_date: '',
        end_date: '',
        duration_months: '',
        status: 'open',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingCycle(null);
  };

  const handleSubmit = async () => {
    try {
      if (editingCycle) {
        await cyclesAPI.update(editingCycle.id, formData);
      } else {
        await cyclesAPI.create(formData);
      }
      handleCloseDialog();
      loadCycles();
    } catch (err) {
      console.error('Error guardando ciclo:', err);
      showAlert(err.message || 'Error al guardar ciclo', 'error');
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm({
      title: '¿Eliminar ciclo?',
      message: 'Esta acción no se puede deshacer. Todos los datos asociados a este ciclo se perderán.',
      type: 'error',
      confirmText: 'Eliminar'
    });
    if (!confirmed) return;

    try {
      await cyclesAPI.delete(id);
      showAlert('Ciclo eliminado exitosamente', 'success');
      loadCycles();
    } catch (err) {
      console.error('Error eliminando ciclo:', err);
      showAlert(err.message || 'Error al eliminar ciclo', 'error');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open':
        return 'success';
      case 'in_progress':
        return 'info';
      case 'closed':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'open':
        return 'Abierto';
      case 'in_progress':
        return 'En Progreso';
      case 'closed':
        return 'Cerrado';
      default:
        return status;
    }
  };

  return (
    <Box className="admin-dashboard">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" className="admin-dashboard-title">Gestión de Ciclos</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          className="admin-button admin-button-primary"
        >
          Nuevo Ciclo
        </Button>
      </Box>

      <TableContainer component={Paper} className="admin-table-container">
        <Table className="admin-table">
          <TableHead className="admin-table-head">
            <TableRow>
              <TableCell className="admin-table-head-cell">Nombre</TableCell>
              <TableCell className="admin-table-head-cell">Fecha Inicio</TableCell>
              <TableCell className="admin-table-head-cell">Fecha Fin</TableCell>
              <TableCell className="admin-table-head-cell">Duración (meses)</TableCell>
              <TableCell className="admin-table-head-cell">Estado</TableCell>
              <TableCell className="admin-table-head-cell">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {cycles.map((cycle) => (
              <TableRow key={cycle.id} className="admin-table-row">
                <TableCell className="admin-table-cell">{cycle.name}</TableCell>
                <TableCell className="admin-table-cell">{new Date(cycle.start_date).toLocaleDateString()}</TableCell>
                <TableCell className="admin-table-cell">{new Date(cycle.end_date).toLocaleDateString()}</TableCell>
                <TableCell className="admin-table-cell">{cycle.duration_months || '-'}</TableCell>
                <TableCell className="admin-table-cell">
                  <Chip
                    label={getStatusLabel(cycle.status)}
                    color={getStatusColor(cycle.status)}
                    size="small"
                    className="admin-chip"
                  />
                </TableCell>
                <TableCell className="admin-table-cell">
                  <IconButton size="small" onClick={() => handleOpenDialog(cycle)} className="admin-icon-button">
                    <EditIcon />
                  </IconButton>
                  <IconButton size="small" color="error" onClick={() => handleDelete(cycle.id)} className="admin-icon-button">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {cycles.length === 0 && !loading && (
          <Box p={3} textAlign="center">
            <Typography color="textSecondary">No hay ciclos registrados</Typography>
          </Box>
        )}
      </TableContainer>

      {/* Dialog para crear/editar */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingCycle ? 'Editar Ciclo' : 'Nuevo Ciclo'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              label="Nombre del Ciclo"
              fullWidth
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="admin-input"
              placeholder="Ej: Ciclo 2024-1"
            />
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField
                label="Fecha Inicio"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                inputProps={{
                  style: { cursor: 'pointer' },
                  onClick: (e) => e.target.showPicker && e.target.showPicker()
                }}
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="admin-input cursor-pointer"
                helperText="Haz clic para seleccionar la fecha"
                onClick={(e) => {
                  const input = e.target.querySelector('input');
                  if (input && input.showPicker) input.showPicker();
                }}
              />
              <TextField
                label="Fecha Fin"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                inputProps={{
                  style: { cursor: 'pointer' },
                  min: formData.start_date || undefined,
                  onClick: (e) => e.target.showPicker && e.target.showPicker()
                }}
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="admin-input cursor-pointer"
                helperText="Haz clic para seleccionar la fecha"
                onClick={(e) => {
                  const input = e.target.querySelector('input');
                  if (input && input.showPicker) input.showPicker();
                }}
              />
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField
                label="Duración (meses)"
                type="number"
                fullWidth
                value={formData.duration_months}
                onChange={(e) => setFormData({ ...formData, duration_months: e.target.value })}
                className="admin-input"
                placeholder="Ej: 6"
              />
              <TextField
                label="Estado"
                select
                fullWidth
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="admin-input admin-select"
              >
                <MenuItem value="open">Abierto</MenuItem>
                <MenuItem value="in_progress">En Progreso</MenuItem>
                <MenuItem value="closed">Cerrado</MenuItem>
              </TextField>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} className="admin-button admin-button-secondary">Cancelar</Button>
          <Button onClick={handleSubmit} variant="contained" className="admin-button admin-button-primary">
            {editingCycle ? 'Actualizar' : 'Crear'}
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

export default AdminCycles;

