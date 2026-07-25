import { Box, Typography, Container, Paper, Divider, Button } from '@mui/material';
import { Link } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';
import './LandingPage.css';

const PageLayout = ({ title, children }) => (
    <Box className="landing-container">
        <Header />
        <Box sx={{
            pt: 15,
            pb: 8,
            minHeight: '80vh',
            background: 'linear-gradient(135deg, #000000 0%, #1a1a1a 100%)',
            color: '#ffffff'
        }}>
            <Container maxWidth="md">
                <Paper
                    elevation={3}
                    sx={{
                        p: { xs: 3, md: 6 },
                        borderRadius: 4,
                        background: 'rgba(255, 255, 255, 0.03)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        color: '#ffffff'
                    }}
                >
                    <Typography
                        variant="h3"
                        component="h1"
                        gutterBottom
                        sx={{
                            fontWeight: 700,
                            background: 'linear-gradient(90deg, #ffffff 0%, #a1a1a1 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent'
                        }}
                    >
                        {title}
                    </Typography>
                    <Divider sx={{ mb: 4, borderColor: 'rgba(255, 255, 255, 0.1)' }} />
                    <Box className="info-content" sx={{ '& p, & li': { color: '#e0e0e0' } }}>
                        {children}
                    </Box>
                    <Box sx={{ mt: 4, textAlign: 'center' }}>
                        <Button
                            component={Link}
                            to="/"
                            variant="outlined"
                            sx={{
                                color: '#ffffff',
                                borderColor: '#ffffff',
                                '&:hover': { borderColor: '#a1a1a1', background: 'rgba(255, 255, 255, 0.05)' }
                            }}
                        >
                            Volver al Inicio
                        </Button>
                    </Box>
                </Paper>
            </Container>
        </Box>
        <Footer />
    </Box>
);

export const AboutPage = () => (
    <PageLayout title="Acerca de Nosotros">
        <Typography variant="h6" gutterBottom>Nuestra Historia</Typography>
        <Typography paragraph>
            La Academia "Unión de Nuevos Inteligentes" nació en la ciudad Imperial del Cusco con un propósito claro: brindar la mejor preparación académica a los jóvenes que aspiran a ingresar a las universidades más prestigiosas del país.
        </Typography>
        <Typography variant="h6" gutterBottom>Nuestra Misión</Typography>
        <Typography paragraph>
            Formar estudiantes con una base sólida de conocimientos, valores éticos y la disciplina necesaria para enfrentar con éxito los retos de la vida universitaria y profesional.
        </Typography>
        <Typography variant="h6" gutterBottom>¿Por qué elegirnos?</Typography>
        <ul>
            <li>Plana docente de primer nivel con amplia experiencia.</li>
            <li>Material didáctico actualizado y especializado.</li>
            <li>Simulacros periódicos tipo examen de admisión.</li>
            <li>Asesoría psicopedagógica personalizada.</li>
        </ul>
    </PageLayout>
);

export const CoursesPage = () => (
    <PageLayout title="Nuestros Cursos">
        <Typography paragraph>Ofrecemos una amplia gama de cursos diseñados para cubrir todos los temas fundamentales exigidos en los exámenes de admisión:</Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 3, mt: 3 }}>
            <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="h6">Matemáticas</Typography>
                <Typography variant="body2">Aritmética, Álgebra, Geometría y Trigonometría.</Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="h6">Lenguaje y Literatura</Typography>
                <Typography variant="body2">Comunicación, Competencia Lingüística y Literatura.</Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="h6">Ciencias</Typography>
                <Typography variant="body2">Física, Química, Biología y Anatomía.</Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="h6">Humanidades</Typography>
                <Typography variant="body2">Historia, Geografía, Cívica, Filosofía y Psicología.</Typography>
            </Paper>
        </Box>
    </PageLayout>
);

export const TeachersPage = () => (
    <PageLayout title="Plana Docente">
        <Typography paragraph>Contamos con los mejores profesionales, dedicados exclusivamente a la formación de futuros universitarios. Nuestro éxito se basa en su experiencia y metodología.</Typography>
        <Typography paragraph>
            Nuestros docentes son egresados de las mejores universidades del país y cuentan con años de experiencia en la preparación preuniversitaria, asegurando que cada sesión sea dinámica y productiva.
        </Typography>
    </PageLayout>
);

export const TestimonialsPage = () => (
    <PageLayout title="Testimonios">
        <Typography variant="h6" gutterBottom>Lo que dicen nuestros alumnos</Typography>
        <Box sx={{ mt: 3 }}>
            {[
                { name: "Carlos M.", text: "Gracias a la Academia UNI logré mi ingreso a Ingeniería Civil en el primer intento. La plana docente es increíble.", school: "UNSAAC" },
                { name: "Lucía P.", text: "La metodología de enseñanza y los simulacros me ayudaron a ganar confianza. ¡Totalmente recomendados!", school: "UNSAAC" },
                { name: "Jorge R.", text: "Excelente preparación no solo académica sino también emocional. El apoyo de los tutores fue fundamental.", school: "UNSAAC" }
            ].map((t, idx) => (
                <Paper key={idx} sx={{ p: 3, mb: 2, bgcolor: 'rgba(25, 118, 210, 0.05)' }}>
                    <Typography variant="body1" fontStyle="italic">"{t.text}"</Typography>
                    <Typography variant="subtitle2" sx={{ mt: 1, textAlign: 'right', fontWeight: 'bold' }}>- {t.name} (Ingresante a {t.school})</Typography>
                </Paper>
            ))}
        </Box>
    </PageLayout>
);

export const TermsPage = () => (
    <PageLayout title="Términos y Condiciones">
        <Typography variant="h6">1. Aceptación de Términos</Typography>
        <Typography paragraph>Al acceder a nuestro sitio web y utilizar los servicios de la Academia UNI, usted acepta cumplir con estos términos y condiciones.</Typography>
        <Typography variant="h6">2. Uso del Servicio</Typography>
        <Typography paragraph>Nuestros servicios están destinados exclusivamente para fines educativos. Cualquier uso indebido de los materiales o del sitio web resultará en la cancelación del acceso.</Typography>
        <Typography variant="h6">3. Matrícula y Pagos</Typography>
        <Typography paragraph>El proceso de matrícula se completa una vez verificado el pago correspondiente. No se realizan devoluciones salvo casos excepcionales analizados por administración.</Typography>
    </PageLayout>
);

export const PrivacyPage = () => (
    <PageLayout title="Política de Privacidad">
        <Typography paragraph>En la Academia UNI, protegemos su privacidad. Sus datos personales se utilizan únicamente para:</Typography>
        <ul>
            <li>Gestionar su matrícula y récord académico.</li>
            <li>Enviar información sobre cursos y eventos institucionales.</li>
            <li>Cumplir con requerimientos legales de entes educativos.</li>
        </ul>
        <Typography paragraph>No compartimos su información con terceros sin su consentimiento expreso.</Typography>
    </PageLayout>
);

export const CookiesPage = () => (
    <PageLayout title="Política de Cookies">
        <Typography paragraph>Utilizamos cookies para mejorar su experiencia en nuestra plataforma. Las cookies nos permiten recordar sus preferencias y entender cómo utiliza nuestro sitio.</Typography>
        <Typography paragraph>Usted puede configurar su navegador para rechazar todas las cookies, pero esto podría afectar la funcionalidad de algunas partes del sitio web.</Typography>
    </PageLayout>
);
