// src/components/admin/AdminPayments.jsx
import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Button,
  Paper,
} from "@mui/material";
import { paymentsAPI } from "../../services/api";

const AdminPayments = () => {
  const [payments, setPayments] = useState([]);
  const [error, setError] = useState("");

  const fetchPayments = async () => {
    try {
      const data = await paymentsAPI.getAll("pendiente");
      setPayments(data);
    } catch (err) {
      console.error(err);
      setError("Error al cargar pagos");
    }
  };

  useEffect(() => {
    fetchPayments();
  }, []);

  const handleApprove = async (installmentId) => {
    try {
      await paymentsAPI.approveInstallment(installmentId);
      fetchPayments();
      alert("Pago aprobado");
    } catch (err) {
      console.error(err);
      setError(err.message || "Error al aprobar");
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Pagos pendientes
      </Typography>
      {error && <Typography color="error">{error}</Typography>}
      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Estudiante</TableCell>
              <TableCell>Item</TableCell>
              <TableCell>Monto</TableCell>
              <TableCell>Voucher</TableCell>
              <TableCell>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {payments.map((p) => (
              <TableRow key={p.id}>
                <TableCell>
                  {p.first_name} {p.last_name} ({p.dni})
                </TableCell>
                <TableCell>
                  {p.item_name} ({p.type})
                </TableCell>
                <TableCell>S/. {p.amount}</TableCell>
                <TableCell>
                  {p.voucher_url ? (
                    <a
                      href={p.voucher_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Ver
                    </a>
                  ) : (
                    "Sin voucher"
                  )}
                </TableCell>
                <TableCell>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => handleApprove(p.enrollment_id)}
                  >
                    Aprobar
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
};

export default AdminPayments;
