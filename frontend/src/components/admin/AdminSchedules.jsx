import React, { useEffect, useState, useMemo } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  Chip,
  CircularProgress,
} from "@mui/material";
import {
  Delete as DeleteIcon,
  CalendarViewWeek as CalendarIcon,
  List as ListIcon,
  Add as AddIcon,
  Room as RoomIcon,
  School as SchoolIcon,
  Inventory2 as PackageIcon,
} from "@mui/icons-material";

import "./admin-dashboard.css";
import { useDialog } from "../../hooks/useDialog";
import DialogWrapper from "../common/DialogWrapper";
import { coursesAPI, packagesAPI, schedulesAPI } from "../../services/api";

const DAYS = [
  "Lunes",
  "Martes",
  "Miércoles",
  "Jueves",
  "Viernes",
  "Sábado",
  "Domingo",
];
const HOURS = Array.from({ length: 15 }, (_, i) => i + 7); // 7:00 - 21:00

// Paleta de colores para diferenciar cursos dentro de un paquete
const COURSE_COLORS = [
  { bg: "#e0f2fe", border: "#0284c7", text: "#0c4a6e" },
  { bg: "#dcfce7", border: "#16a34a", text: "#14532d" },
  { bg: "#fef9c3", border: "#ca8a04", text: "#713f12" },
  { bg: "#fee2e2", border: "#dc2626", text: "#7f1d1d" },
  { bg: "#f3e8ff", border: "#9333ea", text: "#581c87" },
  { bg: "#ffedd5", border: "#ea580c", text: "#7c2d12" },
];

