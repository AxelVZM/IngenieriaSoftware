// src/components/landing/LandingPage.jsx
import { useNavigate } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';
import './LandingPage.css';

const LandingPage = () => {
    const navigate = useNavigate();

    return (
        <div className="landing-page">
            <Header />

            <main className="landing-main">
                {/* Hero Section */}
                <section className="hero-section">
                    <div className="hero-content">
                        <div className="hero-badge">
                            <span className="badge-icon">⭐</span>
                            <span>La Mejor Academia de Preparación Universitaria</span>
                        </div>

                        <h1 className="hero-title">
                            Únete a la Academia
                            <span className="gradient-text"> Líder en Preparación</span>
                            <br />
                            Universitaria
                        </h1>

                        <p className="hero-subtitle">
                            Alcanza tus metas académicas con los mejores docentes, metodología innovadora
                            y un ambiente de excelencia. Tu éxito comienza aquí.
                        </p>

                        <div className="hero-buttons">
                            <button
                                className="btn-primary-large"
                                onClick={() => navigate('/login?mode=register')}
                            >
                                Comienza Ahora
                                <span className="btn-arrow">→</span>
                            </button>
                            <button
                                className="btn-secondary-large"
                                onClick={() => navigate('/login')}
                            >
                                Iniciar Sesión
                            </button>
                        </div>

                        <div className="hero-stats">
                            <div className="stat-item">
                                <div className="stat-number">150+</div>
                                <div className="stat-label">Ingresantes a la UNSAAC y otras universidades del pais</div>
                            </div>
                            <div className="stat-divider"></div>
                            <div className="stat-item">
                                <div className="stat-number">95%</div>
                                <div className="stat-label">Tasa de Éxito</div>
                            </div>
                            <div className="stat-divider"></div>
                            <div className="stat-item">
                                <div className="stat-number">20+</div>
                                <div className="stat-label">Docentes Expertos</div>
                            </div>
                        </div>
                    </div>

                    <div className="hero-decoration">
                        <div className="floating-card card-1">
                            <div className="card-icon">📚</div>
                            <div className="card-text">Cursos Pre Universitarios</div>
                        </div>
                        <div className="floating-card card-2">
                            <div className="card-icon">🏆</div>
                            <div className="card-text">Excelencia Académica</div>
                        </div>
                        <div className="floating-card card-3">
                            <div className="card-icon">👨‍🏫</div>
                            <div className="card-text">Docentes Calificados</div>
                        </div>
                    </div>
                </section>

                {/* Features Section */}
                <section className="features-section">
                    <h2 className="section-title">¿Por Qué Elegirnos?</h2>
                    <div className="features-grid">
                        <div className="feature-card">
                            <div className="feature-icon">🎯</div>
                            <h3>Metodología Efectiva</h3>
                            <p>Metodologia de enseñanza reconocida por la Universidad Peruana Cayetano Heredia</p>
                        </div>
                        <div className="feature-card">
                            <div className="feature-icon">💻</div>
                            <h3>Plataforma Digital</h3>
                            <p>Accede a tus matriculas y horarios desde la red</p>
                        </div>
                        <div className="feature-card">
                            <div className="feature-icon">📊</div>
                            <h3>Monitoreo Constante</h3>
                            <p>Control de Disciplina y Monitoreo constante de los Alumnos</p>
                        </div>
                        <div className="feature-card">
                            <div className="feature-icon">🌟</div>
                            <h3>Horarios Flexibles</h3>
                            <p>Elige el horario que mejor se adapte a tu rutina</p>
                        </div>
                    </div>
                </section>
            </main>

            <Footer />
        </div>
    );
};

export default LandingPage;
