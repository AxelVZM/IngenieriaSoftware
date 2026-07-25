// src/components/admin/AdminPackages.jsx
import React, { useEffect, useState } from "react";
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
  TextField,
  Button,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  InputAdornment,
  Chip,
} from "@mui/material";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Edit as EditIcon,
} from "@mui/icons-material";
import { packagesAPI, cyclesAPI, coursesAPI } from "../../services/api";
import { Checkbox, ListItemText } from "@mui/material";
import { MenuItem } from "@mui/material";
import { useDialog } from '../../hooks/useDialog';
import DialogWrapper from '../common/DialogWrapper';
import "./admin-dashboard.css";

const AdminPackages = () => {
  const [packages, setPackages] = useState([]);
  const [offerings, setOfferings] = useState([]);
  const [editing, setEditing] = useState({});
  const [tabValue, setTabValue] = useState(0);
  const [openPackageDialog, setOpenPackageDialog] = useState(false);
  const [packageForm, setPackageForm] = useState({
    name: "",
    description: "",
    base_price: "",
  });
  const [openOfferingDialog, setOpenOfferingDialog] = useState(false);
  const [cycles, setCycles] = useState([]);
  const [offeringForm, setOfferingForm] = useState({
    package_id: "",
    cycle_id: "",
  });
  const [courses, setCourses] = useState([]);
  const [openAssignDialog, setOpenAssignDialog] = useState(false);
  const [assignForm, setAssignForm] = useState({
    package_id: "",
    course_id: "",
  });

  // Manage mapping: package_offering -> course_offerings
  const [openOfferingCoursesDialog, setOpenOfferingCoursesDialog] =
    useState(false);
  const [selectedPackageOffering, setSelectedPackageOffering] = useState(null);
  const [availableCourseOfferings, setAvailableCourseOfferings] = useState([]);
  const [selectedCourseOfferingIds, setSelectedCourseOfferingIds] = useState(
    []
  );
  const [currentOfferingCourses, setCurrentOfferingCourses] = useState([]);

  // Search state
  const [searchQuery, setSearchQuery] = useState("");

  // Dialog hook
  const { confirmDialog, alertDialog, showConfirm, showAlert, closeConfirm, closeAlert } = useDialog();

  const fetchPackages = async () => {
    try {
      const data = await packagesAPI.getAll();
      setPackages(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchOfferings = async () => {
    try {
      const data = await packagesAPI.getOfferings();
      setOfferings(data || []);
    } catch (err) {
      console.error("Error fetching package offerings", err);
    }
  };

  const fetchCycles = async () => {
    try {
      const data = await cyclesAPI.getAll();
      setCycles(data || []);
    } catch (err) {
      console.error("Error loading cycles", err);
    }
  };

  const fetchCourses = async () => {
    try {
      const data = await coursesAPI.getAll();
      setCourses(data || []);
    } catch (err) {
      console.error("Error loading courses", err);
    }
  };

  useEffect(() => {
    fetchPackages();
    fetchOfferings();
    fetchCycles();
    fetchCourses();
  }, []);

  const startEdit = (p) => setEditing({ ...p });
  const save = async (id) => {
    try {
      await packagesAPI.update(id, editing);
      setEditing({});
      fetchPackages();
    } catch (err) {
      console.error(err);
    }
  };

  const remove = async (id) => {
    const confirmed = await showConfirm({
      title: '¿Eliminar paquete?',
      message: 'Esta acción no se puede deshacer. El paquete será eliminado permanentemente.',
      type: 'error',
      confirmText: 'Eliminar'
    });
    if (!confirmed) return;
    try {
      await packagesAPI.delete(id);
      fetchPackages();
      showAlert('Paquete eliminado exitosamente', 'success');
    } catch (err) {
      console.error(err);
      showAlert(err.message || 'No se pudo eliminar el paquete', 'error');
    }
  };

  const handleCreatePackage = async () => {
    try {
      const created = await packagesAPI.create(packageForm);
      const newId = created?.id;
      setOpenPackageDialog(false);
      setPackageForm({ name: "", description: "", base_price: "" });
      await fetchPackages();
    } catch (err) {
      console.error("Error creating package", err);
      alert(err.message || "Error al crear paquete");
    }
  };

  const openAssignForPackage = (pkg) => {
    setAssignForm({ package_id: pkg.id, course_id: "" });
    setOpenAssignDialog(true);
  };

  const handleAssignCourse = async () => {
    try {
      if (!assignForm.package_id || !assignForm.course_id)
        return alert("Selecciona paquete y curso");
      await packagesAPI.addCourse(assignForm.package_id, assignForm.course_id);
      setOpenAssignDialog(false);
      setAssignForm({ package_id: "", course_id: "" });
      await fetchPackages();
    } catch (err) {
      console.error("Error asignando curso", err);
      alert(err.message || "Error al asignar curso");
    }
  };

  const handleRemoveCourse = async () => {
    try {
      if (!assignForm.package_id || !assignForm.course_id)
        return alert("Selecciona paquete y curso");
      await packagesAPI.removeCourse(
        assignForm.package_id,
        assignForm.course_id
      );
      setOpenAssignDialog(false);
      setAssignForm({ package_id: "", course_id: "" });
      await fetchPackages();
    } catch (err) {
      console.error("Error removiendo curso", err);
      alert(err.message || "Error al remover curso");
    }
  };

  const handleCreateOffering = async () => {
    try {
      // No price_override ni capacity para ofertas de paquetes
      const payload = {
        package_id: offeringForm.package_id,
        cycle_id: offeringForm.cycle_id,
      };
      await packagesAPI.createOffering(payload);
      setOpenOfferingDialog(false);
      setOfferingForm({ package_id: "", cycle_id: "" });
      await fetchOfferings();
    } catch (err) {
      console.error("Error creating package offering", err);
      alert(err.message || "Error al crear oferta de paquete");
    }
  };

  const handleDeleteOffering = async (id) => {
    const confirmed = await showConfirm({
      title: '¿Eliminar oferta de paquete?',
      message: 'Esta acción no se puede deshacer. La oferta será eliminada permanentemente.',
      type: 'error',
      confirmText: 'Eliminar'
    });
    if (!confirmed) return;
    try {
      await packagesAPI.deleteOffering(id);
      await fetchOfferings();
      showAlert('Oferta eliminada exitosamente', 'success');
    } catch (err) {
      console.error("Error deleting offering", err);
      showAlert(err.message || 'No se pudo eliminar la oferta', 'error');
    }
  };

  const openManageOfferingCourses = async (off) => {
    try {
      setSelectedPackageOffering(off);
      setOpenOfferingCoursesDialog(true);
      // Flatten course offerings filtered by cycle of the package offering
      const cycleId = off.cycle_id;
      const flattened = [];
      for (const c of courses) {
        const offs = Array.isArray(c.offerings) ? c.offerings : [];
        for (const co of offs) {
          if (!cycleId || co.cycle_id === cycleId) {
            flattened.push({
              id: co.id,
              label: `${c.name} · ${co.group_label || "Grupo"}${co.first_name ? " · " + co.first_name + " " + co.last_name : ""
                }`,
            });
          }
        }
      }
      setAvailableCourseOfferings(flattened);
      // Load current mappings
      const mapped = await packagesAPI
        .getOfferingCourses(off.id)
        .catch(() => []);
      setCurrentOfferingCourses(mapped || []);
      setSelectedCourseOfferingIds(
        (mapped || []).map((m) => m.course_offering_id)
      );
    } catch (e) {
      console.error("Error opening manage offering courses", e);
    }
  };

  const saveOfferingCourses = async () => {
    if (!selectedPackageOffering) return;
    try {
      const mappedIds = new Set(
        (currentOfferingCourses || []).map((m) => m.course_offering_id)
      );
      // Add new selections
      for (const coId of selectedCourseOfferingIds) {
        if (!mappedIds.has(coId)) {
          await packagesAPI.addOfferingCourse(selectedPackageOffering.id, coId);
        }
      }
      // Remove unselected
      for (const m of currentOfferingCourses) {
        if (!selectedCourseOfferingIds.includes(m.course_offering_id)) {
          await packagesAPI.removeOfferingCourse(
            selectedPackageOffering.id,
            m.course_offering_id
          );
        }
      }
      setOpenOfferingCoursesDialog(false);
      setSelectedPackageOffering(null);
      setSelectedCourseOfferingIds([]);
      setCurrentOfferingCourses([]);
      await fetchOfferings();
    } catch (e) {
      console.error("Error saving offering courses", e);
      alert("Error guardando cursos de la oferta");
    }
  };

  const getFilteredPackages = () => {
    if (!searchQuery) return packages;
    return packages.filter(
      (p) =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.description &&
          p.description.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  };

  const getFilteredOfferings = () => {
    if (!searchQuery) return offerings;
    return offerings.filter(
      (o) =>
        (o.package_name &&
          o.package_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (o.cycle_name &&
          o.cycle_name.toLowerCase().includes(searchQuery.toLowerCase()))
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
          Gestión de Paquetes
        </Typography>
        <Box>
          {tabValue === 0 && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setOpenPackageDialog(true)}
              className="admin-button admin-button-primary"
            >
              Nuevo Paquete
            </Button>
          )}
          {tabValue === 1 && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setOpenOfferingDialog(true)}
              sx={{ ml: 1 }}
              className="admin-button admin-button-primary"
            >
              Nueva Oferta
            </Button>
          )}
        </Box>
      </Box>

      {/* Buscador Común */}
      <Box mb={3} className="admin-filters">
        <TextField
          fullWidth
          placeholder={
            tabValue === 0
              ? "Buscar paquetes..."
              : "Buscar ofertas de paquetes..."
          }
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
        onChange={(e, v) => {
          setTabValue(v);
          setSearchQuery("");
        }}
        sx={{ mb: 3 }}
        className="admin-tabs"
        TabIndicatorProps={{ className: "admin-tab-indicator" }}
      >
        <Tab label="Paquetes" className="admin-tab" />
        <Tab label="Ofertas" className="admin-tab" />
      </Tabs>

      {tabValue === 0 && (
        <TableContainer component={Paper} className="admin-table-container">
          <Table className="admin-table">
            <TableHead className="admin-table-head">
              <TableRow>
                <TableCell className="admin-table-head-cell">Nombre</TableCell>
                <TableCell className="admin-table-head-cell">
                  Precio base
                </TableCell>
                <TableCell className="admin-table-head-cell">
                  Descripción
                </TableCell>
                <TableCell className="admin-table-head-cell">
                  Acciones
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {getFilteredPackages().map((p) => (
                <TableRow key={p.id} className="admin-table-row">
                  <TableCell className="admin-table-cell">
                    <Typography variant="subtitle2" fontWeight="bold">
                      {p.name}
                    </Typography>
                  </TableCell>
                  <TableCell className="admin-table-cell">
                    {editing.id === p.id ? (
                      <TextField
                        size="small"
                        type="number"
                        value={editing.base_price}
                        onChange={(e) =>
                          setEditing({ ...editing, base_price: e.target.value })
                        }
                      />
                    ) : (
                      `S/. ${p.base_price}`
                    )}
                  </TableCell>
                  <TableCell className="admin-table-cell">
                    {editing.id === p.id ? (
                      <TextField
                        size="small"
                        value={editing.description || ""}
                        onChange={(e) =>
                          setEditing({
                            ...editing,
                            description: e.target.value,
                          })
                        }
                      />
                    ) : (
                      p.description || "-"
                    )}
                  </TableCell>
                  <TableCell className="admin-table-cell">
                    {editing.id === p.id ? (
                      <>
                        <Button size="small" onClick={() => save(p.id)}>
                          Guardar
                        </Button>
                        <Button size="small" onClick={() => setEditing({})}>
                          Cancelar
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          size="small"
                          onClick={() => startEdit(p)}
                          startIcon={<EditIcon />}
                        >
                          Editar
                        </Button>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => remove(p.id)}
                          className="admin-icon-button"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {getFilteredPackages().length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ py: 3 }}>
                    <Typography color="text.secondary">
                      No se encontraron paquetes
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {tabValue === 1 && (
        <Box>
          <TableContainer component={Paper} className="admin-table-container">
            <Table className="admin-table">
              <TableHead className="admin-table-head">
                <TableRow>
                  <TableCell className="admin-table-head-cell">
                    Paquete
                  </TableCell>
                  <TableCell className="admin-table-head-cell">Ciclo</TableCell>
                  <TableCell className="admin-table-head-cell">
                    Precio
                  </TableCell>
                  <TableCell className="admin-table-head-cell">
                    Acciones
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {getFilteredOfferings().map((o) => (
                  <TableRow key={o.id} className="admin-table-row">
                    <TableCell className="admin-table-cell">
                      {o.package_name || "-"}
                    </TableCell>
                    <TableCell className="admin-table-cell">
                      {o.cycle_name || "-"}
                    </TableCell>
                    <TableCell className="admin-table-cell">
                      S/. {parseFloat(o.base_price || 0).toFixed(2)}
                    </TableCell>
                    <TableCell className="admin-table-cell">
                      <Button
                        size="small"
                        onClick={() => openManageOfferingCourses(o)}
                        className="admin-button-text"
                      >
                        Cursos ofrecidos
                      </Button>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteOffering(o.id)}
                        className="admin-icon-button"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                {getFilteredOfferings().length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} align="center" sx={{ py: 3 }}>
                      <Typography color="text.secondary">
                        No se encontraron ofertas de paquetes
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Dialog: Crear Paquete */}
      <Dialog
        open={openPackageDialog}
        onClose={() => setOpenPackageDialog(false)}
        maxWidth="sm"
        fullWidth
        className="admin-dialog"
      >
        <DialogTitle>Nuevo Paquete</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 3, pt: 2 }}>
            <TextField
              label="Nombre del Paquete"
              value={packageForm.name}
              onChange={(e) =>
                setPackageForm({ ...packageForm, name: e.target.value })
              }
              fullWidth
              className="admin-input"
              placeholder="Ej: Pack Verano 2024"
            />
            <TextField
              label="Descripción"
              value={packageForm.description}
              onChange={(e) =>
                setPackageForm({ ...packageForm, description: e.target.value })
              }
              fullWidth
              className="admin-input"
              multiline
              rows={2}
            />
            <TextField
              label="Precio base (S/.)"
              type="number"
              value={packageForm.base_price}
              onChange={(e) =>
                setPackageForm({ ...packageForm, base_price: e.target.value })
              }
              fullWidth
              className="admin-input"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">S/.</InputAdornment>
                ),
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setOpenPackageDialog(false)}
            className="admin-button admin-button-secondary"
          >
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={handleCreatePackage}
            className="admin-button admin-button-primary"
          >
            Crear Paquete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Asignar/Quitar Cursos a Paquete */}
      <Dialog
        open={openAssignDialog}
        onClose={() => setOpenAssignDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Asignar o Quitar Curso</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
            <TextField
              select
              label="Paquete"
              value={assignForm.package_id}
              onChange={(e) =>
                setAssignForm({ ...assignForm, package_id: e.target.value })
              }
              fullWidth
            >
              {packages.map((p) => (
                <MenuItem key={p.id} value={p.id}>
                  {p.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Curso"
              value={assignForm.course_id}
              onChange={(e) =>
                setAssignForm({ ...assignForm, course_id: e.target.value })
              }
              fullWidth
            >
              {courses.map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.name}
                </MenuItem>
              ))}
            </TextField>
            <Typography variant="body2" color="text.secondary">
              Cursos actuales del paquete seleccionado:{" "}
              {packages.find((p) => p.id === assignForm.package_id)?.courses ||
                "-"}
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAssignDialog(false)}>Cerrar</Button>
          <Button onClick={handleRemoveCourse}>Quitar</Button>
          <Button variant="contained" onClick={handleAssignCourse}>
            Asignar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Crear Oferta de Paquete */}
      <Dialog
        open={openOfferingDialog}
        onClose={() => setOpenOfferingDialog(false)}
        maxWidth="sm"
        fullWidth
        className="admin-dialog"
      >
        <DialogTitle>Nueva Oferta de Paquete</DialogTitle>
        <DialogContent>
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 3,
              pt: 2,
            }}
          >
            <TextField
              select
              label="Paquete"
              value={offeringForm.package_id}
              onChange={(e) =>
                setOfferingForm({ ...offeringForm, package_id: e.target.value })
              }
              fullWidth
              className="admin-input admin-select"
            >
              {packages.map((p) => (
                <MenuItem key={p.id} value={p.id}>
                  {p.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Ciclo"
              value={offeringForm.cycle_id}
              onChange={(e) =>
                setOfferingForm({ ...offeringForm, cycle_id: e.target.value })
              }
              fullWidth
              className="admin-input admin-select"
            >
              {cycles.map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.name}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setOpenOfferingDialog(false)}
            className="admin-button admin-button-secondary"
          >
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={handleCreateOffering}
            className="admin-button admin-button-primary"
          >
            Crear
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Vincular course_offerings a una package_offering */}
      <Dialog
        open={openOfferingCoursesDialog}
        onClose={() => setOpenOfferingCoursesDialog(false)}
        maxWidth="sm"
        fullWidth
        className="admin-dialog"
      >
        <DialogTitle>Seleccionar cursos ofrecidos para el paquete</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2, color: "text.secondary" }}>
            Paquete: <strong>{selectedPackageOffering?.package_name}</strong> ·
            Ciclo: <strong>{selectedPackageOffering?.cycle_name}</strong>
          </Typography>
          <TextField
            label="Cursos Disponibles"
            select
            fullWidth
            SelectProps={{
              multiple: true,
              renderValue: (selected) => `${selected.length} seleccionados`,
            }}
            value={selectedCourseOfferingIds}
            onChange={(e) =>
              setSelectedCourseOfferingIds(
                typeof e.target.value === "string"
                  ? e.target.value.split(",").map(Number)
                  : e.target.value
              )
            }
            helperText="Selecciona los cursos que conforman este paquete"
            className="admin-input admin-select"
          >
            {availableCourseOfferings.map((opt) => (
              <MenuItem key={opt.id} value={opt.id}>
                <Checkbox
                  checked={selectedCourseOfferingIds.indexOf(opt.id) > -1}
                />
                <ListItemText primary={opt.label} />
              </MenuItem>
            ))}
          </TextField>
          {currentOfferingCourses && currentOfferingCourses.length > 0 && (
            <Box
              mt={2}
              p={2}
              bgcolor="background.paper"
              borderRadius={1}
              border="1px solid #eee"
            >
              <Typography
                variant="caption"
                color="text.secondary"
                fontWeight="bold"
              >
                Actualmente vinculados:
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
                {currentOfferingCourses.map((m) => (
                  <Chip
                    key={m.course_offering_id}
                    label={`ID: ${m.course_offering_id}`}
                    size="small"
                  />
                ))}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setOpenOfferingCoursesDialog(false)}
            className="admin-button admin-button-secondary"
          >
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={saveOfferingCourses}
            className="admin-button admin-button-primary"
          >
            Guardar
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

export default AdminPackages;
