// src/components/admin/AdminStudents.jsx
import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Table,
  TableContainer,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TextField,
  MenuItem,
  Button,
  Divider,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  InputAdornment,
} from "@mui/material";
import {
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from "@mui/icons-material";
import {
  coursesAPI,
  packagesAPI,
  enrollmentsAPI,
  studentsAPI,
} from "../../services/api";
import "./admin-dashboard.css";
import { useDialog } from "../../hooks/useDialog";
import DialogWrapper from "../common/DialogWrapper";

const emptyForm = {
  first_name: "",
  last_name: "",
  dni: "",
  phone: "",
  parent_name: "",
  parent_phone: "",
};

const AdminStudents = () => {
  // Fix BG-U6: 'students' ahora SI se usa y se muestra por defecto.
  const [students, setStudents] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");

  const [filterType, setFilterType] = useState("course");
  const [courseOfferings, setCourseOfferings] = useState([]);
  const [packageOfferings, setPackageOfferings] = useState([]);
  const [selectedOfferingId, setSelectedOfferingId] = useState("");
  const [filteredStudents, setFilteredStudents] = useState(null); // null = sin filtro aplicado

  // Fix BG-U3: estado para edicion
  const [openDialog, setOpenDialog] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);

  const { confirmDialog, alertDialog, showConfirm, showAlert, closeConfirm, closeAlert } = useDialog();

  const fetchStudents = async () => {
    try {
      const data = await studentsAPI.getAll();
      setStudents(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchOfferingsData = async () => {
    try {
      const courses = await coursesAPI.getAll();
      const co = [];
      (courses || []).forEach((c) => {
        (c.offerings || []).forEach((o) => {
          co.push({
            id: o.id,
            label: `${c.name} - ${o.cycle_name || ""} ${
              o.group_label ? "(" + o.group_label + ")" : ""
            }`.trim(),
          });
        });
      });
      setCourseOfferings(co);

      const poRaw = await packagesAPI.getOfferings();
      const po = (poRaw || []).map((o) => ({
        id: o.id,
        label: `${o.package_name || ""} - ${o.cycle_name || ""} ${
          o.group_label ? "(" + o.group_label + ")" : ""
        }`.trim(),
      }));
      setPackageOfferings(po);
    } catch (err) {
      console.error("Error cargando ofertas", err);
    }
  };

  const applyFilter = async () => {
    try {
      if (!selectedOfferingId) return setFilteredStudents(null);
      const data = await enrollmentsAPI.getByOffering(
        filterType,
        selectedOfferingId,
        "aceptado"
      );
      setFilteredStudents(data || []);
    } catch (err) {
      console.error("Error filtrando estudiantes", err);
      setFilteredStudents([]);
    }
  };

  const clearFilter = () => {
    setSelectedOfferingId("");
    setFilteredStudents(null);
  };

  useEffect(() => {
    fetchStudents();
    fetchOfferingsData();
  }, []);

  const handleOpenCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setOpenDialog(true);
  };

  const handleOpenEdit = (student) => {
    setEditingId(student.id);
    setForm({
      first_name: student.first_name || "",
      last_name: student.last_name || "",
      dni: student.dni || "",
      phone: student.phone || "",
      parent_name: student.parent_name || "",
      parent_phone: student.parent_phone || "",
    });
    setOpenDialog(true);
  };

  const handleSave = async () => {
    try {
      // El DNI no se reenvia en la edicion: es el identificador del
      // estudiante y no deberia cambiar desde este formulario.
      const { dni, ...updateData } = form;
      await studentsAPI.update(editingId, updateData);
      showAlert("Estudiante actualizado exitosamente", "success");
      setOpenDialog(false);
      setForm(emptyForm);
      setEditingId(null);
      await fetchStudents();
    } catch (err) {
      showAlert(err.message || "Error al actualizar estudiante", "error");
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm({
      title: "¿Eliminar estudiante?",
      message: "Esta acción eliminará permanentemente al estudiante del sistema.",
      type: "error",
      confirmText: "Eliminar",
    });
    if (!confirmed) return;

    try {
      await studentsAPI.delete(id);
      showAlert("Estudiante eliminado exitosamente", "success");
      await fetchStudents();
    } catch (err) {
      // Fix BG-U5 en accion: si el estudiante tiene matriculas/asistencias,
      // el backend responde 409 con un mensaje claro que se muestra aqui.
      showAlert(err.message || "Error al eliminar estudiante", "error");
    }
  };

  const getFilteredBySearch = () => {
    if (!searchQuery) return students;
    return students.filter(
      (s) =>
        s.dni?.includes(searchQuery) ||
        s.first_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.last_name?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  // Si hay un filtro de oferta aplicado, se muestra ese resultado.
  // Si no, se muestra la lista completa de estudiantes (fix BG-U6).
  const rowsToShow = filteredStudents !== null ? filteredStudents : getFilteredBySearch();

  return (
    <Box className="admin-dashboard">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" className="admin-dashboard-title">
          Estudiantes Matriculados
        </Typography>
      </Box>

      <Paper sx={{ p: 3, mb: 3 }} className="admin-filters">
        <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
          Filtrar estudiantes por oferta (opcional)
        </Typography>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center", flexWrap: "wrap" }}>
          <TextField
            select
            label="Tipo"
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value);
              clearFilter();
            }}
            size="small"
            className="admin-input admin-select"
          >
            <MenuItem value="course">Curso</MenuItem>
            <MenuItem value="package">Paquete</MenuItem>
          </TextField>
          <TextField
            select
            label={filterType === "course" ? "Oferta de curso" : "Oferta de paquete"}
            value={selectedOfferingId}
            onChange={(e) => setSelectedOfferingId(e.target.value)}
            size="small"
            sx={{ minWidth: 320 }}
            className="admin-input admin-select"
          >
            {(filterType === "course" ? courseOfferings : packageOfferings).map((o) => (
              <MenuItem key={o.id} value={o.id}>
                {o.label}
              </MenuItem>
            ))}
          </TextField>
          <Button variant="contained" onClick={applyFilter} className="admin-button admin-button-primary">
            Aplicar Filtro
          </Button>
          {filteredStudents !== null && (
            <Button variant="outlined" onClick={clearFilter} className="admin-button admin-button-secondary">
              Quitar Filtro
            </Button>
          )}
        </Box>
      </Paper>

      <Box mb={3} className="admin-filters">
        <TextField
          fullWidth
          placeholder="Buscar por DNI o nombre..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          disabled={filteredStudents !== null}
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

      <Divider sx={{ mb: 3 }} />
      <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
        {filteredStudents !== null ? "Resultados del Filtro" : `Todos los Estudiantes (${rowsToShow.length})`}
      </Typography>

      <TableContainer component={Paper} variant="outlined" className="admin-table-container">
        <Table className="admin-table">
          <TableHead className="admin-table-head">
            <TableRow>
              <TableCell className="admin-table-head-cell">DNI</TableCell>
              <TableCell className="admin-table-head-cell">Nombre Completo</TableCell>
              <TableCell className="admin-table-head-cell">Teléfono</TableCell>
              {filteredStudents === null && (
                <TableCell className="admin-table-head-cell">Acciones</TableCell>
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {rowsToShow.map((s) => (
              <TableRow key={s.enrollment_id || s.id} className="admin-table-row">
                <TableCell className="admin-table-cell">{s.dni}</TableCell>
                <TableCell className="admin-table-cell">
                  <Typography variant="subtitle2" fontWeight="bold">
                    {s.first_name} {s.last_name}
                  </Typography>
                </TableCell>
                <TableCell className="admin-table-cell">{s.phone}</TableCell>
                {filteredStudents === null && (
                  <TableCell className="admin-table-cell">
                    <Tooltip title="Editar estudiante">
                      <IconButton size="small" onClick={() => handleOpenEdit(s)} className="admin-icon-button">
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <IconButton size="small" color="error" onClick={() => handleDelete(s.id)} className="admin-icon-button">
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                )}
              </TableRow>
            ))}
            {rowsToShow.length === 0 && (
              <TableRow>
                <TableCell colSpan={filteredStudents === null ? 4 : 2} align="center" sx={{ py: 3 }}>
                  <Typography color="text.secondary">Sin resultados</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth className="admin-dialog">
        <DialogTitle>Editar Estudiante</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 3, pt: 2 }}>
            <TextField
              label="Nombres"
              value={form.first_name}
              onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              fullWidth
              className="admin-input"
            />
            <TextField
              label="Apellidos"
              value={form.last_name}
              onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              fullWidth
              className="admin-input"
            />
            <TextField
              label="DNI"
              value={form.dni}
              fullWidth
              disabled
              className="admin-input"
              helperText="El DNI no se puede modificar"
            />
            <TextField
              label="Teléfono"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              fullWidth
              className="admin-input"
            />
            <TextField
              label="Nombre del Apoderado"
              value={form.parent_name}
              onChange={(e) => setForm({ ...form, parent_name: e.target.value })}
              fullWidth
              className="admin-input"
              sx={{ gridColumn: "1 / -1" }}
            />
            <TextField
              label="Teléfono del Apoderado"
              value={form.parent_phone}
              onChange={(e) => setForm({ ...form, parent_phone: e.target.value })}
              fullWidth
              className="admin-input"
              sx={{ gridColumn: "1 / -1" }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)} className="admin-button admin-button-secondary">
            Cancelar
          </Button>
          <Button variant="contained" onClick={handleSave} className="admin-button admin-button-primary">
            Guardar Cambios
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

export default AdminStudents;