// src/components/admin/AdminPaymentsComplete.jsx
import React, { useEffect, useState, useRef } from "react";
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
  Button,
  Chip,
  TextField,
  MenuItem,
  IconButton,
} from "@mui/material";
import {
  CheckCircle as CheckCircleIcon,
  Visibility as VisibilityIcon,
  Cancel as CancelIcon,
} from "@mui/icons-material";
import { paymentsAPI } from "../../services/api";
import ConfirmDialog from "../common/ConfirmDialog";
import PromptDialog from "../common/PromptDialog";
import "./admin-dashboard.css";

const AdminPaymentsComplete = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("pending");

  // Estados para diálogos personalizados
  const [confirmDialog, setConfirmDialog] = useState({
    open: false,
    type: "",
    installmentId: null,
  });
  const [promptDialog, setPromptDialog] = useState({ open: false });
  const [alertMessage, setAlertMessage] = useState({
    open: false,
    message: "",
    type: "info",
  });

  // Use ref to preserve installmentId across state updates
  const pendingInstallmentId = useRef(null);

  useEffect(() => {
    loadPayments();
  }, [statusFilter]);

  const loadPayments = async () => {
    try {
      setLoading(true);
      const status = statusFilter === "all" ? null : statusFilter;
      const data = await paymentsAPI.getAll(status);
      setPayments(data);
    } catch (err) {
      console.error("Error cargando pagos:", err);
      setAlertMessage({
        open: true,
        message: "Error al cargar pagos",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReject = (installmentId) => {
    pendingInstallmentId.current = installmentId;
    setConfirmDialog({ open: true, type: "reject", installmentId });
  };

  const confirmReject = () => {
    setConfirmDialog({ open: false, type: "", installmentId: null });
    setPromptDialog({ open: true });
  };

  const executeReject = async (reason) => {
    const installmentId = pendingInstallmentId.current;
    setPromptDialog({ open: false });
    setConfirmDialog({ open: false, type: "", installmentId: null });
    pendingInstallmentId.current = null;

    if (!installmentId) {
      setAlertMessage({
        open: true,
        message: "Error: ID de pago no encontrado",
        type: "error",
      });
      return;
    }

    try {
      await paymentsAPI.rejectInstallment(installmentId, reason || null);
      setAlertMessage({
        open: true,
        message: "Pago rechazado exitosamente",
        type: "success",
      });
      loadPayments();
    } catch (err) {
      setAlertMessage({
        open: true,
        message: err.message || "Error al rechazar pago",
        type: "error",
      });
    }
  };

  const handleApprove = (installmentId) => {
    setConfirmDialog({ open: true, type: "approve", installmentId });
  };

  const executeApprove = async () => {
    const { installmentId } = confirmDialog;
    setConfirmDialog({ ...confirmDialog, open: false });
    try {
      const res = await paymentsAPI.approveInstallment(installmentId);
      const { cycle_start_date, cycle_end_date } = res || {};
      const datesMsg =
        cycle_start_date && cycle_end_date
          ? ` Ciclo: ${new Date(
              cycle_start_date
            ).toLocaleDateString()} - ${new Date(
              cycle_end_date
            ).toLocaleDateString()}`
          : "";
      setAlertMessage({
        open: true,
        message: `Pago aprobado correctamente.${datesMsg}`,
        type: "success",
      });
      loadPayments();
    } catch (err) {
      setAlertMessage({
        open: true,
        message: err.message || "Error al aprobar pago",
        type: "error",
      });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "paid":
        return "success";
      case "pending":
        return "warning";
      case "overdue":
        return "error";
      case "rejected":
        return "default";
      default:
        return "default";
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case "paid":
        return "Pagado";
      case "pending":
        return "Pendiente";
      case "overdue":
        return "Vencido";
      case "rejected":
        return "Rechazado";
      default:
        return status;
    }
  };

  return (
    <Box className="admin-dashboard">
      <Typography variant="h4" gutterBottom className="admin-dashboard-title">
        Gestión de Pagos
      </Typography>

      <Box mb={2}>
        <TextField
          select
          label="Filtrar por estado"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="all">Todos</MenuItem>
          <MenuItem value="pending">Pendientes</MenuItem>
          <MenuItem value="paid">Pagados</MenuItem>
          <MenuItem value="overdue">Vencidos</MenuItem>
          <MenuItem value="rejected">Rechazados</MenuItem>
        </TextField>
      </Box>

      <TableContainer component={Paper} className="admin-table-container">
        <Table className="admin-table">
          <TableHead className="admin-table-head">
            <TableRow>
              <TableCell className="admin-table-head-cell">
                Estudiante
              </TableCell>
              <TableCell className="admin-table-head-cell">DNI</TableCell>
              <TableCell className="admin-table-head-cell">
                Curso/Paquete
              </TableCell>
              <TableCell className="admin-table-head-cell">Monto</TableCell>
              <TableCell className="admin-table-head-cell">
                Fecha Vencimiento
              </TableCell>
              <TableCell className="admin-table-head-cell">Estado</TableCell>
              <TableCell className="admin-table-head-cell">Voucher</TableCell>
              <TableCell className="admin-table-head-cell">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {payments.map((payment) => (
              <TableRow key={payment.id} className="admin-table-row">
                <TableCell className="admin-table-cell">
                  <Typography variant="subtitle2" fontWeight="bold">
                    {payment.first_name} {payment.last_name}
                  </Typography>
                </TableCell>
                <TableCell className="admin-table-cell">
                  {payment.dni}
                </TableCell>
                <TableCell className="admin-table-cell">
                  {payment.item_name || "-"}
                </TableCell>
                <TableCell className="admin-table-cell">
                  S/. {parseFloat(payment.amount || 0).toFixed(2)}
                </TableCell>
                <TableCell className="admin-table-cell">
                  {payment.due_date
                    ? new Date(payment.due_date).toLocaleDateString()
                    : "-"}
                </TableCell>
                <TableCell className="admin-table-cell">
                  <Chip
                    label={getStatusLabel(payment.status_ui || payment.status)}
                    color={getStatusColor(payment.status_ui || payment.status)}
                    size="small"
                    className="admin-chip"
                  />
                </TableCell>
                <TableCell className="admin-table-cell">
                  {payment.voucher_url ? (
                    <Button
                      size="small"
                      href={payment.voucher_url}
                      target="_blank"
                      startIcon={<VisibilityIcon />}
                    >
                      Ver
                    </Button>
                  ) : (
                    <Typography variant="body2" color="textSecondary">
                      Sin voucher
                    </Typography>
                  )}
                </TableCell>
                <TableCell className="admin-table-cell">
                  {payment.status === "pending" && (
                    <>
                      {payment.voucher_url && (
                        <IconButton
                          size="small"
                          color="success"
                          onClick={() => handleApprove(payment.id)}
                          title="Aprobar pago"
                        >
                          <CheckCircleIcon />
                        </IconButton>
                      )}
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleReject(payment.id)}
                        title="Rechazar pago"
                        sx={{ ml: 1 }}
                      >
                        <CancelIcon />
                      </IconButton>
                    </>
                  )}
                  {payment.status === "overdue" && (
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Chip label="Vencido" color="error" size="small" />
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleReject(payment.id)}
                        title="Rechazar pago"
                      >
                        <CancelIcon />
                      </IconButton>
                    </Box>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {payments.length === 0 && (
          <Box p={3} textAlign="center">
            <Typography color="textSecondary">No hay pagos</Typography>
          </Box>
        )}
      </TableContainer>

      {/* Diálogo de Confirmación */}
      <ConfirmDialog
        open={confirmDialog.open && confirmDialog.type !== ""}
        onClose={() =>
          setConfirmDialog({ open: false, type: "", installmentId: null })
        }
        onConfirm={
          confirmDialog.type === "approve" ? executeApprove : confirmReject
        }
        title={
          confirmDialog.type === "approve"
            ? "¿Aprobar pago?"
            : "¿Rechazar pago?"
        }
        message={
          confirmDialog.type === "approve"
            ? "Esta acción marcará el pago como aprobado y activará la matrícula del estudiante."
            : "El pago será marcado como rechazado y se notificará al estudiante."
        }
        confirmText={confirmDialog.type === "approve" ? "Aprobar" : "Continuar"}
        type={confirmDialog.type === "approve" ? "success" : "warning"}
      />

      {/* Diálogo de Razón de Rechazo */}
      <PromptDialog
        open={promptDialog.open}
        onClose={() => setPromptDialog({ open: false })}
        onConfirm={executeReject}
        title="Razón del rechazo"
        message="Ingresa el motivo por el cual se rechaza este pago (opcional)"
        label="Razón"
        defaultValue="Voucher ilegible / no coincide el monto /fuera de fecha"
        placeholder="Escribe la razón aquí..."
        multiline
      />

      {/* Mensaje de Alerta */}
      <ConfirmDialog
        open={alertMessage.open}
        onClose={() => setAlertMessage({ ...alertMessage, open: false })}
        onConfirm={() => setAlertMessage({ ...alertMessage, open: false })}
        title={
          alertMessage.type === "success"
            ? "Éxito"
            : alertMessage.type === "error"
            ? "Error"
            : "Información"
        }
        message={alertMessage.message}
        confirmText="Entendido"
        cancelText=""
        type={alertMessage.type}
      />
    </Box>
  );
};

export default AdminPaymentsComplete;
