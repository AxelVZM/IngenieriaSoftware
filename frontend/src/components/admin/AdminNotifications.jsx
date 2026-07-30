import { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Checkbox,
  FormControlLabel,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  MenuItem,
  Grid,
} from "@mui/material";
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import { notificationsAPI, adminAPI, cyclesAPI } from "../../services/api";

dayjs.locale('es');

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function AdminNotifications() {
  const [tabValue, setTabValue] = useState(0);
  const [qrCode, setQrCode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [scanned, setScanned] = useState(false);
  const [message, setMessage] = useState(null);
  const [qrRefreshCount, setQrRefreshCount] = useState(0);

  // Payment notifications state
  const [rejectedPayments, setRejectedPayments] = useState([]);
  const [acceptedPayments, setAcceptedPayments] = useState([]);
  const [loadingPayments, setLoadingPayments] = useState(false);
  const [sendingNotifications, setSendingNotifications] = useState(false);

  // Attendance notifications state
  const [cycles, setCycles] = useState([]);
  const [selectedCycle, setSelectedCycle] = useState('');
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [selectedGroup, setSelectedGroup] = useState('A'); // Default to group A
  const [groups] = useState(['A', 'B', 'C', 'D']);
  const [attendanceStudents, setAttendanceStudents] = useState([]);
  const [loadingAttendance, setLoadingAttendance] = useState(false);
  const [sendingAttendance, setSendingAttendance] = useState(false);
  const [dateRange, setDateRange] = useState({ min: null, max: null });

  // Auto-refresh QR every 60 seconds
  useEffect(() => {
    if (qrCode && !loggedIn) {
      const timer = setTimeout(() => {
        handleRefreshQR();
      }, 60000); // 60 seconds

      return () => clearTimeout(timer);
    }
  }, [qrCode, loggedIn, qrRefreshCount]);

  // Load cycles on mount
  useEffect(() => {
    loadCycles();
  }, []);

  // Update date range when cycle changes
  useEffect(() => {
    if (selectedCycle) {
      const cycle = cycles.find(c => c.id === parseInt(selectedCycle));
      if (cycle) {
        setDateRange({
          min: dayjs(cycle.start_date),
          max: dayjs(cycle.end_date).isBefore(dayjs()) ? dayjs(cycle.end_date) : dayjs()
        });
      }
    }
  }, [selectedCycle, cycles]);

  const loadCycles = async () => {
    try {
      const data = await cyclesAPI.getAll();
      setCycles(data);
      // Auto-select first cycle if available
      if (data.length > 0 && !selectedCycle) {
        setSelectedCycle(data[0].id);
      }
    } catch (error) {
      console.error('Error loading cycles:', error);
    }
  };

  const handleRefreshQR = async () => {
    try {
      const response = await notificationsAPI.initWhatsApp();
      if (response.status === "qr_ready") {
        setQrCode(response.qr);
        setQrRefreshCount((prev) => prev + 1);
        setMessage({ type: "info", text: "🔄 QR actualizado" });
      }
    } catch (error) {
      console.error("Error refreshing QR:", error);
    }
  };

  const handleInitWhatsApp = async () => {
    setLoading(true);
    setMessage(null);
    setQrRefreshCount(0);
    try {
      const response = await notificationsAPI.initWhatsApp();

      if (response.status === "already_logged_in") {
        setLoggedIn(true);
        setMessage({
          type: "success",
          text: "✓ Ya estás logueado en WhatsApp",
        });
      } else if (response.status === "qr_ready") {
        setQrCode(response.qr);
        setMessage({ type: "info", text: "📱 Escanea el QR con tu teléfono" });
      }
    } catch (error) {
      setMessage({ type: "error", text: `Error: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyLogin = async () => {
    setLoading(true);
    try {
      const response = await notificationsAPI.verifyWhatsApp();

      if (response.logged_in) {
        setLoggedIn(true);
        setQrCode(null);
        setMessage({
          type: "success",
          text: "✓ Login verificado exitosamente",
        });
      } else {
        setMessage({ type: "error", text: "✗ Aún no has escaneado el QR" });
      }
    } catch (error) {
      setMessage({ type: "error", text: `Error: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleSendTest = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const response = await notificationsAPI.testWhatsApp("969728039");

      if (response.status === "success") {
        setMessage({
          type: "success",
          text: `✓ Mensaje enviado a ${response.phone}`,
        });
      } else {
        setMessage({ type: "error", text: `✗ Error: ${response.message}` });
      }
    } catch (error) {
      setMessage({ type: "error", text: `Error: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSession = async () => {
    setLoading(true);
    try {
      await notificationsAPI.closeWhatsApp();
      setQrCode(null);
      setLoggedIn(false);
      setScanned(false);
      setQrRefreshCount(0);
      setMessage({ type: "info", text: "Sesión cerrada" });
    } catch (error) {
      setMessage({ type: "error", text: `Error: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  // Payment notification handlers
  const handleValidateRejected = async () => {
    setLoadingPayments(true);
    setMessage(null);
    try {
      const data = await notificationsAPI.getPaymentsRejected();
      setRejectedPayments(data);
      setMessage({
        type: "success",
        text: `✓ ${data.length} pagos rechazados encontrados`,
      });
    } catch (error) {
      setMessage({ type: "error", text: `Error: ${error.message}` });
    } finally {
      setLoadingPayments(false);
    }
  };

  const handleValidateAccepted = async () => {
    setLoadingPayments(true);
    setMessage(null);
    try {
      const data = await notificationsAPI.getPaymentsAccepted();
      setAcceptedPayments(data);
      setMessage({
        type: "success",
        text: `✓ ${data.length} pagos aceptados encontrados`,
      });
    } catch (error) {
      setMessage({ type: "error", text: `Error: ${error.message}` });
    } finally {
      setLoadingPayments(false);
    }
  };

  const handleSendNotifications = async (type, payments) => {
    if (!loggedIn) {
      setMessage({
        type: "error",
        text: "Debes iniciar sesión en WhatsApp primero",
      });
      return;
    }

    if (payments.length === 0) {
      setMessage({ type: "error", text: "No hay pagos para notificar" });
      return;
    }

    if (!window.confirm(`¿Enviar ${payments.length} notificaciones?`)) {
      return;
    }

    setSendingNotifications(true);
    setMessage(null);

    try {
      const response = await notificationsAPI.sendPaymentNotifications(
        type,
        payments
      );

      const successCount = response.results.filter(
        (r) => r.status === "success"
      ).length;
      const errorCount = response.results.filter(
        (r) => r.status === "error"
      ).length;

      setMessage({
        type: successCount > 0 ? "success" : "error",
        text: `✓ ${successCount} enviados, ✗ ${errorCount} fallidos`,
      });

      // Clear the list after sending
      if (type === "rejected") {
        setRejectedPayments([]);
      } else {
        setAcceptedPayments([]);
      }
    } catch (error) {
      setMessage({ type: "error", text: `Error: ${error.message}` });
    } finally {
      setSendingNotifications(false);
    }
  };

  // Attendance notification handlers
  const handleSearchAttendance = async () => {
    if (!selectedCycle || !selectedDate || !selectedGroup) {
      setMessage({ type: 'error', text: 'Debe seleccionar ciclo, fecha y grupo' });
      return;
    }

    setLoadingAttendance(true);
    setMessage(null);

    try {
      const data = await adminAPI.getAttendanceNotifications(
        selectedCycle,
        selectedDate.format('YYYY-MM-DD'),
        selectedGroup
      );
      setAttendanceStudents(data);

      if (data.length === 0) {
        setMessage({ type: 'info', text: 'No se encontraron ausencias para los filtros seleccionados' });
      } else {
        setMessage({ type: 'success', text: `✓ ${data.length} estudiantes con ausencias encontrados` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Error: ${error.message}` });
      setAttendanceStudents([]);
    } finally {
      setLoadingAttendance(false);
    }
  };

  const handleSendAttendanceNotifications = async () => {
    if (!loggedIn) {
      setMessage({ type: 'error', text: 'Debes iniciar sesión en WhatsApp primero' });
      return;
    }

    const withPhone = attendanceStudents.filter(s => s.phone_to_use).length;
    if (withPhone === 0) {
      setMessage({ type: 'error', text: 'No hay estudiantes con teléfono para notificar' });
      return;
    }

    const withoutPhone = attendanceStudents.length - withPhone;
    const confirmMsg = `¿Enviar ${withPhone} notificaciones?${withoutPhone > 0 ? ` (${withoutPhone} sin teléfono serán omitidos)` : ''}`;

    if (!window.confirm(confirmMsg)) {
      return;
    }

    setSendingAttendance(true);
    setMessage(null);

    try {
      const result = await adminAPI.sendAttendanceNotifications(
        selectedCycle,
        selectedDate.format('YYYY-MM-DD'),
        selectedGroup
      );

      setMessage({
        type: result.success > 0 ? 'success' : 'error',
        text: `✓ ${result.success} enviados, ✗ ${result.errors} fallidos`
      });

      // Clear list after sending
      setAttendanceStudents([]);
      setSelectedGroup('');
    } catch (error) {
      setMessage({ type: 'error', text: `Error: ${error.message}` });
    } finally {
      setSendingAttendance(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        📱 Notificaciones WhatsApp
      </Typography>

      <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} sx={{ mb: 3 }}>
        <Tab label="WhatsApp Login" />
        <Tab label="Pagos Rechazados" />
        <Tab label="Pagos Aceptados" />
        <Tab label="Asistencias" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Iniciar Sesión WhatsApp
            </Typography>

            {/* Advertencia */}
            <Alert severity="warning" sx={{ mb: 3 }}>
              <strong>⚠️ IMPORTANTE:</strong>
              <ul style={{ margin: "8px 0", paddingLeft: "20px" }}>
                <li>Cierra WhatsApp Web en otros dispositivos</li>
                <li>Escanea el QR con tu teléfono</li>
                <li>El QR se actualiza cada 60 segundos</li>
                <li>No cierres esta ventana hasta terminar el envío</li>
              </ul>
            </Alert>

            {/* Mensajes */}
            {message && tabValue === 0 && (
              <Alert severity={message.type} sx={{ mb: 2 }}>
                {message.text}
              </Alert>
            )}

            {/* QR Code */}
            {qrCode && (
              <Box sx={{ textAlign: "center", mb: 3 }}>
                <img
                  src={`data:image/png;base64,${qrCode}`}
                  alt="QR Code"
                  style={{
                    width: "400px",
                    height: "400px",
                    border: "2px solid #ccc",
                    borderRadius: "8px",
                    objectFit: "contain",
                  }}
                />
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  Actualización automática en 60s
                </Typography>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={scanned}
                      onChange={(e) => setScanned(e.target.checked)}
                    />
                  }
                  label="Ya escaneé el QR"
                  sx={{ mt: 2, display: "block" }}
                />
              </Box>
            )}

            {/* Botones */}
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
              {!qrCode && !loggedIn && (
                <Button
                  variant="contained"
                  onClick={handleInitWhatsApp}
                  disabled={loading}
                  startIcon={loading && <CircularProgress size={20} />}
                >
                  Iniciar WhatsApp
                </Button>
              )}

              {qrCode && scanned && (
                <Button
                  variant="contained"
                  color="success"
                  onClick={handleVerifyLogin}
                  disabled={loading}
                >
                  Verificar Login
                </Button>
              )}

              {loggedIn && (
                <>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleSendTest}
                    disabled={loading}
                  >
                    Enviar Mensaje de Prueba
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={handleCloseSession}
                    disabled={loading}
                  >
                    Cerrar Sesión
                  </Button>
                </>
              )}
            </Box>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              🚫 Notificar Pagos Rechazados
            </Typography>

            {message && tabValue === 1 && (
              <Alert severity={message.type} sx={{ mb: 2 }}>
                {message.text}
              </Alert>
            )}

            <Box sx={{ mb: 3 }}>
              <Button
                variant="outlined"
                onClick={handleValidateRejected}
                disabled={loadingPayments || sendingNotifications}
                startIcon={loadingPayments && <CircularProgress size={20} />}
              >
                Validar Lista de Rechazados
              </Button>
            </Box>

            {rejectedPayments.length > 0 && (
              <>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  Total: {rejectedPayments.length} pagos rechazados (últimos 30
                  días)
                </Typography>
                <TableContainer
                  component={Paper}
                  sx={{ maxHeight: 400, mb: 2 }}
                >
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Estudiante</TableCell>
                        <TableCell>Apoderado</TableCell>
                        <TableCell>Teléfono</TableCell>
                        <TableCell>Curso</TableCell>
                        <TableCell align="right">Monto</TableCell>
                        <TableCell>Motivo</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {rejectedPayments.map((payment, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{payment.student_name}</TableCell>
                          <TableCell>{payment.parent_name}</TableCell>
                          <TableCell>{payment.parent_phone}</TableCell>
                          <TableCell>{payment.course_name}</TableCell>
                          <TableCell align="right">
                            S/ {payment.amount}
                          </TableCell>
                          <TableCell sx={{ fontSize: "0.85em" }}>
                            {payment.rejection_reason || "N/A"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                <Button
                  variant="contained"
                  color="error"
                  onClick={() =>
                    handleSendNotifications("rejected", rejectedPayments)
                  }
                  disabled={!loggedIn || sendingNotifications}
                  startIcon={
                    sendingNotifications && <CircularProgress size={20} />
                  }
                >
                  {sendingNotifications
                    ? "Enviando..."
                    : "Enviar Notificaciones"}
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              ✅ Notificar Pagos Aceptados
            </Typography>

            {message && tabValue === 2 && (
              <Alert severity={message.type} sx={{ mb: 2 }}>
                {message.text}
              </Alert>
            )}

            <Box sx={{ mb: 3 }}>
              <Button
                variant="outlined"
                onClick={handleValidateAccepted}
                disabled={loadingPayments || sendingNotifications}
                startIcon={loadingPayments && <CircularProgress size={20} />}
              >
                Validar Lista de Aceptados
              </Button>
            </Box>

            {acceptedPayments.length > 0 && (
              <>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  Total: {acceptedPayments.length} pagos aceptados (últimos 7
                  días)
                </Typography>
                <TableContainer
                  component={Paper}
                  sx={{ maxHeight: 400, mb: 2 }}
                >
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Estudiante</TableCell>
                        <TableCell>Apoderado</TableCell>
                        <TableCell>Teléfono</TableCell>
                        <TableCell>Curso</TableCell>
                        <TableCell align="right">Monto</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {acceptedPayments.map((payment, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{payment.student_name}</TableCell>
                          <TableCell>{payment.parent_name}</TableCell>
                          <TableCell>{payment.parent_phone}</TableCell>
                          <TableCell>{payment.course_name}</TableCell>
                          <TableCell align="right">
                            S/ {payment.amount}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                <Button
                  variant="contained"
                  color="success"
                  onClick={() =>
                    handleSendNotifications("accepted", acceptedPayments)
                  }
                  disabled={!loggedIn || sendingNotifications}
                  startIcon={
                    sendingNotifications && <CircularProgress size={20} />
                  }
                >
                  {sendingNotifications
                    ? "Enviando..."
                    : "Enviar Notificaciones"}
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📅 Notificar Asistencias
            </Typography>

            {message && tabValue === 3 && (
              <Alert severity={message.type} sx={{ mb: 2 }}>
                {message.text}
              </Alert>
            )}

            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  select
                  fullWidth
                  label="Ciclo"
                  value={selectedCycle}
                  onChange={(e) => setSelectedCycle(e.target.value)}
                  size="small"
                >
                  <MenuItem value="">-- Seleccione --</MenuItem>
                  {cycles.map(c => (
                    <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                  ))}
                </TextField>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="es">
                  <DatePicker
                    label="Fecha"
                    value={selectedDate}
                    onChange={(newValue) => {
                      if (newValue) {
                        setSelectedDate(newValue);
                      }
                    }}
                    format="DD/MM/YYYY"
                    minDate={dateRange.min}
                    maxDate={dateRange.max}
                    slotProps={{
                      textField: {
                        size: 'small',
                        fullWidth: true,
                      },
                    }}
                  />
                </LocalizationProvider>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  select
                  fullWidth
                  label="Grupo"
                  value={selectedGroup}
                  onChange={(e) => setSelectedGroup(e.target.value)}
                  size="small"
                >
                  <MenuItem value="">-- Seleccione --</MenuItem>
                  {groups.map(g => (
                    <MenuItem key={g} value={g}>Grupo {g}</MenuItem>
                  ))}
                </TextField>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={handleSearchAttendance}
                  disabled={loadingAttendance || sendingAttendance || !selectedCycle || !selectedDate || !selectedGroup}
                  startIcon={loadingAttendance && <CircularProgress size={20} />}
                >
                  Buscar Ausencias
                </Button>
              </Grid>
            </Grid>

            {attendanceStudents.length > 0 && (
              <>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  Total: {attendanceStudents.filter(s => s.phone_to_use).length} estudiantes recibirán notificación
                  {attendanceStudents.filter(s => !s.phone_to_use).length > 0 &&
                    `, ${attendanceStudents.filter(s => !s.phone_to_use).length} sin teléfono`
                  }
                </Typography>
                <TableContainer component={Paper} sx={{ maxHeight: 400, mb: 2 }}>
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>DNI</TableCell>
                        <TableCell>Estudiante</TableCell>
                        <TableCell>Teléfono</TableCell>
                        <TableCell>Tipo</TableCell>
                        <TableCell>Cursos Ausentes</TableCell>
                        <TableCell>Cantidad</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {attendanceStudents.map(student => (
                        <TableRow key={student.student_id}>
                          <TableCell>{student.dni}</TableCell>
                          <TableCell>{student.first_name} {student.last_name}</TableCell>
                          <TableCell>{student.phone_to_use || 'Sin teléfono'}</TableCell>
                          <TableCell>
                            {student.phone_type === 'parent' ? 'Padre' :
                              student.phone_type === 'student' ? 'Estudiante' : '-'}
                          </TableCell>
                          <TableCell>{student.absent_courses?.join(', ')}</TableCell>
                          <TableCell>{student.absence_count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleSendAttendanceNotifications}
                  disabled={!loggedIn || sendingAttendance || attendanceStudents.filter(s => s.phone_to_use).length === 0}
                  startIcon={sendingAttendance && <CircularProgress size={20} />}
                >
                  {sendingAttendance ? 'Enviando...' : 'Enviar Notificaciones'}
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
}
