// src/components/admin/AdminEnrollmentsComplete.jsx
//
// Correcciones aplicadas:
//   F-01  RF15 no estaba implementado. Este componente es el que monta la
//         ruta /admin/enrollments y solo mostraba matrículas ACEPTADAS,
//         sin permitir cambiar estados ni eliminar. `handleUpdateStatus`
//         existía pero no lo invocaba nada, y el endpoint
//         DELETE /enrollments/{id} no lo consumía ningún componente.
//   F-02  Se importaban Dialog, TextField, MenuItem, Button, IconButton,
//         CheckIcon, CloseIcon y VisibilityIcon sin usar ninguno.
//         `statusFilter` se declaraba sin setter y jamás se leía.
//   F-03  El Chip mostraba label="Aceptado" fijo mientras el color se
//         calculaba de forma dinámica: al ampliar el filtro, toda fila
//         aparecería etiquetada como "Aceptado" con el color equivocado.
//   F-04  `loading` se activaba pero no se renderizaba en ninguna parte.
//   F-05  Los errores se comunicaban con alert() del navegador, bloqueante
//         y sin posibilidad de copiar el mensaje.
//   F-06  No existía confirmación antes de acciones destructivas.
//   F-07  Al rechazar no se pedía motivo, pese a que el RF21 lo exige.

import React, { useEffect, useMemo, useState } from 'react';
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
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  TextField,
  MenuItem,
  Tooltip,
  Alert,
  CircularProgress,
  Stack,
  InputAdornment,
} from '@mui/material';
import {
  Check as CheckIcon,
  Close as CloseIcon,
  Delete as DeleteIcon,
  History as HistoryIcon,
  Search as SearchIcon,
  Flag as FlagIcon,
} from '@mui/icons-material';
import { enrollmentsAPI } from '../../services/api';
import './admin-dashboard.css';

// F-03: una sola fuente de verdad para etiqueta y color del estado.
const ESTADOS = {
  pendiente: { label: 'Pendiente de pago', color: 'warning' },
  aceptado: { label: 'Aceptada', color: 'success' },
  rechazado: { label: 'Rechazada', color: 'error' },
  cancelado: { label: 'Cancelada', color: 'default' },
  finalizado: { label: 'Finalizada', color: 'info' },
};

const describirEstado = (estado) =>
  ESTADOS[estado] || { label: estado || 'Sin estado', color: 'default' };

// SEM-02/UX-06: "pending" cubre dos situaciones distintas para el admin —
// el estudiante todavía no subió nada, o ya subió el voucher y espera
// revisión. El backend no tiene un estado intermedio propio, así que se
// distingue aquí con la presencia de voucher_url.
const describirPago = (matricula) => {
  if (!matricula.payment_status) return 'Sin cuota';
  if (matricula.payment_status === 'paid') return 'Pagado';
  if (matricula.payment_status === 'overdue') return 'Vencido';
  return matricula.voucher_url ? 'En revisión' : 'Sin comprobante';
};

// Refleja la máquina de estados del backend. Si el backend rechaza una
// transición, la interfaz ni siquiera debería haberla ofrecido.
const TRANSICIONES = {
  pendiente: ['aceptado', 'rechazado', 'cancelado'],
  aceptado: ['finalizado', 'cancelado'],
  rechazado: ['pendiente', 'cancelado'],
  cancelado: [],
  finalizado: [],
};

const FILTROS = [
  { valor: 'todos', etiqueta: 'Todas' },
  { valor: 'pendiente', etiqueta: 'Pendientes de pago' },
  { valor: 'aceptado', etiqueta: 'Aceptadas' },
  { valor: 'rechazado', etiqueta: 'Rechazadas' },
  { valor: 'finalizado', etiqueta: 'Finalizadas' },
  { valor: 'cancelado', etiqueta: 'Canceladas' },
];