const AdminSchedules = () => {
  // Estados de vista y filtro
  const [viewMode, setViewMode] = useState("calendar");
  const [filterType, setFilterType] = useState("course"); // 'course' | 'package'
  const [selectedFilterId, setSelectedFilterId] = useState("");

  // Data
  const [schedules, setSchedules] = useState([]);
  const [offerings, setOfferings] = useState([]); // Ofertas de Cursos
  const [packageOfferings, setPackageOfferings] = useState([]); // Ofertas de Paquetes
  const [loading, setLoading] = useState(false);

  // Modal y Formulario
  const [openDialog, setOpenDialog] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(null);
  const [formData, setFormData] = useState({
    course_offering_id: "",
    day_of_week: [],
    start_time: "",
    end_time: "",
    classroom: "",
  });

  const {
    confirmDialog,
    alertDialog,
    showConfirm,
    showAlert,
    closeConfirm,
    closeAlert,
  } = useDialog();

  // --- CARGA DE DATOS INICIALES (Listas para los selects) ---
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const dataCourses = await coursesAPI.getAll();
        const flatOfferings = [];
        dataCourses.forEach((c) => {
          if (c.offerings)
            c.offerings.forEach((o) => {
              flatOfferings.push({ ...o, course_name: c.name });
            });
        });
        setOfferings(flatOfferings);

        const dataPackages = await packagesAPI.getOfferings();
        setPackageOfferings(dataPackages);

        if (flatOfferings.length > 0) setSelectedFilterId(flatOfferings[0].id);
      } catch (err) {
        console.error("Error cargando datos base:", err);
      }
    };
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (!selectedFilterId) return;

    const fetchSchedules = async () => {
      setLoading(true);
      try {
        let data;
        if (filterType === "course") {
          data = await schedulesAPI.getByOffering(selectedFilterId);
        } else {
          data = await schedulesAPI.getByPackageOffering(selectedFilterId);
        }
        setSchedules(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchSchedules();
  }, [filterType, selectedFilterId]);

  // --- HANDLERS ---
  const handleOpen = (
    schedule = null,
    preSelectedDay = null,
    preSelectedTime = null
  ) => {
    if (schedule) {
      setEditingSchedule(schedule);
      setFormData({
        course_offering_id: schedule.course_offering_id,
        day_of_week: schedule.day_of_week,
        start_time: schedule.start_time,
        end_time: schedule.end_time,
        classroom: schedule.classroom,
      });
    } else {
      setEditingSchedule(null);
      // Si estamos en modo "Curso Individual", pre-seleccionamos ese curso en el form
      const defaultCourse = filterType === "course" ? selectedFilterId : "";

      setFormData({
        course_offering_id: defaultCourse,
        day_of_week: preSelectedDay
          ? (viewMode === "list" ? [preSelectedDay] : preSelectedDay)
          : (viewMode === "list" ? [] : ""),
        start_time: preSelectedTime || "",
        end_time: preSelectedTime ? calculateEndTime(preSelectedTime) : "",
        classroom: "",
      });
    }
    setOpenDialog(true);
  };

  const calculateEndTime = (startTime) => {
    const [h, m] = startTime.split(":").map(Number);
    const endH = h + 2;
    return `${endH.toString().padStart(2, "0")}:${m
      .toString()
      .padStart(2, "0")}`;
  };

  const handleClose = () => {
    setOpenDialog(false);
    setEditingSchedule(null);
    setFormData({
      course_offering_id: "",
      day_of_week: viewMode === "list" ? [] : "",
      start_time: "",
      end_time: "",
      classroom: "",
    });
  };

  const handleSubmit = async () => {
    try {
      if (
        !editingSchedule &&
        Array.isArray(formData.day_of_week) &&
        formData.day_of_week.length > 0
      ) {
        for (const day of formData.day_of_week) {
          await schedulesAPI.create({ ...formData, day_of_week: day });
        }
      } else if (editingSchedule) {
        await schedulesAPI.update(editingSchedule.id, formData);
      } else {
        await schedulesAPI.create(formData);
      }

      const currentId = selectedFilterId;
      setSelectedFilterId("");
      setTimeout(() => setSelectedFilterId(currentId), 50);
      handleClose();
    } catch (err) {
      console.error("Error al guardar");
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm({
      title: "¿Eliminar sesión?",
      message: "Esta acción eliminará permanentemente esta sesión de clase.",
      type: "error",
      confirmText: "Eliminar",
    });
    if (!confirmed) return;

    try {
      await schedulesAPI.delete(id);
      showAlert("Sesión eliminada exitosamente", "success");
      const currentId = selectedFilterId;
      setSelectedFilterId("");
      setTimeout(() => setSelectedFilterId(currentId), 50);
      if (openDialog) handleClose();
    } catch (err) {
      console.error(err);
      showAlert("Error al eliminar sesión", "error");
    }
  };

  // --- HELPERS ESTILO ---
  const getCourseColor = (courseName) => {
    let hash = 0;
    for (let i = 0; i < courseName.length; i++)
      hash = courseName.charCodeAt(i) + ((hash << 5) - hash);
    const index = Math.abs(hash) % COURSE_COLORS.length;
    return COURSE_COLORS[index];
  };

  const getPositionStyle = (startTime, endTime) => {
    const startParts = startTime.split(":").map(Number);
    const endParts = endTime.split(":").map(Number);
    const topPixels = startParts[1];
    const durationMinutes =
      endParts[0] * 60 + endParts[1] - (startParts[0] * 60 + startParts[1]);

    return {
      top: `${topPixels}px`,
      height: `${durationMinutes}px`,
    };
  };

  return (
    <Box
      className="admin-fade-in"
      sx={{ p: 3, maxWidth: "1600px", margin: "0 auto" }}
    >
      {/* HEADER Y FILTROS */}
      <Box sx={{ mb: 4 }}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 2,
          }}
        >
          <Typography className="admin-dashboard-title">
            Planificador Académico
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            className="admin-button-primary"
            onClick={() => handleOpen()}
          >
            Nueva Sesión
          </Button>
        </Box>

        {/* BARRA DE CONTROL PRINCIPAL */}
        <Paper
          sx={{
            p: 2,
            display: "flex",
            gap: 2,
            alignItems: "center",
            flexWrap: "wrap",
            borderRadius: 2,
          }}
        >
          {/* 1. Selector de TIPO (Curso vs Paquete) */}
          <ToggleButtonGroup
            color="primary"
            value={filterType}
            exclusive
            onChange={(e, newVal) => {
              if (!newVal) return;
              setFilterType(newVal);
              setSelectedFilterId(""); // Resetear selección al cambiar modo
            }}
            size="small"
          >
            <ToggleButton value="course">
              <SchoolIcon sx={{ mr: 1 }} /> Curso Individual
            </ToggleButton>
            <ToggleButton value="package">
              <PackageIcon sx={{ mr: 1 }} /> Ver por Paquete
            </ToggleButton>
          </ToggleButtonGroup>

          {/* 2. Dropdown Dinámico */}
          <FormControl size="small" sx={{ minWidth: 300, flexGrow: 1 }}>
            <InputLabel>
              {filterType === "course"
                ? "Seleccionar Curso"
                : "Seleccionar Paquete"}
            </InputLabel>
            <Select
              value={selectedFilterId}
              label={
                filterType === "course"
                  ? "Seleccionar Curso"
                  : "Seleccionar Paquete"
              }
              onChange={(e) => setSelectedFilterId(e.target.value)}
            >
              {filterType === "course"
                ? offerings.map((o) => (
                  <MenuItem key={o.id} value={o.id}>
                    {o.course_name} - {o.group_label} ({o.cycle_name})
                  </MenuItem>
                ))
                : packageOfferings.map((p) => (
                  <MenuItem key={p.id} value={p.id}>
                    <strong>{p.package_name}</strong> &nbsp; — {p.group_label}{" "}
                    ({p.cycle_name})
                  </MenuItem>
                ))}
            </Select>
          </FormControl>

          {/* 3. Selector de VISTA (Calendario vs Lista) */}
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newView) => {
              if (newView) setViewMode(newView);
            }}
            size="small"
          >
            <ToggleButton value="calendar">
              <CalendarIcon />
            </ToggleButton>
            <ToggleButton value="list">
              <ListIcon />
            </ToggleButton>
          </ToggleButtonGroup>
        </Paper>
      </Box>

      {/* LOADING STATE */}
      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", p: 5 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* --- VISTA CALENDARIO --- */}
          {viewMode === "calendar" && (
            <Paper
              className="calendar-container"
              sx={{ overflowX: "auto", p: 2, borderRadius: 3 }}
            >
              <div className="calendar-grid">
                <div className="calendar-header-cell time-col">Hora</div>
                {DAYS.map((day) => (
                  <div key={day} className="calendar-header-cell day-col">
                    {day}
                  </div>
                ))}

                {HOURS.map((hour) => (
                  <React.Fragment key={hour}>
                    <div className="calendar-time-cell">
                      {`${hour.toString().padStart(2, "0")}:00`}
                    </div>

                    {DAYS.map((day) => (
                      <div
                        key={`${day}-${hour}`}
                        className="calendar-cell"
                        onClick={() =>
                          handleOpen(
                            null,
                            day,
                            `${hour.toString().padStart(2, "0")}:00`
                          )
                        }
                      >
                        {schedules
                          .filter((s) => s.day_of_week === day)
                          .filter(
                            (s) => parseInt(s.start_time.split(":")[0]) === hour
                          )
                          .map((schedule) => {
                            const styles = getPositionStyle(
                              schedule.start_time,
                              schedule.end_time
                            );
                            const colors = getCourseColor(
                              schedule.course_name || "X"
                            );

                            return (
                              <div
                                key={schedule.id}
                                className="calendar-event admin-fade-in"
                                style={{
                                  ...styles,
                                  backgroundColor: colors.bg,
                                  borderLeft: `4px solid ${colors.border}`,
                                  color: colors.text,
                                }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleOpen(schedule);
                                }}
                                title={`${schedule.course_name} (${schedule.start_time} - ${schedule.end_time})`}
                              >
                                <div
                                  className="event-time"
                                  style={{ color: colors.border }}
                                >
                                  {schedule.start_time.slice(0, 5)} -{" "}
                                  {schedule.end_time.slice(0, 5)}
                                </div>
                                <div className="event-title">
                                  {schedule.course_name}
                                </div>
                                <div className="event-details">
                                  {schedule.classroom && (
                                    <span>Aula {schedule.classroom}</span>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    ))}
                  </React.Fragment>
                ))}
              </div>
            </Paper>
          )}

          {/* --- VISTA LISTA --- */}
          {viewMode === "list" && (
            <Paper className="admin-table-container">
              <table className="admin-table" style={{ width: "100%" }}>
                <thead className="admin-table-head">
                  <tr>
                    <th className="admin-table-head-cell">Curso</th>
                    <th className="admin-table-head-cell">Día</th>
                    <th className="admin-table-head-cell">Horario</th>
                    <th className="admin-table-head-cell">Aula</th>
                    <th className="admin-table-head-cell"></th>
                  </tr>
                </thead>
                <tbody>
                  {schedules.map((s) => (
                    <tr key={s.id} className="admin-table-row">
                      <td className="admin-table-cell font-bold">
                        {s.course_name}
                      </td>
                      <td className="admin-table-cell">{s.day_of_week}</td>
                      <td className="admin-table-cell">
                        {s.start_time.slice(0, 5)} - {s.end_time.slice(0, 5)}
                      </td>
                      <td className="admin-table-cell">{s.classroom}</td>
                      <td className="admin-table-cell">
                        <Button size="small" onClick={() => handleOpen(s)}>
                          Editar
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => handleDelete(s.id)}
                        >
                          Borrar
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {schedules.length === 0 && (
                    <tr>
                      <td
                        colSpan={5}
                        style={{ textAlign: "center", padding: 20 }}
                      >
                        No hay horarios asignados
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </Paper>
          )}
        </>
      )}

      {/* --- MODAL FORMULARIO --- */}
      <Dialog
        open={openDialog}
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
        className="admin-dialog"
      >
        <DialogTitle>
          {editingSchedule ? "Editar Sesión" : "Programar Clase"}
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Box
            component="form"
            sx={{ mt: 2, display: "flex", flexDirection: "column", gap: 2 }}
          >
            <FormControl fullWidth>
              <InputLabel>Curso a Programar</InputLabel>
              <Select
                value={formData.course_offering_id}
                label="Curso a Programar"
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    course_offering_id: e.target.value,
                  })
                }
              >
                {/* Si el filtro es "Paquete", aquí deberíamos mostrar SOLO los cursos de ese paquete.
                   Pero para simplificar, mostramos todos (o podrías filtrarlos si tienes esa data mapeada)
                */}
                {offerings.map((off) => (
                  <MenuItem key={off.id} value={off.id}>
                    {off.course_name} ({off.group_label})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box sx={{ display: "flex", gap: 2 }}>
              {!editingSchedule ? (
                <FormControl fullWidth>
                  <InputLabel>Día(s)</InputLabel>
                  <Select
                    multiple={viewMode === "list"}
                    value={formData.day_of_week}
                    label="Día(s)"
                    onChange={(e) =>
                      setFormData({ ...formData, day_of_week: e.target.value })
                    }
                    renderValue={(sel) =>
                      Array.isArray(sel) ? sel.join(", ") : sel
                    }
                  >
                    {DAYS.map((day) => (
                      <MenuItem key={day} value={day}>
                        {day}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              ) : (
                <TextField
                  fullWidth
                  label="Día"
                  value={formData.day_of_week}
                  disabled
                />
              )}
              <TextField
                fullWidth
                label="Aula"
                value={formData.classroom}
                onChange={(e) =>
                  setFormData({ ...formData, classroom: e.target.value })
                }
                InputProps={{
                  startAdornment: <RoomIcon color="action" sx={{ mr: 1 }} />,
                }}
              />
            </Box>
            <Box sx={{ display: "flex", gap: 2 }}>
              <TextField
                fullWidth
                label="Inicio"
                type="time"
                value={formData.start_time}
                onChange={(e) =>
                  setFormData({ ...formData, start_time: e.target.value })
                }
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                fullWidth
                label="Fin"
                type="time"
                value={formData.end_time}
                onChange={(e) =>
                  setFormData({ ...formData, end_time: e.target.value })
                }
                InputLabelProps={{ shrink: true }}
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          {editingSchedule && (
            <Button
              onClick={() => handleDelete(editingSchedule.id)}
              color="error"
              startIcon={<DeleteIcon />}
            >
              Eliminar
            </Button>
          )}
          <Button onClick={handleClose}>Cancelar</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            className="admin-button-primary"
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

export default AdminSchedules;
