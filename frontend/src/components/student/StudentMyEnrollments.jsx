// src/components/student/StudentMyEnrollments.jsx
import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import {
  Upload as UploadIcon,
  CheckCircleOutline as CheckIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
} from "@mui/icons-material";
import { enrollmentsAPI, paymentsAPI } from "../../services/api";
import { useAuth } from "../../contexts/AuthContext";
import "./student-dashboard.css";
import { useDialog } from "../../hooks/useDialog";
import DialogWrapper from "../common/DialogWrapper";

const StudentMyEnrollments = () => {
  const { user } = useAuth();
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEnrollment, setSelectedEnrollment] = useState(null);
  const [openVoucherDialog, setOpenVoucherDialog] = useState(false);
  const [voucherFile, setVoucherFile] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const {
    confirmDialog,
    alertDialog,
    showConfirm,
    showAlert,
    closeConfirm,
    closeAlert,
  } = useDialog();

  useEffect(() => {
    if (user) {
      loadEnrollments();
    }
  }, [user]);

  const loadEnrollments = async () => {
    try {
      setLoading(true);
      const data = await enrollmentsAPI.getAll();
      setEnrollments(data);
    } catch (err) {
      console.error("Error cargando matrículas:", err);
      setError("Error al cargar matrículas");
    } finally {
      setLoading(false);
    }
  };

  const handleUploadVoucher = async (installmentId) => {
    if (!voucherFile) {
      setError("Selecciona un archivo");
      return;
    }

    try {
      setError("");
      await paymentsAPI.uploadVoucher(installmentId, voucherFile);
      setSuccess("voucher_subido"); // Marcador especial para mostrar mensaje completo
      setOpenVoucherDialog(false);
      setVoucherFile(null);
      loadEnrollments();
    } catch (err) {
      setError(err.message || "Error al subir voucher");
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "aceptado":
        return "success";
      case "pendiente":
        return "warning";
      case "rechazado":
        return "error";
      case "cancelado":
        return "default";
      default:
        return "default";
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case "aceptado":
        return "Aceptado";
      case "pendiente":
        return "Pendiente";
      case "rechazado":
        return "Rechazado";
      case "cancelado":
        return "Cancelado";
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <Box className="student-loading">
        <CircularProgress className="student-loading-spinner" />
      </Box>
    );
  }

  return (
    <Box className="student-content fade-in">
      <Box mb={4}>
        <Typography variant="h4" className="student-page-title">
          Mis Matrículas
        </Typography>
        <Typography color="text.secondary">
          Administra tus matrículas y realiza los pagos de las cuotas.
        </Typography>
      </Box>

      {error && (
        <Alert
          severity="error"
          className="student-alert"
          onClose={() => setError("")}
        >
          {error}
        </Alert>
      )}

      {success && success === "voucher_subido" ? (
        <Alert
          severity="success"
          className="student-alert"
          icon={<CheckIcon fontSize="large" />}
          sx={{
            bgcolor: "#f0fdf4",
            border: "2px solid #86efac",
            "& .MuiAlert-icon": { color: "#16a34a" },
          }}
        >
          <Box>
            <Typography
              variant="h6"
              fontWeight={700}
              sx={{ color: "#15803d", mb: 1 }}
            >
              ¡Gracias por matricularte con nosotros!
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Tu comprobante ha sido enviado correctamente. Por favor, espera a
              que un administrador acepte tu matrícula. Este proceso puede
              tardar un poco.
            </Typography>

            <Box
              sx={{
                mt: 2,
                p: 2,
                bgcolor: "white",
                borderRadius: 2,
                border: "1px solid #d1fae5",
              }}
            >
              <Typography
                variant="subtitle2"
                fontWeight={700}
                sx={{ mb: 1.5, color: "#15803d" }}
              >
                ¿Tienes dudas? Contáctanos:
              </Typography>
              <Grid container spacing={1.5}>
                <Grid item xs={12} sm={6}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <PhoneIcon fontSize="small" sx={{ color: "#16a34a" }} />
                    <Box>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        display="block"
                      >
                        Teléfono
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>
                        +51 938 865 416
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <EmailIcon fontSize="small" sx={{ color: "#16a34a" }} />
                    <Box>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        display="block"
                      >
                        Email
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>
                        info@academiauni.edu.pe
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </Box>

            <Button
              variant="outlined"
              size="small"
              onClick={() => setSuccess("")}
              sx={{
                mt: 2,
                borderColor: "#86efac",
                color: "#15803d",
                "&:hover": {
                  borderColor: "#22c55e",
                  bgcolor: "#f0fdf4",
                },
              }}
            >
              Entendido
            </Button>
          </Box>
        </Alert>
      ) : success ? (
        <Alert
          severity="success"
          className="student-alert"
          onClose={() => setSuccess("")}
        >
          {success}
        </Alert>
      ) : null}

      <Grid container spacing={3}>
        {enrollments
          // Ocultar cursos que pertenecen a un paquete y matrículas canceladas; dejar solo la matrícula del paquete
          .filter((enrollment) => {
            if (enrollment.status === "cancelado") {
              return false;
            }
            if (
              enrollment.enrollment_type === "course" &&
              enrollment.package_offering_id
            ) {
              return false;
            }
            return true;
          })
          .map((enrollment) => (
            <Grid item xs={12} md={6} key={enrollment.id}>
              <Card
                className={`student-card student-enrollment-card course-card ${enrollment.status}`}
              >
                <CardContent>
                  <Box
                    display="flex"
                    justifyContent="space-between"
                    alignItems="start"
                    mb={2}
                  >
                    <Box display="flex" gap={1}>
                      <Chip
                        label={
                          enrollment.enrollment_type === "course"
                            ? "📚 Curso"
                            : "📦 Paquete"
                        }
                        size="small"
                        className="student-badge default"
                      />
                    </Box>
                    <Chip
                      label={getStatusLabel(enrollment.status)}
                      className={`student-badge ${enrollment.status === "aceptado"
                        ? "approved"
                        : enrollment.status === "pendiente"
                          ? "pending"
                          : enrollment.status === "rechazado"
                            ? "rejected"
                            : "default"
                        }`}
                      size="small"
                    />
                  </Box>
                  <Typography
                    variant="h6"
                    className="course-card-title"
                    sx={{ mb: 2 }}
                  >
                    {enrollment.item_name || "Curso/Paquete"}
                  </Typography>
                  {enrollment.cycle_name && (
                    <Typography
                      variant="body2"
                      color="textSecondary"
                      gutterBottom
                    >
                      Ciclo: {enrollment.cycle_name}
                    </Typography>
                  )}
                  {(enrollment.cycle_start_date ||
                    enrollment.cycle_end_date) && (
                      <Typography
                        variant="body2"
                        color="textSecondary"
                        gutterBottom
                      >
                        {enrollment.cycle_start_date
                          ? new Date(
                            enrollment.cycle_start_date
                          ).toLocaleDateString()
                          : "-"}{" "}
                        -{" "}
                        {enrollment.cycle_end_date
                          ? new Date(
                            enrollment.cycle_end_date
                          ).toLocaleDateString()
                          : "-"}
                      </Typography>
                    )}
                  {/* Para matrículas de paquete, mostrar descripción de cursos incluidos */}
                  {enrollment.enrollment_type === "package" &&
                    enrollment.package_courses_summary && (
                      <Typography
                        variant="body2"
                        color="textSecondary"
                        gutterBottom
                      >
                        Cursos incluidos: {enrollment.package_courses_summary}
                      </Typography>
                    )}
                  <Typography className="student-price" sx={{ mt: 2 }}>
                    S/. {parseFloat(enrollment.item_price || 0).toFixed(2)}
                  </Typography>

                  {enrollment.status === "pendiente" &&
                    (!enrollment.installments ||
                      enrollment.installments.every(
                        (inst) => inst.status !== "paid" && !inst.voucher_url
                      )) && (
                      <Box sx={{ mt: 2 }}>
                        <Button
                          variant="outlined"
                          size="small"
                          className="student-btn-remove"
                          onClick={async () => {
                            const confirmed = await showConfirm({
                              title: "¿Cancelar matrícula?",
                              message:
                                "Esta acción cancelará tu matrícula y no podrá recuperarse.",
                              type: "warning",
                              confirmText: "Cancelar Matrícula",
                            });
                            if (!confirmed) return;

                            try {
                              setError("");
                              setSuccess("");
                              await enrollmentsAPI.cancel(enrollment.id);
                              setSuccess("Matrícula cancelada correctamente");
                              loadEnrollments();
                            } catch (err) {
                              setError(
                                err.message || "Error al cancelar matrícula"
                              );
                            }
                          }}
                          sx={{ textTransform: "none" }}
                        >
                          Cancelar matrícula
                        </Button>
                      </Box>
                    )}

                  {/* Cuotas */}
                  {enrollment.installments &&
                    enrollment.installments.length > 0 && (
                      <Box sx={{ mt: 3 }}>
                        <Typography
                          variant="subtitle2"
                          gutterBottom
                          sx={{ fontWeight: 700, mb: 1.5 }}
                        >
                          💳 Cuotas de Pago
                        </Typography>
                        <TableContainer
                          component={Paper}
                          variant="outlined"
                          sx={{ borderRadius: 2, overflow: "hidden" }}
                        >
                          <Table size="small">
                            <TableHead>
                              <TableRow sx={{ bgcolor: "#f8fafc" }}>
                                <TableCell
                                  sx={{ fontWeight: 700, color: "#475569" }}
                                >
                                  #
                                </TableCell>
                                <TableCell
                                  sx={{ fontWeight: 700, color: "#475569" }}
                                >
                                  Monto
                                </TableCell>
                                <TableCell
                                  sx={{ fontWeight: 700, color: "#475569" }}
                                >
                                  Vencimiento
                                </TableCell>
                                <TableCell
                                  sx={{ fontWeight: 700, color: "#475569" }}
                                >
                                  Estado
                                </TableCell>
                                <TableCell
                                  sx={{ fontWeight: 700, color: "#475569" }}
                                >
                                  Acciones
                                </TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {enrollment.installments.map((installment) => (
                                <TableRow key={installment.id}>
                                  <TableCell>
                                    {installment.installment_number}
                                  </TableCell>
                                  <TableCell>
                                    S/.{" "}
                                    {parseFloat(
                                      installment.amount || 0
                                    ).toFixed(2)}
                                  </TableCell>
                                  <TableCell>
                                    {installment.due_date
                                      ? new Date(
                                        installment.due_date
                                      ).toLocaleDateString()
                                      : "-"}
                                  </TableCell>
                                  <TableCell>
                                    <Chip
                                      label={
                                        installment.status === "paid"
                                          ? "Pagado"
                                          : installment.status === "overdue"
                                            ? "Vencido"
                                            : "Pendiente"
                                      }
                                      color={
                                        installment.status === "paid"
                                          ? "success"
                                          : installment.status === "overdue"
                                            ? "error"
                                            : "warning"
                                      }
                                      size="small"
                                    />
                                  </TableCell>
                                  <TableCell>
                                    {(installment.status === "pending" ||
                                      installment.status === "overdue") &&
                                      !installment.voucher_url && (
                                        <Button
                                          size="small"
                                          variant="contained"
                                          className="student-btn-primary"
                                          startIcon={<UploadIcon />}
                                          onClick={() => {
                                            setSelectedEnrollment(installment);
                                            setOpenVoucherDialog(true);
                                          }}
                                          sx={{ textTransform: "none" }}
                                        >
                                          Subir Voucher
                                        </Button>
                                      )}
                                    {installment.voucher_url && (
                                      <Button
                                        size="small"
                                        variant="outlined"
                                        className="student-btn-secondary"
                                        href={installment.voucher_url}
                                        target="_blank"
                                        sx={{ textTransform: "none" }}
                                      >
                                        Ver Voucher
                                      </Button>
                                    )}
                                    {installment.rejection_reason && (
                                      <Alert severity="error" sx={{ mt: 1 }}>
                                        Rechazado:{" "}
                                        {installment.rejection_reason}
                                      </Alert>
                                    )}
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Box>
                    )}
                </CardContent>
              </Card>
            </Grid>
          ))}
      </Grid>

      {enrollments.length === 0 && (
        <Box className="empty-search-state">
          <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
            📋 No tienes matrículas registradas
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Dirígete a "Cursos Disponibles" para comenzar tu matrícula
          </Typography>
        </Box>
      )}

      {/* Dialog para subir voucher */}
      <Dialog
        open={openVoucherDialog}
        onClose={() => setOpenVoucherDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle className="student-dialog-title">
          📤 Subir Voucher de Pago
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 2 }}>
            {selectedEnrollment &&
              (() => {
                const parentEnrollment = enrollments.find(
                  (enr) =>
                    Array.isArray(enr.installments) &&
                    enr.installments.some(
                      (inst) => inst.id === selectedEnrollment.id
                    )
                );

                return (
                  <>
                    {parentEnrollment && (
                      <>
                        {parentEnrollment.cycle_name && (
                          <Typography variant="body2" color="textSecondary">
                            Ciclo: {parentEnrollment.cycle_name}
                          </Typography>
                        )}
                        {(parentEnrollment.cycle_start_date ||
                          parentEnrollment.cycle_end_date) && (
                            <Typography variant="body2" color="textSecondary">
                              {parentEnrollment.cycle_start_date
                                ? new Date(
                                  parentEnrollment.cycle_start_date
                                ).toLocaleDateString()
                                : "-"}{" "}
                              -{" "}
                              {parentEnrollment.cycle_end_date
                                ? new Date(
                                  parentEnrollment.cycle_end_date
                                ).toLocaleDateString()
                                : "-"}
                            </Typography>
                          )}
                      </>
                    )}
                    <Typography variant="body2">
                      Cuota #{selectedEnrollment.installment_number} - S/.{" "}
                      {parseFloat(selectedEnrollment.amount || 0).toFixed(2)}
                    </Typography>
                    <TextField
                      type="file"
                      inputProps={{ accept: "image/jpeg,image/jpg,image/png,image/gif,image/webp" }}
                      onChange={(e) => setVoucherFile(e.target.files[0])}
                      fullWidth
                    />
                  </>
                );
              })()}
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: "1px solid #f1f5f9" }}>
          <Button onClick={() => setOpenVoucherDialog(false)}>Cancelar</Button>
          <Button
            onClick={() => handleUploadVoucher(selectedEnrollment?.id)}
            variant="contained"
            className="student-btn-primary"
            disabled={!voucherFile}
          >
            Subir Voucher
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

export default StudentMyEnrollments;
