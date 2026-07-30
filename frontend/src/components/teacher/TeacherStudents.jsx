// src/components/teacher/TeacherStudents.jsx
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
  CircularProgress,
  Alert,
} from '@mui/material';
import { teachersAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import './teacher-dashboard.css';

const TeacherStudents = () => {
  const { user } = useAuth();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user?.related_id) {
      loadStudents();
    }
  }, [user]);

  const loadStudents = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await teachersAPI.getStudents(user.related_id);
      setStudents(data);
    } catch (err) {
      console.error('Error cargando estudiantes:', err);
      setError('Error al cargar estudiantes. Por favor, intenta de nuevo.');
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
        Mis Estudiantes
      </Typography>

      {error && (
        <Alert severity="error" className="teacher-alert" onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper} className="teacher-table-container">
        <Table className="teacher-table">
          <TableHead className="teacher-table-head">
            <TableRow>
              <TableCell className="teacher-table-head-cell">DNI</TableCell>
              <TableCell className="teacher-table-head-cell">Nombre</TableCell>
              <TableCell className="teacher-table-head-cell">Apellido</TableCell>
              <TableCell className="teacher-table-head-cell">Teléfono</TableCell>
              <TableCell className="teacher-table-head-cell">Apoderado</TableCell>
              <TableCell className="teacher-table-head-cell">Teléfono Apoderado</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {students.map((student) => (
              <TableRow key={student.id} className="teacher-table-row">
                <TableCell className="teacher-table-cell">{student.dni}</TableCell>
                <TableCell className="teacher-table-cell">
                  <Typography variant="subtitle2" fontWeight="bold">
                    {student.first_name}
                  </Typography>
                </TableCell>
                <TableCell className="teacher-table-cell">
                  <Typography variant="subtitle2" fontWeight="bold">
                    {student.last_name}
                  </Typography>
                </TableCell>
                <TableCell className="teacher-table-cell">{student.phone || '-'}</TableCell>
                <TableCell className="teacher-table-cell">{student.parent_name || '-'}</TableCell>
                <TableCell className="teacher-table-cell">{student.parent_phone || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {students.length === 0 && (
          <Box className="teacher-empty-state">
            <Typography className="teacher-empty-state-text">
              No tienes estudiantes asignados
            </Typography>
          </Box>
        )}
      </TableContainer>
    </Box>
  );
};

export default TeacherStudents;

