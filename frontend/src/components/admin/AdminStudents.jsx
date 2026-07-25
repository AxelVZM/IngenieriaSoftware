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
  InputAdornment,
} from "@mui/material";
import { Search as SearchIcon } from "@mui/icons-material";
import {
  coursesAPI,
  packagesAPI,
  enrollmentsAPI,
  studentsAPI,
} from "../../services/api";
import "./admin-dashboard.css";

const AdminStudents = () => {
  const [students, setStudents] = useState([]);
  const [filterType, setFilterType] = useState("course");
  const [courseOfferings, setCourseOfferings] = useState([]);
  const [packageOfferings, setPackageOfferings] = useState([]);
  const [selectedOfferingId, setSelectedOfferingId] = useState("");
  const [filteredStudents, setFilteredStudents] = useState([]);

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
      // Curso: obtener todas las ofertas desde coursesAPI.getAll
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

      // Paquete: obtener ofertas
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
      if (!selectedOfferingId) return setFilteredStudents([]);
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

  useEffect(() => {
    fetchStudents();
    fetchOfferingsData();
  }, []);

  return (
    <Box className="admin-dashboard">
      <Typography variant="h4" gutterBottom className="admin-dashboard-title">
        Estudiantes Matriculados
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }} className="admin-filters">
        <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
          Filtrar estudiantes por oferta
        </Typography>
        <Box
          sx={{
            display: "flex",
            gap: 2,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <TextField
            select
            label="Tipo"
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value);
              setSelectedOfferingId("");
              setFilteredStudents([]);
            }}
            size="small"
            className="admin-input admin-select"
          >
            <MenuItem value="course">Curso</MenuItem>
            <MenuItem value="package">Paquete</MenuItem>
          </TextField>
          <TextField
            select
            label={
              filterType === "course" ? "Oferta de curso" : "Oferta de paquete"
            }
            value={selectedOfferingId}
            onChange={(e) => setSelectedOfferingId(e.target.value)}
            size="small"
            sx={{ minWidth: 320 }}
            className="admin-input admin-select"
          >
            {(filterType === "course" ? courseOfferings : packageOfferings).map(
              (o) => (
                <MenuItem key={o.id} value={o.id}>
                  {o.label}
                </MenuItem>
              )
            )}
          </TextField>
          <Button
            variant="contained"
            onClick={applyFilter}
            className="admin-button admin-button-primary"
          >
            Aplicar Filtro
          </Button>
        </Box>

        <Divider sx={{ my: 3 }} />
        <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
          Resultados del Filtro
        </Typography>
        <TableContainer
          component={Paper}
          variant="outlined"
          className="admin-table-container"
        >
          <Table className="admin-table">
            <TableHead className="admin-table-head">
              <TableRow>
                <TableCell className="admin-table-head-cell">DNI</TableCell>
                <TableCell className="admin-table-head-cell">
                  Nombre Completo
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredStudents.map((s) => (
                <TableRow key={s.enrollment_id} className="admin-table-row">
                  <TableCell className="admin-table-cell">{s.dni}</TableCell>
                  <TableCell className="admin-table-cell">
                    <Typography variant="subtitle2" fontWeight="bold">
                      {s.first_name} {s.last_name}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
              {filteredStudents.length === 0 && (
                <TableRow>
                  <TableCell colSpan={2} align="center" sx={{ py: 3 }}>
                    <Typography color="text.secondary">
                      Sin resultados
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default AdminStudents;
