// src/components/admin/UsersSectionNav.jsx
import React from "react";
import { Tabs, Tab, Box } from "@mui/material";
import { useNavigate, useLocation } from "react-router-dom";

// Fix NAV-01: antes no habia forma de moverse entre estas 3 pantallas sin
// volver al menu lateral completo. Este componente se coloca arriba de las
// tres y permite saltar directo entre ellas.
const TABS = [
  { label: "Usuarios (todos)", path: "/admin/users" },
  { label: "Estudiantes", path: "/admin/students" },
  { label: "Docentes", path: "/admin/teachers" },
];

const UsersSectionNav = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const currentIndex = TABS.findIndex((t) => location.pathname.startsWith(t.path));

  return (
    <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
      <Tabs
        value={currentIndex === -1 ? 0 : currentIndex}
        onChange={(_, newIndex) => navigate(TABS[newIndex].path)}
      >
        {TABS.map((t) => (
          <Tab key={t.path} label={t.label} />
        ))}
      </Tabs>
    </Box>
  );
};

export default UsersSectionNav;