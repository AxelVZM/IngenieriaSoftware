// src/components/admin/AdminUsers.jsx
import React, { useEffect, useState } from "react";
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
  TextField,
  InputAdornment,
  Chip,
  MenuItem,
} from "@mui/material";
import { Search as SearchIcon } from "@mui/icons-material";
import { studentsAPI, teachersAPI } from "../../services/api";
import "./admin-dashboard.css";

const AdminUsers = () => {
  // Fix BG-U4: antes esta pantalla se llamaba "Usuarios Registrados" pero
  // solo consultaba studentsAPI.getAll(), nunca docentes. Ahora combina
  // ambos roles en una sola lista, que es lo que el nombre de la pantalla
  // sugiere. (No se incluye "admin" porque el sistema no expone un
  // endpoint para listar administradores).
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");

  const fetchUsers = async () => {
    try {
      const [students, teachers] = await Promise.all([
        studentsAPI.getAll(),
        teachersAPI.getAll(),
      ]);

      const studentRows = (students || []).map((s) => ({
        id: `student-${s.id}`,
        dni: s.dni,
        name: `${s.first_name} ${s.last_name}`,
        phone: s.phone,
        role: "Estudiante",
      }));

      const teacherRows = (teachers || []).map((t) => ({
        id: `teacher-${t.id}`,
        dni: t.dni,
        name: t.name || `${t.first_name} ${t.last_name}`,
        phone: t.phone,
        role: "Docente",
      }));

      setUsers([...studentRows, ...teacherRows]);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const getFilteredUsers = () => {
    let result = users;

    if (roleFilter !== "all") {
      result = result.filter((u) => u.role === roleFilter);
    }

    if (searchQuery) {
      result = result.filter(
        (u) =>
          u.dni?.includes(searchQuery) ||
          u.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          u.phone?.includes(searchQuery)
      );
    }

    return result;
  };

  return (
    <Box className="admin-dashboard">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" className="admin-dashboard-title">
          Usuarios Registrados
        </Typography>
      </Box>

      <Box mb={3} className="admin-filters" sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
        <TextField
          select
          label="Rol"
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          size="small"
          sx={{ minWidth: 180 }}
          className="admin-input admin-select"
        >
          <MenuItem value="all">Todos</MenuItem>
          <MenuItem value="Estudiante">Estudiantes</MenuItem>
          <MenuItem value="Docente">Docentes</MenuItem>
        </TextField>
        <TextField
          fullWidth
          placeholder="Buscar por DNI, nombre o teléfono..."
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
          sx={{ flex: 1 }}
        />
      </Box>

      <TableContainer component={Paper} className="admin-table-container">
        <Table className="admin-table">
          <TableHead className="admin-table-head">
            <TableRow>
              <TableCell className="admin-table-head-cell">DNI</TableCell>
              <TableCell className="admin-table-head-cell">Nombre</TableCell>
              <TableCell className="admin-table-head-cell">Teléfono</TableCell>
              <TableCell className="admin-table-head-cell">Rol</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {getFilteredUsers().map((u) => (
              <TableRow key={u.id} className="admin-table-row">
                <TableCell className="admin-table-cell">{u.dni}</TableCell>
                <TableCell className="admin-table-cell">
                  <Typography variant="subtitle2" fontWeight="bold">
                    {u.name}
                  </Typography>
                </TableCell>
                <TableCell className="admin-table-cell">{u.phone}</TableCell>
                <TableCell className="admin-table-cell">
                  <Chip
                    label={u.role}
                    size="small"
                    color={u.role === "Docente" ? "primary" : "default"}
                  />
                </TableCell>
              </TableRow>
            ))}
            {getFilteredUsers().length === 0 && (
              <TableRow>
                <TableCell colSpan={4} align="center" sx={{ py: 3 }}>
                  <Typography color="text.secondary">
                    {searchQuery ? "No se encontraron usuarios" : "No hay usuarios registrados"}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default AdminUsers;