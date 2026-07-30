// src/components/landing/Header.jsx
import { useNavigate } from 'react-router-dom';
import einsteinLogo from '../../assets/Albert Einstein.jpg';
import './LandingPage.css';

const Header = () => {
    const navigate = useNavigate();

    return (
        <header className="landing-header">
            <div className="header-container">
                <div className="logo">
                    <img src={einsteinLogo} alt="Albert Einstein" className="logo-image" />
                    <span className="logo-text">Academia Unión de Nuevos Inteligentes</span>
                </div>
                <nav className="header-nav">
                    <button
                        className="btn-login"
                        onClick={() => navigate('/login')}
                    >
                        Iniciar Sesión
                    </button>
                    <button
                        className="btn-register"
                        onClick={() => navigate('/login?mode=register')}
                    >
                        Registrarse
                    </button>
                </nav>
            </div>
        </header>
    );
};

export default Header;
