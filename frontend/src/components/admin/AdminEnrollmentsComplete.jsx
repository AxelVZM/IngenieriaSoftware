// src/components/admin/AdminEnrollmentsComplete.jsx
import React, { useEffect, useState } from 'react';
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
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
} from '@mui/material';
import {
  Check as CheckIcon,
  Close as CloseIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { enrollmentsAPI } from '../../services/api';
import './admin-dashboard.css';

const AdminEnrollmentsComplete = () => {
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter] = useState('aceptado');

  useEffect(() => {
    loadEnrollments();
  }, []);

  const loadEnrollments = async () => {
    try {
      setLoading(true);
      const data = await enrollmentsAPI.getAllAdmin();
      setEnrollments(data);
    } catch (err) {
      console.error('Error cargando matrículas:', err);
      alert('Error al cargar matrículas');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (enrollmentId, status) => {
    try {
      await enrollmentsAPI.updateStatus(enrollmentId, status);
      alert(`Matrícula ${status} correctamente`);
      loadEnrollments();
    } catch (err) {
      alert(err.message || 'Error al actualizar estado');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'aceptado':
        return 'success';
      case 'pendiente':
        return 'warning';
      case 'rechazado':
        return 'error';
      case 'cancelado':
        return 'default';
      default:
        return 'default';
    }
  };

  const filteredEnrollments = enrollments.filter(e => e.status === 'aceptado');

  return (
    <Box className="admin-dashboard">
      <Typography variant="h4" gutterBottom className="admin-dashboard-title">
        Gestión de Matrículas
      </Typography>

      {/* Vista solo de matrículas aceptadas por pago */}

      <TableContainer component={Paper} className="admin-table-container">
        <Table className="admin-table">
          <TableHead className="admin-table-head">
            <TableRow>
              <TableCell className="admin-table-head-cell">Estudiante</TableCell>
              <TableCell className="admin-table-head-cell">DNI</TableCell>
              <TableCell className="admin-table-head-cell">Curso/Paquete</TableCell>
              <TableCell className="admin-table-head-cell">Tipo</TableCell>
              <TableCell className="admin-table-head-cell">Estado</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredEnrollments.map((enrollment) => (
              <TableRow key={enrollment.id} className="admin-table-row">
                <TableCell className="admin-table-cell">
                  <Typography variant="subtitle2" fontWeight="bold">
                    {enrollment.first_name} {enrollment.last_name}
                  </Typography>
                </TableCell>
                <TableCell className="admin-table-cell">{enrollment.dni}</TableCell>
                <TableCell className="admin-table-cell">{enrollment.item_name || '-'}</TableCell>
                <TableCell className="admin-table-cell">
                  {enrollment.enrollment_type === 'course' ? 'Curso' : enrollment.enrollment_type === 'package' ? 'Paquete' : enrollment.enrollment_type}
                </TableCell>
                <TableCell className="admin-table-cell">
                  <Chip
                    label="Aceptado"
                    color={getStatusColor(enrollment.status)}
                    size="small"
                    className="admin-chip"
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {filteredEnrollments.length === 0 && (
          <Box p={3} textAlign="center">
            <Typography color="textSecondary">No hay matrículas</Typography>
          </Box>
        )}
      </TableContainer>
    </Box>
  );
};

export default AdminEnrollmentsComplete;

