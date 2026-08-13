-- =============================================================================
-- Esquema de la base de datos - Academia UNI Urubamba
-- =============================================================================
-- Reconstruido a partir del codigo (backend/controllers/*.py, backend/models/*.py)
-- porque el repositorio original no contenia ningun archivo de migracion ni DDL:
-- las tablas de produccion (Railway) se crearon a mano, fuera del control de
-- versiones. Este archivo es la primera fuente de verdad versionada del esquema.
--
-- Dos piezas son best-effort porque el codigo backend nunca las escribe
-- (se alimentan/crean fuera de este repo) y no se pudo recuperar su DDL
-- original exacto:
--   - analytics_summary: solo se lee/filtra, nunca se inserta desde este
--     backend. Se crea vacia; si no la alimenta ningun proceso externo,
--     el panel de analitica simplemente mostrara "sin datos".
--   - view_dashboard_admin_extended: se reconstruye con una definicion
--     razonable basada en el resto del esquema. Si el dashboard admin
--     espera columnas distintas a las de aqui, hay que ajustarla.
--
-- Uso:
--   psql "$DATABASE_URL" -f schema.sql
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Tipos
-- -----------------------------------------------------------------------------

CREATE TYPE day_of_week AS ENUM (
    'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'
);

-- -----------------------------------------------------------------------------
-- cycles
-- -----------------------------------------------------------------------------

CREATE TABLE cycles (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    start_date       DATE NOT NULL,
    end_date         DATE NOT NULL,
    duration_months  INTEGER NOT NULL CHECK (duration_months > 0),
    status           VARCHAR(20) NOT NULL DEFAULT 'open'
);

-- -----------------------------------------------------------------------------
-- teachers
-- -----------------------------------------------------------------------------

CREATE TABLE teachers (
    id               SERIAL PRIMARY KEY,
    first_name       VARCHAR(100) NOT NULL,
    last_name        VARCHAR(100) NOT NULL,
    dni              VARCHAR(8) NOT NULL UNIQUE,
    phone            VARCHAR(20),
    email            VARCHAR(150),
    specialization   VARCHAR(150)
);

-- -----------------------------------------------------------------------------
-- users (cuentas de administrador y docente; los estudiantes viven en `students`)
-- -----------------------------------------------------------------------------

CREATE TABLE users (
    id               SERIAL PRIMARY KEY,
    username         VARCHAR(50) NOT NULL UNIQUE,
    password_hash    VARCHAR(255) NOT NULL,
    role             VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
    related_id       INTEGER REFERENCES teachers(id) ON DELETE SET NULL
);

-- -----------------------------------------------------------------------------
-- students
-- -----------------------------------------------------------------------------

CREATE TABLE students (
    id               SERIAL PRIMARY KEY,
    dni              VARCHAR(8) NOT NULL UNIQUE,
    first_name       VARCHAR(60) NOT NULL,
    last_name        VARCHAR(60) NOT NULL,
    phone            VARCHAR(20) NOT NULL,
    parent_name      VARCHAR(80) NOT NULL,
    parent_phone     VARCHAR(20),
    password_hash    VARCHAR(255) NOT NULL
);

-- -----------------------------------------------------------------------------
-- courses / course_offerings
-- -----------------------------------------------------------------------------

CREATE TABLE courses (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(150) NOT NULL,
    description      TEXT,
    base_price       NUMERIC(10, 2) NOT NULL CHECK (base_price > 0)
);

CREATE TABLE course_offerings (
    id               SERIAL PRIMARY KEY,
    course_id        INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    cycle_id         INTEGER NOT NULL REFERENCES cycles(id) ON DELETE RESTRICT,
    group_label      VARCHAR(20) NOT NULL DEFAULT '',
    teacher_id       INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
    price_override   NUMERIC(10, 2),
    capacity         INTEGER
);

CREATE INDEX idx_course_offerings_course ON course_offerings(course_id);
CREATE INDEX idx_course_offerings_cycle  ON course_offerings(cycle_id);

-- -----------------------------------------------------------------------------
-- packages / package_courses / package_offerings / package_offering_courses
-- -----------------------------------------------------------------------------

CREATE TABLE packages (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(150) NOT NULL,
    description      TEXT,
    base_price       NUMERIC(10, 2) NOT NULL CHECK (base_price > 0)
);

-- Cursos "base" (no ofertas concretas) que componen un paquete.
CREATE TABLE package_courses (
    package_id       INTEGER NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
    course_id        INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    PRIMARY KEY (package_id, course_id)
);

CREATE TABLE package_offerings (
    id               SERIAL PRIMARY KEY,
    package_id       INTEGER NOT NULL REFERENCES packages(id) ON DELETE RESTRICT,
    cycle_id         INTEGER NOT NULL REFERENCES cycles(id) ON DELETE RESTRICT,
    group_label      VARCHAR(20),
    price_override   NUMERIC(10, 2),
    capacity         INTEGER
);

CREATE INDEX idx_package_offerings_package ON package_offerings(package_id);
CREATE INDEX idx_package_offerings_cycle   ON package_offerings(cycle_id);

-- Qué ofertas de curso concretas cubre cada oferta de paquete (mismo ciclo).
CREATE TABLE package_offering_courses (
    package_offering_id  INTEGER NOT NULL REFERENCES package_offerings(id) ON DELETE CASCADE,
    course_offering_id   INTEGER NOT NULL REFERENCES course_offerings(id) ON DELETE CASCADE,
    PRIMARY KEY (package_offering_id, course_offering_id)
);

-- -----------------------------------------------------------------------------
-- schedules
-- -----------------------------------------------------------------------------

CREATE TABLE schedules (
    id                    SERIAL PRIMARY KEY,
    course_offering_id    INTEGER NOT NULL REFERENCES course_offerings(id) ON DELETE CASCADE,
    day_of_week           day_of_week NOT NULL,
    start_time            TIME NOT NULL,
    end_time              TIME NOT NULL,
    classroom             VARCHAR(50)
);

CREATE INDEX idx_schedules_offering ON schedules(course_offering_id);

-- -----------------------------------------------------------------------------
-- enrollments
-- -----------------------------------------------------------------------------

CREATE TABLE enrollments (
    id                   SERIAL PRIMARY KEY,
    student_id           INTEGER NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    course_offering_id   INTEGER REFERENCES course_offerings(id) ON DELETE RESTRICT,
    package_offering_id  INTEGER REFERENCES package_offerings(id) ON DELETE RESTRICT,
    enrollment_type      VARCHAR(10) NOT NULL CHECK (enrollment_type IN ('course', 'package')),
    status               VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                         CHECK (status IN ('pendiente', 'aceptado', 'rechazado', 'cancelado', 'finalizado')),
    registered_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accepted_at          TIMESTAMP,
    rejected_at          TIMESTAMP,
    cancelled_at         TIMESTAMP,
    finalized_at         TIMESTAMP
);

CREATE INDEX idx_enrollments_student ON enrollments(student_id);

-- RF13 (C-12 en enrollmentController.py): un estudiante no puede tener dos
-- matriculas ACTIVAS sobre la misma oferta. "Activo" = pendiente, aceptado o
-- finalizado (ESTADOS_ACTIVOS en el codigo); rechazado/cancelado no cuentan,
-- por eso el indice es parcial. create_enrollment() atrapa la violacion de
-- estos indices como asyncpg.UniqueViolationError.
CREATE UNIQUE INDEX ux_enrollments_course_active
    ON enrollments (student_id, course_offering_id)
    WHERE enrollment_type = 'course'
      AND status IN ('pendiente', 'aceptado', 'finalizado');

CREATE UNIQUE INDEX ux_enrollments_package_active
    ON enrollments (student_id, package_offering_id)
    WHERE enrollment_type = 'package'
      AND status IN ('pendiente', 'aceptado', 'finalizado');

-- -----------------------------------------------------------------------------
-- enrollment_status_history (RNF15 - trazabilidad)
-- -----------------------------------------------------------------------------

CREATE TABLE enrollment_status_history (
    id                SERIAL PRIMARY KEY,
    enrollment_id     INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    previous_status   VARCHAR(20),
    new_status        VARCHAR(20) NOT NULL,
    changed_by_id     INTEGER,
    changed_by_role   VARCHAR(20),
    reason            TEXT,
    changed_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_enrollment_history_enrollment ON enrollment_status_history(enrollment_id);

-- -----------------------------------------------------------------------------
-- payment_plans / installments
-- -----------------------------------------------------------------------------

CREATE TABLE payment_plans (
    id               SERIAL PRIMARY KEY,
    enrollment_id    INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    total_amount     NUMERIC(10, 2) NOT NULL,
    installments     INTEGER NOT NULL  -- numero total de cuotas del plan, no una FK
);

CREATE INDEX idx_payment_plans_enrollment ON payment_plans(enrollment_id);

CREATE TABLE installments (
    id                   SERIAL PRIMARY KEY,
    payment_plan_id      INTEGER NOT NULL REFERENCES payment_plans(id) ON DELETE CASCADE,
    installment_number   INTEGER NOT NULL,
    due_date             DATE NOT NULL,
    amount               NUMERIC(10, 2) NOT NULL,
    status               VARCHAR(20) NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending', 'paid', 'overdue')),
    voucher_url          TEXT,
    rejection_reason     TEXT,
    rejected_at          TIMESTAMP,
    paid_at              TIMESTAMP,
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_installments_plan ON installments(payment_plan_id);

-- -----------------------------------------------------------------------------
-- attendance
-- -----------------------------------------------------------------------------

CREATE TABLE attendance (
    id             SERIAL PRIMARY KEY,
    student_id     INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    schedule_id    INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    date           DATE NOT NULL,
    status         VARCHAR(20) NOT NULL,
    UNIQUE (student_id, schedule_id, date)
);

-- -----------------------------------------------------------------------------
-- notifications_log
-- -----------------------------------------------------------------------------

CREATE TABLE notifications_log (
    id             SERIAL PRIMARY KEY,
    student_id     INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    parent_phone   VARCHAR(20),
    type           VARCHAR(50) NOT NULL,
    message        TEXT NOT NULL,
    status         VARCHAR(20) NOT NULL,
    sent_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- analytics_summary (best-effort: ningun controlador del backend le escribe)
-- -----------------------------------------------------------------------------

CREATE TABLE analytics_summary (
    id            SERIAL PRIMARY KEY,
    student_id    INTEGER REFERENCES students(id) ON DELETE CASCADE,
    cycle_id      INTEGER REFERENCES cycles(id) ON DELETE CASCADE,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- view_dashboard_admin_extended (best-effort: el DDL original no estaba en el
-- repo; reconstruida combinando estudiantes + matriculas + pagos)
-- -----------------------------------------------------------------------------

CREATE VIEW view_dashboard_admin_extended AS
SELECT
    s.id                                                                AS student_id,
    s.first_name,
    s.last_name,
    s.dni,
    s.phone,
    s.parent_name,
    s.parent_phone,
    COUNT(DISTINCT e.id)                                                AS total_enrollments,
    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'aceptado')           AS enrollments_aceptadas,
    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'pendiente')          AS enrollments_pendientes,
    COALESCE(SUM(i.amount) FILTER (WHERE i.status = 'paid'), 0)         AS total_pagado,
    MAX(e.registered_at)                                                AS ultima_matricula
FROM students s
LEFT JOIN enrollments e   ON e.student_id = s.id
LEFT JOIN payment_plans pp ON pp.enrollment_id = e.id
LEFT JOIN installments i   ON i.payment_plan_id = pp.id
GROUP BY s.id, s.first_name, s.last_name, s.dni, s.phone, s.parent_name, s.parent_phone;

COMMIT;
