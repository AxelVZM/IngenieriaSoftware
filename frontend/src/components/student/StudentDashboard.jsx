// src/components/student/StudentDashboard.jsx
import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from "@mui/material";
import {
  coursesAPI,
  packagesAPI,
  cyclesAPI,
  enrollmentsAPI,
  paymentsAPI,
} from "../../services/api";

const StudentDashboard = () => {
  const [courses, setCourses] = useState([]);
  const [packages, setPackages] = useState([]);
  const [selected, setSelected] = useState([]);
  const [openPay, setOpenPay] = useState(false);
  const [payments, setPayments] = useState([]);
  const [voucherFile, setVoucherFile] = useState(null);
  const [error, setError] = useState("");
  const [activeCycle, setActiveCycle] = useState(null);

  useEffect(() => {
    coursesAPI
      .getAll()
      .then(setCourses)
      .catch((e) => console.error(e));
    packagesAPI
      .getAll()
      .then(setPackages)
      .catch((e) => console.error(e));
    cyclesAPI
      .getActive()
      .then(setActiveCycle)
      .catch((e) => console.error("Error obteniendo ciclo activo", e));
  }, []);

  const toggleSelect = (type, id, name, price) => {
    const key = `${type}-${id}`;
    const exists = selected.find((s) => s.key === key);
    if (exists) setSelected(selected.filter((s) => s.key !== key));
    else setSelected([...selected, { key, type, id, name, price }]);
  };

  const total = selected.reduce((s, i) => s + Number(i.price || 0), 0);

  const handleCreate = async () => {
    try {
      const items = selected.map((i) => ({ type: i.type, id: i.id }));
      const data = await enrollmentsAPI.create(items);
      const created = data.created || [];
      setPayments(created);
      setOpenPay(true);
    } catch (err) {
      console.error(err);
      setError(err.message || "Error al crear matrícula");
    }
  };

  const handleUpload = async (enrollmentId) => {
    try {
      if (!voucherFile) return setError("Seleccione un voucher");
      await paymentsAPI.uploadVoucher(enrollmentId, voucherFile);
      alert("Voucher subido correctamente");
      setOpenPay(false);
      setSelected([]);
    } catch (err) {
      console.error(err);
      setError(err.message || "Error al subir voucher");
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {activeCycle && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1">
            Ciclo actual: {activeCycle.name}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {activeCycle.start_date
              ? new Date(activeCycle.start_date).toLocaleDateString()
              : "-"}{" "}
            -{" "}
            {activeCycle.end_date
              ? new Date(activeCycle.end_date).toLocaleDateString()
              : "-"}
          </Typography>
        </Box>
      )}
      <Typography variant="h5" sx={{ mb: 2 }}>
        Cursos disponibles
      </Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {courses.map((c) => (
          <Grid item xs={12} md={4} key={c.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{c.name}</Typography>
                <Typography variant="body2">{c.description}</Typography>
                <Typography sx={{ mt: 1 }}>
                  Profesor: {c.teacher_name || "Sin asignar"}
                </Typography>
                <Typography sx={{ mt: 1 }}>Precio: S/. {c.price}</Typography>
                {activeCycle && (
                  <Typography
                    variant="body2"
                    color="textSecondary"
                    sx={{ mt: 0.5 }}
                  >
                    Ciclo: {activeCycle.name} (
                    {activeCycle.start_date
                      ? new Date(activeCycle.start_date).toLocaleDateString()
                      : "-"}{" "}
                    -{" "}
                    {activeCycle.end_date
                      ? new Date(activeCycle.end_date).toLocaleDateString()
                      : "-"}
                    )
                  </Typography>
                )}
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  onClick={() => toggleSelect("course", c.id, c.name, c.price)}
                >
                  {selected.find((s) => s.key === `course-${c.id}`)
                    ? "Quitar"
                    : "Seleccionar"}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Typography variant="h5" sx={{ mb: 2 }}>
        Paquetes
      </Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {packages.map((p) => (
          <Grid item xs={12} md={4} key={p.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{p.name}</Typography>
                <Typography variant="body2">{p.description}</Typography>
                <Typography sx={{ mt: 1 }}>
                  Precio paquete: S/. {p.price_total}
                </Typography>
                {activeCycle && (
                  <Typography
                    variant="body2"
                    color="textSecondary"
                    sx={{ mt: 0.5 }}
                  >
                    Ciclo: {activeCycle.name} (
                    {activeCycle.start_date
                      ? new Date(activeCycle.start_date).toLocaleDateString()
                      : "-"}{" "}
                    -{" "}
                    {activeCycle.end_date
                      ? new Date(activeCycle.end_date).toLocaleDateString()
                      : "-"}
                    )
                  </Typography>
                )}
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  onClick={() =>
                    toggleSelect("package", p.id, p.name, p.price_total)
                  }
                >
                  {selected.find((s) => s.key === `package-${p.id}`)
                    ? "Quitar"
                    : "Seleccionar"}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 2 }}>
        <Typography>Total: S/. {total.toFixed(2)}</Typography>
        <Button
          variant="contained"
          sx={{ mt: 1 }}
          disabled={selected.length === 0}
          onClick={handleCreate}
        >
          Generar matrícula y pagar
        </Button>
      </Box>

      {error && (
        <Typography color="error" sx={{ mt: 2 }}>
          {error}
        </Typography>
      )}

      <Dialog open={openPay} onClose={() => setOpenPay(false)} fullWidth>
        <DialogTitle>Subir Voucher de Pago</DialogTitle>
        <DialogContent>
          {activeCycle && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="body2" color="textSecondary">
                Ciclo: {activeCycle.name} (
                {activeCycle.start_date
                  ? new Date(activeCycle.start_date).toLocaleDateString()
                  : "-"}{" "}
                -{" "}
                {activeCycle.end_date
                  ? new Date(activeCycle.end_date).toLocaleDateString()
                  : "-"}
                )
              </Typography>
            </Box>
          )}
          <Typography>Adjunta el voucher para cada pago generado.</Typography>
          <Box sx={{ mt: 2 }}>
            <input
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
              onChange={(e) => setVoucherFile(e.target.files[0])}
            />
          </Box>
          <Box sx={{ mt: 2 }}>
            {/* Mostrar pagos de paquetes con descripción de cursos, y pagos individuales reales */}
            {payments
              .filter((p) => {
                // Mantener siempre las entradas de paquetes
                if (p.type === "package") return true;
                // Para cursos sueltos (no provenientes de paquete), solo considerar si tienen monto > 0
                const amount = Number(p.amount || 0);
                return p.type === "course" && amount > 0;
              })
              .map((p) => (
                <Box
                  key={p.enrollmentId}
                  sx={{
                    mb: 2,
                    p: 1,
                    border: "1px solid #ddd",
                    borderRadius: 1,
                  }}
                >
                  {p.type === "package" ? (
                    <>
                      <Typography
                        variant="subtitle1"
                        sx={{ fontWeight: "bold" }}
                      >
                        Pago de paquete
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 0.5 }}>
                        Monto total: S/. {Number(p.amount || 0).toFixed(2)}
                      </Typography>
                      {Array.isArray(p.courses) && p.courses.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography
                            variant="body2"
                            sx={{ fontWeight: "bold" }}
                          >
                            Cursos incluidos:
                          </Typography>
                          {p.courses.map((c, idx) => (
                            <Typography key={idx} variant="body2">
                              - {c.name}
                              {c.group ? ` (Grupo ${c.group})` : ""}
                            </Typography>
                          ))}
                        </Box>
                      )}
                    </>
                  ) : (
                    <>
                      <Typography
                        variant="subtitle1"
                        sx={{ fontWeight: "bold" }}
                      >
                        Pago de curso
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 0.5 }}>
                        Monto: S/. {Number(p.amount || 0).toFixed(2)}
                      </Typography>
                    </>
                  )}
                  <Button
                    variant="outlined"
                    onClick={() => handleUpload(p.enrollmentId)}
                    sx={{ mt: 1 }}
                  >
                    Subir voucher
                  </Button>
                </Box>
              ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPay(false)}>Cerrar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StudentDashboard;
