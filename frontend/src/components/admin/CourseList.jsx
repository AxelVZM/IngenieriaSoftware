// src/components/admin/CourseList.jsx
import React, { useState, useEffect } from "react";
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  Collapse,
  IconButton,
} from "@mui/material";
import { KeyboardArrowDown, KeyboardArrowUp } from "@mui/icons-material";
import { Link } from "react-router-dom";
import { coursesAPI } from "../../services/api";

const CourseRow = ({ course }) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <TableRow sx={{ "& > *": { borderBottom: "unset" } }}>
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row">
          {course.name}
        </TableCell>
        <TableCell>{course.teacher_name || "Sin asignar"}</TableCell>
        <TableCell>S/. {course.price}</TableCell>
        <TableCell>{course.schedules?.length || 0} horarios</TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 1 }}>
              <Typography variant="h6" gutterBottom component="div">
                Horarios
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Día</TableCell>
                    <TableCell>Hora Inicio</TableCell>
                    <TableCell>Hora Fin</TableCell>
                    <TableCell>Aula</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {course.schedules?.map((schedule, index) => (
                    <TableRow key={index}>
                      <TableCell>{schedule.day_of_week}</TableCell>
                      <TableCell>{schedule.start_time}</TableCell>
                      <TableCell>{schedule.end_time}</TableCell>
                      <TableCell>{schedule.classroom}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

const CourseList = () => {
  const [courses, setCourses] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const data = await coursesAPI.getAll();
        setCourses(data);
      } catch (err) {
        console.error("Error:", err);
        setError("Error al cargar los cursos");
      }
    };
    fetchCourses();
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 3 }}>
        <Typography variant="h5">Cursos</Typography>
        <Button
          variant="contained"
          color="primary"
          component={Link}
          to="/admin/courses/new"
        >
          Nuevo Curso
        </Button>
      </Box>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell>Nombre</TableCell>
              <TableCell>Profesor</TableCell>
              <TableCell>Precio</TableCell>
              <TableCell>Horarios</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {courses.map((course) => (
              <CourseRow key={course.id} course={course} />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default CourseList;
