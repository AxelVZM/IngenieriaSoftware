// src/components/admin/CourseForm.jsx
import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack,
  IconButton,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import { useFormik } from "formik";
import * as yup from "yup";
import { teachersAPI, coursesAPI, schedulesAPI } from "../../services/api";

const validationSchema = yup.object({
  name: yup.string().required("El nombre del curso es requerido"),
  description: yup.string().required("La descripción es requerida"),
  teacher_id: yup.number().required("El profesor es requerido"),
  price: yup
    .number()
    .required("El precio es requerido")
    .min(0, "El precio no puede ser negativo"),
});

const DAYS = [
  "Lunes",
  "Martes",
  "Miércoles",
  "Jueves",
  "Viernes",
  "Sábado",
  "Domingo",
];

const CourseForm = () => {
  const [teachers, setTeachers] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchTeachers = async () => {
      try {
        const data = await teachersAPI.getAll();
        setTeachers(data);
      } catch (err) {
        console.error("Error al cargar profesores:", err);
        setError("Error al cargar la lista de profesores");
      }
    };
    fetchTeachers();
  }, []);

  const formik = useFormik({
    initialValues: {
      name: "",
      description: "",
      teacher_id: "",
      price: "",
    },
    validationSchema,
    onSubmit: async (values) => {
      try {
        const courseData = await coursesAPI.create(values);

        const schedulePromises = schedules.map((schedule) =>
          schedulesAPI.create({
            course_id: courseData.id,
            day_of_week: schedule.day,
            start_time: schedule.startTime,
            end_time: schedule.endTime,
            classroom: schedule.classroom,
          })
        );

        await Promise.all(schedulePromises);
        alert("Curso y horarios creados exitosamente");
        formik.resetForm();
        setSchedules([]);
      } catch (err) {
        console.error("Error:", err);
        setError("Error al crear el curso");
      }
    },
  });

  const handleAddSchedule = () => {
    setSchedules([
      ...schedules,
      {
        day: "",
        startTime: "",
        endTime: "",
        classroom: "",
      },
    ]);
  };

  const handleRemoveSchedule = (index) => {
    setSchedules(schedules.filter((_, i) => i !== index));
  };

  const handleScheduleChange = (index, field, value) => {
    const newSchedules = [...schedules];
    newSchedules[index] = {
      ...newSchedules[index],
      [field]: value,
    };
    setSchedules(newSchedules);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Crear Nuevo Curso
        </Typography>

        <form onSubmit={formik.handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                id="name"
                name="name"
                label="Nombre del Curso"
                value={formik.values.name}
                onChange={formik.handleChange}
                error={formik.touched.name && Boolean(formik.errors.name)}
                helperText={formik.touched.name && formik.errors.name}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                id="description"
                name="description"
                label="Descripción"
                multiline
                rows={4}
                value={formik.values.description}
                onChange={formik.handleChange}
                error={
                  formik.touched.description &&
                  Boolean(formik.errors.description)
                }
                helperText={
                  formik.touched.description && formik.errors.description
                }
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Profesor</InputLabel>
                <Select
                  id="teacher_id"
                  name="teacher_id"
                  value={formik.values.teacher_id}
                  onChange={formik.handleChange}
                  error={
                    formik.touched.teacher_id &&
                    Boolean(formik.errors.teacher_id)
                  }
                >
                  {teachers.map((teacher) => (
                    <MenuItem key={teacher.id} value={teacher.id}>
                      {teacher.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                id="price"
                name="price"
                label="Precio"
                type="number"
                value={formik.values.price}
                onChange={formik.handleChange}
                error={formik.touched.price && Boolean(formik.errors.price)}
                helperText={formik.touched.price && formik.errors.price}
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Horarios
              </Typography>
              {schedules.map((schedule, index) => (
                <Box
                  key={index}
                  sx={{
                    mb: 2,
                    p: 2,
                    border: "1px solid #ddd",
                    borderRadius: 1,
                  }}
                >
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={2}>
                      <FormControl fullWidth>
                        <InputLabel>Día</InputLabel>
                        <Select
                          value={schedule.day}
                          onChange={(e) =>
                            handleScheduleChange(index, "day", e.target.value)
                          }
                        >
                          {DAYS.map((day) => (
                            <MenuItem key={day} value={day}>
                              {day}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} md={2}>
                      <TextField
                        fullWidth
                        label="Hora inicio"
                        type="time"
                        value={schedule.startTime}
                        onChange={(e) =>
                          handleScheduleChange(
                            index,
                            "startTime",
                            e.target.value
                          )
                        }
                        InputLabelProps={{ shrink: true }}
                      />
                    </Grid>
                    <Grid item xs={12} md={2}>
                      <TextField
                        fullWidth
                        label="Hora fin"
                        type="time"
                        value={schedule.endTime}
                        onChange={(e) =>
                          handleScheduleChange(index, "endTime", e.target.value)
                        }
                        InputLabelProps={{ shrink: true }}
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        label="Aula"
                        value={schedule.classroom}
                        onChange={(e) =>
                          handleScheduleChange(
                            index,
                            "classroom",
                            e.target.value
                          )
                        }
                      />
                    </Grid>
                    <Grid item xs={12} md={2}>
                      <IconButton
                        onClick={() => handleRemoveSchedule(index)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Grid>
                  </Grid>
                </Box>
              ))}
              <Button
                variant="outlined"
                onClick={handleAddSchedule}
                sx={{ mt: 2 }}
              >
                Agregar Horario
              </Button>
            </Grid>

            {error && (
              <Grid item xs={12}>
                <Typography color="error">{error}</Typography>
              </Grid>
            )}

            <Grid item xs={12}>
              <Button
                fullWidth
                variant="contained"
                color="primary"
                type="submit"
                sx={{ mt: 2 }}
              >
                Crear Curso
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
};

export default CourseForm;