const AdminEnrollmentsComplete = () => {
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');

  const [filtroEstado, setFiltroEstado] = useState('todos');
  const [busqueda, setBusqueda] = useState('');

  const [dialogoEstado, setDialogoEstado] = useState(null); // { matricula, destino }
  const [motivo, setMotivo] = useState('');
  const [dialogoBorrado, setDialogoBorrado] = useState(null);
  const [historial, setHistorial] = useState(null);

  useEffect(() => {
    cargarMatriculas();
  }, []);

  const cargarMatriculas = async () => {
    try {
      setLoading(true);
      setError('');
      const datos = await enrollmentsAPI.getAllAdmin();
      setEnrollments(Array.isArray(datos) ? datos : []);
    } catch (err) {
      // F-05: el error se muestra en pantalla, no en un alert bloqueante.
      setError(err.message || 'No se pudieron cargar las matrículas. Reintenta en unos segundos.');
    } finally {
      setLoading(false);
    }
  };

  const abrirCambioEstado = (matricula, destino) => {
    setMotivo('');
    setError('');
    setDialogoEstado({ matricula, destino });
  };

  const confirmarCambioEstado = async () => {
    if (!dialogoEstado) return;
    const { matricula, destino } = dialogoEstado;

    // F-07: el motivo es obligatorio al rechazar, cancelar o finalizar (RF21).
    // Finalizar antes de que termine el ciclo ("baja anticipada") ya no se
    // bloquea por fecha, pero exige motivo siempre — sin excepción, ni
    // siquiera si el ciclo ya terminó — porque el estudiante lo va a ver
    // reflejado en sus matrículas.
    const exigeMotivo = destino === 'rechazado' || destino === 'cancelado' || destino === 'finalizado';
    if (exigeMotivo && !motivo.trim()) {
      setError('Indica el motivo: el estudiante lo va a ver en su panel.');
      return;
    }

    try {
      setGuardando(true);
      setError('');
      await enrollmentsAPI.updateStatus(matricula.id, destino, motivo.trim() || null);
      setAviso(`Matrícula de ${matricula.first_name} ${matricula.last_name} marcada como «${describirEstado(destino).label}».`);
      setDialogoEstado(null);
      await cargarMatriculas();
    } catch (err) {
      setError(err.message || 'No se pudo actualizar el estado.');
    } finally {
      setGuardando(false);
    }
  };

  const confirmarBorrado = async () => {
    if (!dialogoBorrado) return;
    try {
      setGuardando(true);
      setError('');
      await enrollmentsAPI.remove(dialogoBorrado.id);
      setAviso('Matrícula eliminada.');
      setDialogoBorrado(null);
      await cargarMatriculas();
    } catch (err) {
      setError(err.message || 'No se pudo eliminar la matrícula.');
    } finally {
      setGuardando(false);
    }
  };

  const verHistorial = async (matricula) => {
    try {
      setError('');
      const datos = await enrollmentsAPI.getHistory(matricula.id);
      setHistorial({ matricula, entradas: datos });
    } catch (err) {
      setError(err.message || 'No se pudo recuperar el historial.');
    }
  };

  const filtradas = useMemo(() => {
    const texto = busqueda.trim().toLowerCase();
    return enrollments.filter((e) => {
      if (filtroEstado !== 'todos' && e.status !== filtroEstado) return false;
      if (!texto) return true;
      const campo = `${e.first_name || ''} ${e.last_name || ''} ${e.dni || ''} ${e.item_name || ''}`;
      return campo.toLowerCase().includes(texto);
    });
  }, [enrollments, filtroEstado, busqueda]);

  // F-04: el estado de carga ahora se ve.
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" py={8}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box className="admin-dashboard">
      <Typography variant="h4" gutterBottom className="admin-dashboard-title">
        Gestión de matrículas
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      {aviso && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setAviso('')}>
          {aviso}
        </Alert>
      )}

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3 }}>
        <TextField
          select
          label="Estado"
          value={filtroEstado}
          onChange={(e) => setFiltroEstado(e.target.value)}
          size="small"
          sx={{ minWidth: 220 }}
        >
          {FILTROS.map((f) => (
            <MenuItem key={f.valor} value={f.valor}>
              {f.etiqueta}
            </MenuItem>
          ))}
        </TextField>

        <TextField
          placeholder="Buscar por nombre, DNI o curso"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          size="small"
          fullWidth
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
      </Stack>

      <TableContainer component={Paper} className="admin-table-container">
        <Table className="admin-table">
          <TableHead className="admin-table-head">
            <TableRow>
              <TableCell className="admin-table-head-cell">Estudiante</TableCell>
              <TableCell className="admin-table-head-cell">DNI</TableCell>
              <TableCell className="admin-table-head-cell">Curso o paquete</TableCell>
              <TableCell className="admin-table-head-cell">Tipo</TableCell>
              <TableCell className="admin-table-head-cell">Estado</TableCell>
              <TableCell className="admin-table-head-cell">Pago</TableCell>
              <TableCell className="admin-table-head-cell" align="right">
                Acciones
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filtradas.map((matricula) => {
              const estado = describirEstado(matricula.status);
              const destinos = TRANSICIONES[matricula.status] || [];

              return (
                <TableRow key={matricula.id} className="admin-table-row">
                  <TableCell className="admin-table-cell">
                    <Typography variant="subtitle2" fontWeight="bold">
                      {matricula.first_name} {matricula.last_name}
                    </Typography>
                  </TableCell>
                  <TableCell className="admin-table-cell">{matricula.dni}</TableCell>
                  <TableCell className="admin-table-cell">
                    {matricula.item_name || '—'}
                    {matricula.group_label ? ` (Grupo ${matricula.group_label})` : ''}
                  </TableCell>
                  <TableCell className="admin-table-cell">
                    {matricula.enrollment_type === 'course'
                      ? 'Curso'
                      : matricula.enrollment_type === 'package'
                        ? 'Paquete'
                        : '—'}
                  </TableCell>
                  <TableCell className="admin-table-cell">
                    <Chip
                      label={estado.label}
                      color={estado.color}
                      size="small"
                      className="admin-chip"
                    />
                  </TableCell>
                  <TableCell className="admin-table-cell">
                    {describirPago(matricula)}
                    {matricula.voucher_url && (
                      <>
                        {' · '}
                        <a href={matricula.voucher_url} target="_blank" rel="noreferrer">
                          Ver comprobante
                        </a>
                      </>
                    )}
                  </TableCell>
                  <TableCell className="admin-table-cell" align="right">
                    <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                      {destinos.includes('aceptado') && (
                        <Tooltip title="Aceptar matrícula">
                          <IconButton
                            color="success"
                            size="small"
                            onClick={() => abrirCambioEstado(matricula, 'aceptado')}
                          >
                            <CheckIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      {destinos.includes('rechazado') && (
                        <Tooltip title="Rechazar matrícula">
                          <IconButton
                            color="error"
                            size="small"
                            onClick={() => abrirCambioEstado(matricula, 'rechazado')}
                          >
                            <CloseIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      {destinos.includes('finalizado') && (
                        <Tooltip title="Marcar como finalizada">
                          <IconButton
                            color="info"
                            size="small"
                            onClick={() => abrirCambioEstado(matricula, 'finalizado')}
                          >
                            <FlagIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Ver historial de cambios">
                        <IconButton size="small" onClick={() => verHistorial(matricula)}>
                          <HistoryIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Eliminar registro">
                        <IconButton
                          size="small"
                          onClick={() => setDialogoBorrado(matricula)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>

        {filtradas.length === 0 && (
          <Box p={4} textAlign="center">
            <Typography color="textSecondary">
              {enrollments.length === 0
                ? 'Todavía no hay matrículas registradas.'
                : 'Ninguna matrícula coincide con el filtro. Cambia el estado o borra la búsqueda.'}
            </Typography>
          </Box>
        )}
      </TableContainer>

      {/* Cambio de estado (RF15 / RF20 / RF21) */}
      <Dialog open={Boolean(dialogoEstado)} onClose={() => setDialogoEstado(null)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogoEstado && `Marcar como «${describirEstado(dialogoEstado.destino).label}»`}
        </DialogTitle>
        <DialogContent>
          {dialogoEstado && (
            <>
              <DialogContentText sx={{ mb: 2 }}>
                {dialogoEstado.matricula.first_name} {dialogoEstado.matricula.last_name} —{' '}
                {dialogoEstado.matricula.item_name}
                {dialogoEstado.matricula.enrollment_type === 'package' &&
                  ' · Los cursos incluidos en el paquete cambiarán junto con él.'}
              </DialogContentText>

              {dialogoEstado.destino === 'finalizado' && (() => {
                const finCiclo = dialogoEstado.matricula.cycle_end_date;
                const noHaTerminado = finCiclo && new Date(finCiclo) > new Date();
                return noHaTerminado ? (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    El ciclo todavía no ha terminado (termina el{' '}
                    {new Date(finCiclo).toLocaleDateString('es-PE', { timeZone: 'UTC' })}).
                    Puedes finalizar la matrícula de todas formas — es una <strong>baja
                    anticipada</strong> — pero el motivo es obligatorio y el estudiante lo
                    va a ver en su panel.
                  </Alert>
                ) : (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    {finCiclo
                      ? `El ciclo ya llegó a su fecha de fin (${new Date(finCiclo).toLocaleDateString('es-PE', { timeZone: 'UTC' })}).`
                      : 'Esta oferta no tiene un ciclo con fecha de fin registrada.'}
                  </Alert>
                );
              })()}

              <TextField
                label={
                  dialogoEstado.destino === 'rechazado' ||
                  dialogoEstado.destino === 'cancelado' ||
                  dialogoEstado.destino === 'finalizado'
                    ? 'Motivo (obligatorio)'
                    : 'Observación (opcional)'
                }
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                multiline
                rows={3}
                fullWidth
                helperText="Quedará registrado en el historial y se mostrará al estudiante."
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogoEstado(null)}>Volver</Button>
          <Button variant="contained" onClick={confirmarCambioEstado} disabled={guardando}>
            {guardando ? 'Guardando…' : 'Confirmar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* F-06: confirmación antes de eliminar */}
      <Dialog open={Boolean(dialogoBorrado)} onClose={() => setDialogoBorrado(null)}>
        <DialogTitle>Eliminar la matrícula</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Se borrará el registro de {dialogoBorrado?.first_name} {dialogoBorrado?.last_name} en{' '}
            {dialogoBorrado?.item_name}, junto con su plan de pago. La acción no se puede deshacer.
            Si solo quieres dar de baja al estudiante, usa «Cancelada» y conservarás el historial.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogoBorrado(null)}>Volver</Button>
          <Button color="error" variant="contained" onClick={confirmarBorrado} disabled={guardando}>
            {guardando ? 'Eliminando…' : 'Eliminar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Historial de cambios (RNF15) */}
      <Dialog open={Boolean(historial)} onClose={() => setHistorial(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Historial de la matrícula</DialogTitle>
        <DialogContent>
          {historial?.entradas?.length ? (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Fecha</TableCell>
                  <TableCell>Cambio</TableCell>
                  <TableCell>Autor</TableCell>
                  <TableCell>Motivo</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {historial.entradas.map((h, i) => (
                  <TableRow key={i}>
                    <TableCell>{new Date(h.changed_at).toLocaleString()}</TableCell>
                    <TableCell>
                      {h.previous_status ? describirEstado(h.previous_status).label : 'Alta'} →{' '}
                      {describirEstado(h.new_status).label}
                    </TableCell>
                    <TableCell>{h.changed_by_role || '—'}</TableCell>
                    <TableCell>{h.reason || '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <DialogContentText>Esta matrícula no registra cambios de estado.</DialogContentText>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistorial(null)}>Cerrar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminEnrollmentsComplete;