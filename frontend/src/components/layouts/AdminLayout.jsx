// src/components/layouts/AdminLayout.jsx
import React, { useState } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  School as SchoolIcon,
  People as PeopleIcon,
  PersonOutline as PersonOutlineIcon,
  Assignment as AssignmentIcon,
  Payment as PaymentIcon,
  Schedule as ScheduleIcon,
  Inventory as InventoryIcon,
  CalendarToday as CalendarIcon,
  ExitToApp as LogoutIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import './admin-layout.css';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/admin/dashboard' },
  { text: 'Ciclos', icon: <CalendarIcon />, path: '/admin/cycles' },
  { text: 'Cursos', icon: <SchoolIcon />, path: '/admin/courses' },
  { text: 'Paquetes', icon: <InventoryIcon />, path: '/admin/packages' },
  { text: 'Docentes', icon: <PeopleIcon />, path: '/admin/teachers' },
  { text: 'Usuarios', icon: <PersonOutlineIcon />, path: '/admin/users' },
  { text: 'Estudiantes', icon: <PeopleIcon />, path: '/admin/students' },
  { text: 'Matrículas', icon: <AssignmentIcon />, path: '/admin/enrollments' },
  { text: 'Pagos', icon: <PaymentIcon />, path: '/admin/payments' },
  { text: 'Horarios', icon: <ScheduleIcon />, path: '/admin/schedules' },
  { text: 'Notificaciones', icon: <NotificationsIcon />, path: '/admin/notifications' },
];

const AdminLayout = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleLogout = () => {
    logout();
  };

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap component="div" className="admin-drawer-title">
          Admin Panel
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              className="admin-menu-item"
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                if (isMobile) setMobileOpen(false);
              }}
            >
              <ListItemIcon className="admin-menu-icon">{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} className="admin-menu-text" />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Divider />
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={handleLogout} className="admin-logout-item">
            <ListItemIcon className="admin-menu-icon">
              <LogoutIcon />
            </ListItemIcon>
            <ListItemText primary="Cerrar Sesión" />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        className="admin-appbar"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            className="admin-menu-button"
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }} className="admin-appbar-title">
            Sistema de Academia - Administrador
          </Typography>
          <Typography variant="body2" className="admin-appbar-user">
            {user?.username || user?.name || 'Admin'}
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          className="admin-drawer"
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          className="admin-drawer"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};

export default AdminLayout;

