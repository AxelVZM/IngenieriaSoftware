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
} from "@mui/material";
import { Search as SearchIcon } from "@mui/icons-material";
import { studentsAPI } from "../../services/api";
import "./admin-dashboard.css";

const AdminUsers = () => {
  const [students, setStudents] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");

  const fetchStudents = async () => {
    try {
      const data = await studentsAPI.getAll();
      setStudents(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, []);

  const getFilteredUsers = () => {
    if (!searchQuery) return students;
    return students.filter(
      (s) =>
        s.dni?.includes(searchQuery) ||
        s.first_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.last_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.phone?.includes(searchQuery)
    );
  };

  return (
    <Box className="admin-dashboard">
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography variant="h4" className="admin-dashboard-title">
          Usuarios Registrados
        </Typography>
      </Box>

      {/* Search Bar */}
      <Box mb={3} className="admin-filters">
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
        />
      </Box>

      <TableContainer component={Paper} className="admin-table-container">
        <Table className="admin-table">
          <TableHead className="admin-table-head">
            <TableRow>
              <TableCell className="admin-table-head-cell">DNI</TableCell>
              <TableCell className="admin-table-head-cell">Nombre</TableCell>
              <TableCell className="admin-table-head-cell">Teléfono</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {getFilteredUsers().map((s) => (
              <TableRow key={s.id} className="admin-table-row">
                <TableCell className="admin-table-cell">{s.dni}</TableCell>
                <TableCell className="admin-table-cell">
                  <Typography variant="subtitle2" fontWeight="bold">
                    {s.first_name} {s.last_name}
                  </Typography>
                </TableCell>
                <TableCell className="admin-table-cell">{s.phone}</TableCell>
              </TableRow>
            ))}
            {getFilteredUsers().length === 0 && (
              <TableRow>
                <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                  <Typography color="text.secondary">
                    {searchQuery
                      ? "No se encontraron usuarios"
                      : "No hay usuarios registrados"}
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
