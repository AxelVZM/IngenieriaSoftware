// src/components/auth/Register.jsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Register = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to login page which now contains both login and register
    navigate('/login');
  }, [navigate]);

  return null;
};

export default Register;