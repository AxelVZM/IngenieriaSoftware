// src/components/student/StudentAvailableCourses.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
  IconButton,
  Avatar,
  Divider,
  Paper
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterListIcon,
  School as SchoolIcon,
  Inventory2 as PackageIcon,
  CheckCircle as CheckCircleIcon,
  AddCircleOutline as AddIcon,
  RemoveCircleOutline as RemoveIcon,
  Payment as PaymentIcon,
  AccountBalance as BankIcon
} from '@mui/icons-material';
import { coursesAPI, packagesAPI, cyclesAPI, enrollmentsAPI, schedulesAPI } from '../../services/api';
import './student-dashboard.css';

const StudentAvailableCourses = () => {
  const navigate = useNavigate();

  // --- ESTADOS DE DATOS ---
  const [courses, setCourses] = useState([]);
  const [packages, setPackages] = useState([]);
  const [cycles, setCycles] = useState([]);

  // Información bancaria para pagos
  const BANK_INFO = {
    bank: 'Caja Cusco',
    accountNumber: '500-8924567-0-23',
    accountHolder: 'Academia UNI',
    accountType: 'Cuenta de Ahorros'
  };

  // --- ESTADOS DE UI/FILTROS ---
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0); // 0: Cursos, 1: Paquetes
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCycleId, setSelectedCycleId] = useState('all'); // 'all' o cycle_id

  // --- ESTADOS DE SELECCIÓN Y MATRÍCULA ---
  const [selectedItems, setSelectedItems] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [schedulesPreview, setSchedulesPreview] = useState({});
  const [loadingSchedules, setLoadingSchedules] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [coursesData, packagesData, cyclesData, packageOfferingsData] = await Promise.all([
        coursesAPI.getAll(),
        packagesAPI.getAll(),
        cyclesAPI.getActive().catch(() => []),
        packagesAPI.getOfferings().catch(() => []),
      ]);

      // Los cursos de la API ya vienen con sus offerings incluidas
      // Solo nos aseguramos de que tengan el campo offerings
      const coursesWithOfferings = coursesData.map(course => ({
        ...course,
        offerings: course.offerings || []
      }));
      setCourses(coursesWithOfferings);
      setCycles(Array.isArray(cyclesData) ? cyclesData : []);

      // Vincular ofertas a paquetes
      const packagesWithOfferings = packagesData.map(pkg => {
        const offerings = packageOfferingsData.filter(po => po.package_id === pkg.id);
        return { ...pkg, offerings };
      });
      setPackages(packagesWithOfferings);

      // Auto-seleccionar el ciclo más reciente si existe
      if (cyclesData.length > 0) {
        // Opcional: setSelectedCycleId(cyclesData[0].id);
      }
    } catch (err) {
      console.error('Error cargando datos:', err);
      setError('Error al cargar cursos disponibles');
    } finally {
      setLoading(false);
    }
  };

  // --- LÓGICA DE FILTRADO ---
  const getFilteredItems = () => {
    let items = [];

    if (tabValue === 0) {
      // PROCESAR CURSOS
      courses.forEach(course => {
        if (!course.offerings) return;
        course.offerings.forEach(offering => {
          // Filtro por Ciclo
          if (selectedCycleId !== 'all' && offering.cycle_id !== selectedCycleId) return;

          // Filtro por Buscador
          const searchMatch =
            course.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (course.description && course.description.toLowerCase().includes(searchTerm.toLowerCase()));

          if (!searchMatch) return;

          items.push({
            type: 'course',
            id: offering.id,
            name: course.name,
            description: course.description,
            price: offering.price_override || course.base_price,
            cycle_name: offering.cycle_name,
            cycle_start: offering.cycle_start_date,
            cycle_end: offering.cycle_end_date,
            group: offering.group_label,
            teacher: offering.first_name ? `${offering.first_name} ${offering.last_name}` : null
          });
        });
      });
    } else {
      // PROCESAR PAQUETES
      packages.forEach(pkg => {
        if (!pkg.offerings) return;
        pkg.offerings.forEach(offering => {
          if (selectedCycleId !== 'all' && offering.cycle_id !== selectedCycleId) return;

          const searchMatch =
            pkg.name.toLowerCase().includes(searchTerm.toLowerCase());

          if (!searchMatch) return;

          items.push({
            type: 'package',
            id: offering.id,
            name: pkg.name,
            description: pkg.description,
            price: offering.price_override || pkg.base_price,
            cycle_name: offering.cycle_name,
            cycle_start: offering.cycle_start_date,
            cycle_end: offering.cycle_end_date,
            group: null // Paquetes suelen ser generales, o mostrar group_label si aplica
          });
        });
      });
    }
    return items;
  };

  // --- MANEJO DE SELECCIÓN ---
  const toggleSelection = (item) => {
    const key = `${item.type}-${item.id}`;
    const exists = selectedItems.find(i => i.key === key);

    if (exists) {
      setSelectedItems(selectedItems.filter(i => i.key !== key));
    } else {
      setSelectedItems([...selectedItems, { ...item, key }]);
    }
  };

  const handleEnroll = async () => {
    if (selectedItems.length === 0) return setError('Selecciona al menos un curso');

    try {
      setError('');
      const items = selectedItems.map(item => ({ type: item.type, id: item.id }));
      await enrollmentsAPI.create(items);
      setSuccess('matricula_exitosa'); // Marcador especial para mostrar info de pago
      setSelectedItems([]);
      setOpenDialog(false);
      loadData();
    } catch (err) {
      setError(err.message || 'Error al procesar la matrícula');
    }
  };

  // --- CARGA DE HORARIOS PREVIOS ---
  useEffect(() => {
    const loadSchedulesPreview = async () => {
      if (!openDialog || selectedItems.length === 0) {
        setSchedulesPreview({});
        return;
      }
      try {
        setLoadingSchedules(true);
        const results = {};
        for (const item of selectedItems) {
          try {
            const apiCall = item.type === 'course'
              ? schedulesAPI.getByCourseOffering(item.id)
              : schedulesAPI.getByPackageOffering(item.id);
            results[item.key] = await apiCall || [];
          } catch (e) { results[item.key] = []; }
        }
        setSchedulesPreview(results);
      } finally { setLoadingSchedules(false); }
    };
    loadSchedulesPreview();
  }, [openDialog, JSON.stringify(selectedItems.map(i => i.key))]);

  const total = selectedItems.reduce((sum, item) => sum + parseFloat(item.price || 0), 0);
  const filteredItems = getFilteredItems();

  if (loading) return (
    <Box className="student-loading"><CircularProgress className="student-loading-spinner" /></Box>
  );

  return (
    <Box className="student-content fade-in">

      {/* 1. HEADER Y TÍTULO */}
      <Box mb={4}>
        <Typography variant="h4" className="student-page-title">
          Catálogo Académico
        </Typography>
        <Typography color="text.secondary">
          Selecciona el ciclo y los cursos ideales para tu preparación.
        </Typography>
      </Box>

      {/* 2. BARRA DE HERRAMIENTAS (FILTROS) */}
      <Card sx={{ mb: 4, borderRadius: 3, boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}>
        <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
          <Grid container spacing={2} alignItems="center">

            {/* Buscador */}
            <Grid item xs={12} md={5}>
              <TextField
                fullWidth
                placeholder="Buscar por nombre..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <InputAdornment position="start"><SearchIcon color="action" /></InputAdornment>,
                  sx: { borderRadius: 2, bgcolor: '#f8fafc' }
                }}
                size="small"
                variant="outlined"
              />
            </Grid>

            {/* Filtro de Ciclos (Chips) */}
            <Grid item xs={12} md={7}>
              <Box display="flex" gap={1} flexWrap="wrap" alignItems="center">
                <FilterListIcon color="action" sx={{ mr: 1 }} />
                <Chip
                  label="Todos los ciclos"
                  onClick={() => setSelectedCycleId('all')}
                  className={`filter-chip ${selectedCycleId === 'all' ? 'active' : ''}`}
                />
                {cycles.map(cycle => (
                  <Chip
                    key={cycle.id}
                    label={cycle.name}
                    onClick={() => setSelectedCycleId(cycle.id)}
                    className={`filter-chip ${selectedCycleId === cycle.id ? 'active' : ''}`}
                  />
                ))}
              </Box>
            </Grid>

          </Grid>
        </CardContent>
      </Card>

      {/* 3. TABS (CURSOS vs PAQUETES) */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(e, v) => setTabValue(v)}
          className="student-tabs"
          textColor="primary"
          indicatorColor="primary"
        >
          <Tab icon={<SchoolIcon />} iconPosition="start" label="Cursos Individuales" />
          <Tab icon={<PackageIcon />} iconPosition="start" label="Paquetes Promocionales" />
        </Tabs>
      </Box>

      {/* ALERTAS */}
      {error && <Alert severity="error" className="student-alert" onClose={() => setError('')}>{error}</Alert>}
      {success && success === 'matricula_exitosa' ? (
        <Alert
          severity="success"
          className="student-alert"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => navigate('/student/my-enrollments')}
              startIcon={<PaymentIcon />}
            >
              Ir a Pagos
            </Button>
          }
        >
          <Box>
            <Typography variant="subtitle2" fontWeight={700}>¡Matrícula Exitosa!</Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Realiza tu pago a la cuenta:
            </Typography>
            <Box sx={{ mt: 1, p: 2, bgcolor: 'rgba(255,255,255,0.9)', borderRadius: 2, border: '1px solid #cbd5e1' }}>
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Banco:</Typography>
                  <Typography variant="body2" fontWeight={600}>{BANK_INFO.bank}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Tipo:</Typography>
                  <Typography variant="body2" fontWeight={600}>{BANK_INFO.accountType}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="caption" color="text.secondary">N° Cuenta:</Typography>
                  <Typography variant="body2" fontWeight={700} color="primary">{BANK_INFO.accountNumber}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="caption" color="text.secondary">Titular:</Typography>
                  <Typography variant="body2" fontWeight={600}>{BANK_INFO.accountHolder}</Typography>
                </Grid>
              </Grid>
            </Box>
          </Box>
        </Alert>
      ) : success ? (
        <Alert severity="success" className="student-alert" onClose={() => setSuccess('')}>{success}</Alert>
      ) : null}

      {/* 4. GRID DE RESULTADOS */}
      <Grid container spacing={3}>
        {filteredItems.length > 0 ? (
          filteredItems.map((item) => {
            const isSelected = selectedItems.some(i => i.key === `${item.type}-${item.id}`);
            return (
              <Grid item xs={12} sm={6} lg={4} key={`${item.type}-${item.id}`}>
                <Card className={`student-card course-card ${isSelected ? 'selected' : ''}`}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" mb={2}>
                      <Chip
                        label={item.group || 'General'}
                        size="small"
                        className="student-badge default"
                      />
                      <Chip
                        label={item.cycle_name}
                        size="small"
                        className="student-badge available"
                      />
                    </Box>

                    <Typography variant="h6" className="course-card-title">
                      {item.name}
                    </Typography>

                    <Typography variant="body2" className="course-card-desc">
                      {item.description || 'Sin descripción disponible.'}
                    </Typography>

                    {item.teacher && (
                      <Box display="flex" alignItems="center" mt={2} mb={1}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>D</Avatar>
                        <Typography variant="caption" color="text.primary" fontWeight={500}>
                          {item.teacher}
                        </Typography>
                      </Box>
                    )}

                    <Box display="flex" justifyContent="space-between" alignItems="center" mt={3}>
                      <Typography className="student-price">
                        S/. {parseFloat(item.price).toFixed(2)}
                      </Typography>

                      <Button
                        variant={isSelected ? "outlined" : "contained"}
                        color={isSelected ? "error" : "primary"}
                        startIcon={isSelected ? <RemoveIcon /> : <AddIcon />}
                        className={isSelected ? 'student-btn-remove' : 'student-btn-primary'}
                        size="small"
                        onClick={() => toggleSelection(item)}
                      >
                        {isSelected ? 'Quitar' : 'Seleccionar'}
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })
        ) : (
          <Grid item xs={12}>
            <Box className="empty-search-state">
              <SearchIcon sx={{ fontSize: 60, color: '#e2e8f0', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No encontramos cursos con esos criterios
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Intenta cambiar el ciclo o la búsqueda
              </Typography>
            </Box>
          </Grid>
        )}
      </Grid>

      {/* 5. RESUMEN FLOTANTE (STICKY FOOTER) */}
      {selectedItems.length > 0 && (
        <Box className="student-summary-box slide-up">
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="caption" color="text.secondary" display="block">
                ITEMS SELECCIONADOS ({selectedItems.length})
              </Typography>
              <Typography className="student-summary-total">
                Total: S/. {total.toFixed(2)}
              </Typography>
            </Box>
            <Button
              size="large"
              className="student-btn-primary"
              onClick={() => setOpenDialog(true)}
              endIcon={<CheckCircleIcon />}
            >
              Confirmar Matrícula
            </Button>
          </Box>
        </Box>
      )}

      {/* DIALOGO DE CONFIRMACIÓN (Manteniendo lógica original pero mejor estilo) */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle className="student-dialog-title">Resumen de Matrícula</DialogTitle>
        <DialogContent className="student-dialog-content">
          <Box mb={3}>
            {selectedItems.map(item => (
              <Box key={item.key} className="confirm-item-row">
                <Box>
                  <Typography variant="subtitle2" fontWeight={700}>{item.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {item.cycle_name} {item.group ? `• Grupo ${item.group}` : ''}
                  </Typography>
                </Box>
                <Typography fontWeight={600}>S/. {parseFloat(item.price).toFixed(2)}</Typography>
              </Box>
            ))}
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px dashed #e2e8f0', display: 'flex', justifyContent: 'space-between' }}>
              <Typography fontWeight={700}>TOTAL A PAGAR</Typography>
              <Typography fontWeight={700} color="primary" fontSize="1.1rem">
                S/. {total.toFixed(2)}
              </Typography>
            </Box>
          </Box>

          {/* Información Bancaria */}
          <Paper elevation={0} sx={{ p: 2, bgcolor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 2, mb: 2 }}>
            <Box display="flex" alignItems="center" mb={1}>
              <BankIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="subtitle2" fontWeight={700}>Información de Pago</Typography>
            </Box>
            <Divider sx={{ my: 1 }} />
            <Grid container spacing={1.5}>
              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary" display="block">Banco:</Typography>
                <Typography variant="body2" fontWeight={600}>{BANK_INFO.bank}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary" display="block">Tipo de Cuenta:</Typography>
                <Typography variant="body2" fontWeight={600}>{BANK_INFO.accountType}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary" display="block">Número de Cuenta:</Typography>
                <Typography variant="body2" fontWeight={700} color="primary">{BANK_INFO.accountNumber}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary" display="block">Titular:</Typography>
                <Typography variant="body2" fontWeight={600}>{BANK_INFO.accountHolder}</Typography>
              </Grid>
            </Grid>
            <Alert severity="info" sx={{ mt: 2, py: 0.5 }}>
              <Typography variant="caption">
                Después de confirmar, sube tu comprobante en "Mis Matrículas"
              </Typography>
            </Alert>
          </Paper>

          {/* Horarios (Mejorado para mostrar nombres de cursos en paquetes) */}
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 700 }}>📅 Horarios Previstos</Typography>
          {loadingSchedules ? (
            <Typography variant="caption">Cargando horarios...</Typography>
          ) : (
            <Box className="schedules-preview-box">
              {selectedItems.map(item => {
                const list = schedulesPreview[item.key] || [];
                if (!list.length) return null;

                // Para paquetes, agrupar por curso
                if (item.type === 'package') {
                  // Agrupar horarios por curso
                  const groupedByCourse = {};
                  list.forEach(schedule => {
                    const courseName = schedule.course_name || 'Sin nombre';
                    if (!groupedByCourse[courseName]) {
                      groupedByCourse[courseName] = [];
                    }
                    groupedByCourse[courseName].push(schedule);
                  });

                  return (
                    <Box key={item.key} mb={2} sx={{ pl: 1, borderLeft: '3px solid #6366f1' }}>
                      <Typography variant="caption" fontWeight={700} color="primary" display="block" sx={{ mb: 0.5 }}>
                        {item.name}
                      </Typography>
                      {Object.entries(groupedByCourse).map(([courseName, schedules]) => (
                        <Box key={courseName} mb={1} sx={{ ml: 1 }}>
                          <Typography variant="caption" fontWeight={600} color="text.primary" display="block">
                            • {courseName}
                          </Typography>
                          {schedules.map((s, i) => (
                            <Typography key={i} variant="caption" display="block" sx={{ ml: 2, color: '#64748b' }}>
                              - {s.day_of_week}: {s.start_time?.slice(0, 5)} - {s.end_time?.slice(0, 5)}
                            </Typography>
                          ))}
                        </Box>
                      ))}
                    </Box>
                  );
                }

                // Para cursos individuales, mostrar directamente
                return (
                  <Box key={item.key} mb={1}>
                    <Typography variant="caption" fontWeight={700} color="primary">{item.name}</Typography>
                    {list.map((s, i) => (
                      <Typography key={i} variant="caption" display="block" sx={{ ml: 1, color: '#64748b' }}>
                        • {s.day_of_week}: {s.start_time?.slice(0, 5)} - {s.end_time?.slice(0, 5)}
                      </Typography>
                    ))}
                  </Box>
                );
              })}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: '1px solid #f1f5f9' }}>
          <Button onClick={() => setOpenDialog(false)}>Cancelar</Button>
          <Button onClick={handleEnroll} variant="contained" className="student-btn-primary">
            Confirmar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StudentAvailableCourses;