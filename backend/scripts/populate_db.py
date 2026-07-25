"""
Script para poblar la base de datos con datos de prueba
Genera docentes, cursos, ofertas, paquetes y horarios
"""
import asyncio
import asyncpg
import random
from datetime import date, time
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Nombres y apellidos aleatorios para docentes
NOMBRES = [
    "Juan", "María", "Pedro", "Ana", "Luis", "Carmen", "Carlos", "Rosa",
    "Miguel", "Laura", "José", "Isabel", "Antonio", "Sofía", "Francisco",
    "Elena", "Javier", "Patricia", "Manuel", "Lucía", "Raúl", "Marta",
    "Diego", "Cristina", "Alberto", "Beatriz", "Fernando", "Gloria",
    "Roberto", "Teresa"
]

APELLIDOS = [
    "García", "Rodríguez", "Martínez", "López", "González", "Pérez",
    "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez",
    "Díaz", "Cruz", "Morales", "Reyes", "Ortiz", "Gutiérrez",
    "Chávez", "Ruiz", "Jiménez", "Hernández", "Mendoza", "Vargas",
    "Castro", "Romero", "Ramos", "Medina", "Navarro", "Campos"
]

# Cursos base según CreacionCursos.txt
CURSOS_BASE = [
    "Aritmética",
    "Álgebra", 
    "Geometría",
    "Trigonometría",
    "Física I",
    "Física II",
    "Competencia Lingüística",
    "Química",
    "Biología",
    "Historia",
    "Filosofía y Lógica",
    "Educación Cívica",
    "Razonamiento Matemático",
    "Razonamiento Verbal",
    "Geografía",
    "Economía"
]

# Paquetes y sus cursos con grupos
PAQUETES = {
    "Grupo A - Ingeniería y Ciencias Básicas": [
        ("Aritmética", "A"),
        ("Álgebra", "A"),
        ("Geometría", "A"),
        ("Trigonometría", "A"),
        ("Física I", "A"),
        ("Física II", "A"),
        ("Competencia Lingüística", "A"),
        ("Química", "A"),
    ],
    "Grupo B - Ciencias de la Salud y de la Vida": [
        ("Aritmética", "B"),
        ("Álgebra", "B"),
        ("Biología", "A"),
        ("Física I", "B"),
        ("Física II", "B"),
        ("Competencia Lingüística", "B"),
        ("Química", "B"),
    ],
    "Grupo C - Ciencias Empresariales": [
        ("Aritmética", "C"),
        ("Álgebra", "C"),
        ("Historia", "A"),
        ("Competencia Lingüística", "C"),
        ("Geografía", "A"),
        ("Economía", "A"),
        ("Educación Cívica", "A"),
    ],
    "Grupo D - Ciencias Sociales": [
        ("Aritmética", "D"),
        ("Álgebra", "D"),
        ("Competencia Lingüística", "D"),
        ("Historia", "B"),
        ("Geografía", "B"),
        ("Filosofía y Lógica", "A"),
        ("Educación Cívica", "B"),
    ]
}

# Horarios disponibles
HORARIOS_SEMANA = [
    # Lunes a Viernes: 7am-1pm (sesiones de 2 horas)
    ("07:00", "09:00"),
    ("09:00", "11:00"),
    ("11:00", "13:00"),
    # Lunes a Viernes: 2pm-8pm (sesiones de 2 horas)
    ("14:00", "16:00"),
    ("16:00", "18:00"),
    ("18:00", "20:00"),
]

HORARIOS_SABADO = [
    # Sábado: 7am-12pm (sesiones de 1 hora)
    ("07:00", "08:00"),
    ("08:00", "09:00"),
    ("09:00", "10:00"),
    ("10:00", "11:00"),
    ("11:00", "12:00"),
]

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
SABADO = "Sábado"

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("✅ Conectado a la base de datos")
    
    try:
        # 1. Obtener o crear ciclo activo
        cycle = await conn.fetchrow(
            "SELECT id, name FROM cycles WHERE status = 'open' OR status = 'in_progress' ORDER BY id DESC LIMIT 1"
        )
        
        if not cycle:
            print("⚠️  No hay ciclo activo, creando uno nuevo...")
            cycle = await conn.fetchrow(
                """INSERT INTO cycles (name, start_date, end_date, duration_months, status)
                   VALUES ('Ciclo 2025-I', $1, $2, 6, 'open')
                   RETURNING id, name""",
                date(2025, 3, 1), date(2025, 8, 31)
            )
        
        cycle_id = cycle['id']
        print(f"📅 Usando ciclo: {cycle['name']} (ID: {cycle_id})")
        
        # 2. Crear docentes (20-30)
        num_teachers = random.randint(20, 30)
        print(f"\n👨‍🏫 Creando {num_teachers} docentes...")
        teachers = []
        PHONES = ["969728039", "970253943", "984618002", "949850422", "950132313"]
        
        # Import password hash function
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from utils.security import get_password_hash
        
        for i in range(num_teachers):
            nombre = random.choice(NOMBRES)
            apellido = random.choice(APELLIDOS)
            dni = f"{random.randint(10000000, 99999999)}"
            phone = random.choice(PHONES)
            email = f"{nombre.lower()}.{apellido.lower()}@academia.edu.pe"
            
            # Verificar si ya existe el DNI
            existing = await conn.fetchval("SELECT id FROM teachers WHERE dni = $1", dni)
            if existing:
                continue
            
            # 1. Crear usuario en users table (como create_teacher)
            user_result = await conn.fetchrow(
                """INSERT INTO users (username, password_hash, role, related_id)
                   VALUES ($1, $2, 'teacher', NULL) RETURNING id""",
                dni, get_password_hash(dni)
            )
            user_id = user_result['id']
            
            # 2. Crear teacher
            teacher = await conn.fetchrow(
                """INSERT INTO teachers (first_name, last_name, dni, phone, email, specialization)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   RETURNING id, first_name, last_name""",
                nombre, apellido, dni, phone, email, random.choice(CURSOS_BASE)
            )
            teacher_id = teacher['id']
            
            # 3. Actualizar users.related_id con teacher_id
            await conn.execute("UPDATE users SET related_id = $1 WHERE id = $2", teacher_id, user_id)
            
            teachers.append(teacher)
            print(f"  ✓ {teacher['first_name']} {teacher['last_name']} (ID: {teacher['id']}, User: {dni})")
        
        print(f"✅ {len(teachers)} docentes creados")
        
        # 3. Crear cursos base
        print(f"\n📚 Creando {len(CURSOS_BASE)} cursos base...")
        course_map = {}  # nombre -> id
        
        for curso_nombre in CURSOS_BASE:
            precio = round(random.uniform(150, 200), 2)
            
            # Verificar si ya existe
            existing = await conn.fetchval("SELECT id FROM courses WHERE name = $1", curso_nombre)
            if existing:
                course_map[curso_nombre] = existing
                print(f"  ⚠️  {curso_nombre} ya existe (ID: {existing})")
                continue
            
            course = await conn.fetchrow(
                """INSERT INTO courses (name, description, base_price)
                   VALUES ($1, $2, $3)
                   RETURNING id, name, base_price""",
                curso_nombre,
                f"Curso de {curso_nombre} para preparación universitaria",
                precio
            )
            course_map[curso_nombre] = course['id']
            print(f"  ✓ {course['name']} - S/. {course['base_price']} (ID: {course['id']})")
        
        print(f"✅ {len(course_map)} cursos en la base de datos")
        
        # 4. Crear ofertas de cursos y asignar horarios
        print(f"\n🎓 Creando ofertas de cursos con horarios...")
        offering_map = {}  # (nombre_curso, grupo) -> offering_id
        
        # Recopilar todas las ofertas necesarias de los paquetes
        ofertas_necesarias = set()
        for paquete_nombre, cursos in PAQUETES.items():
            for curso_nombre, grupo in cursos:
                ofertas_necesarias.add((curso_nombre, grupo))
        
        for curso_nombre, grupo in sorted(ofertas_necesarias):
            if curso_nombre not in course_map:
                print(f"  ⚠️  Curso {curso_nombre} no encontrado, saltando...")
                continue
            
            course_id = course_map[curso_nombre]
            teacher = random.choice(teachers)
            capacidad = random.randint(15, 30)
            
            # Crear offering
            offering = await conn.fetchrow(
                """INSERT INTO course_offerings (course_id, cycle_id, group_label, teacher_id, capacity)
                   VALUES ($1, $2, $3, $4, $5)
                   RETURNING id""",
                course_id, cycle_id, grupo, teacher['id'], capacidad
            )
            offering_id = offering['id']
            offering_map[(curso_nombre, grupo)] = offering_id
            
            print(f"  ✓ {curso_nombre} - Grupo {grupo} (Profesor: {teacher['first_name']} {teacher['last_name']})")
            
            # Asignar horarios: 2 días de lunes a viernes + 1 sábado
            dias_asignados = random.sample(DIAS_SEMANA, 2)  # 2 días entre semana
            
            for dia in dias_asignados:
                horario = random.choice(HORARIOS_SEMANA)
                # Convertir strings a time objects
                h_start, m_start = map(int, horario[0].split(':'))
                h_end, m_end = map(int, horario[1].split(':'))
                start_time = time(h_start, m_start)
                end_time = time(h_end, m_end)
                
                await conn.execute(
                    """INSERT INTO schedules (course_offering_id, day_of_week, start_time, end_time, classroom)
                       VALUES ($1, $2::day_of_week, $3, $4, $5)""",
                    offering_id, dia, start_time, end_time, f"Aula {random.randint(101, 310)}"
                )
                print(f"    → {dia}: {horario[0]} - {horario[1]}")
            
            # Añadir 1 sesión los sábados
            horario_sabado = random.choice(HORARIOS_SABADO)
            h_start, m_start = map(int, horario_sabado[0].split(':'))
            h_end, m_end = map(int, horario_sabado[1].split(':'))
            start_time = time(h_start, m_start)
            end_time = time(h_end, m_end)
            
            await conn.execute(
                """INSERT INTO schedules (course_offering_id, day_of_week, start_time, end_time, classroom)
                   VALUES ($1, $2::day_of_week, $3, $4, $5)""",
                offering_id, SABADO, start_time, end_time, f"Aula {random.randint(101, 310)}"
            )
            print(f"    → {SABADO}: {horario_sabado[0]} - {horario_sabado[1]}")
        
        print(f"✅ {len(offering_map)} ofertas de cursos creadas con horarios")
        
        # 5. Crear paquetes
        print(f"\n📦 Creando {len(PAQUETES)} paquetes...")
        
        for paquete_nombre, cursos in PAQUETES.items():
            precio_total = sum(random.uniform(150, 200) for _ in cursos)
            descuento = precio_total * 0.15  # 15% de descuento
            precio_paquete = round(precio_total - descuento, 2)
            
            # Verificar si ya existe
            existing = await conn.fetchval("SELECT id FROM packages WHERE name = $1", paquete_nombre)
            if existing:
                package_id = existing
                print(f"  ⚠️  {paquete_nombre} ya existe (ID: {package_id})")
            else:
                package = await conn.fetchrow(
                    """INSERT INTO packages (name, description, base_price)
                       VALUES ($1, $2, $3)
                       RETURNING id""",
                    paquete_nombre,
                    f"Paquete completo para {paquete_nombre.split(' - ')[1]}",
                    precio_paquete
                )
                package_id = package['id']
                print(f"  ✓ {paquete_nombre} - S/. {precio_paquete} (ID: {package_id})")
                
                # Vincular cursos base al paquete
                for curso_nombre, grupo in cursos:
                    if curso_nombre in course_map:
                        await conn.execute(
                            """INSERT INTO package_courses (package_id, course_id)
                               VALUES ($1, $2)
                               ON CONFLICT DO NOTHING""",
                            package_id, course_map[curso_nombre]
                        )
            
            # Crear package offering
            po = await conn.fetchrow(
                """INSERT INTO package_offerings (package_id, cycle_id, group_label, capacity)
                   VALUES ($1, $2, $3, $4)
                   RETURNING id""",
                package_id, cycle_id, "ÚNICO", random.randint(20, 40)
            )
            po_id = po['id']
            
            # Vincular course_offerings al package_offering
            for curso_nombre, grupo in cursos:
                key = (curso_nombre, grupo)
                if key in offering_map:
                    await conn.execute(
                        """INSERT INTO package_offering_courses (package_offering_id, course_offering_id)
                           VALUES ($1, $2)
                           ON CONFLICT DO NOTHING""",
                        po_id, offering_map[key]
                    )
            
            print(f"    → Package offering creado (ID: {po_id}) con {len(cursos)} cursos")
        
        print(f"\n✅ ¡Población de base de datos completada exitosamente!")
        print(f"\nResumen:")
        print(f"  • Docentes: {len(teachers)}")
        print(f"  • Cursos: {len(course_map)}")
        print(f"  • Ofertas de cursos: {len(offering_map)}")
        print(f"  • Paquetes: {len(PAQUETES)}")
        print(f"  • Ciclo: {cycle['name']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    asyncio.run(main())
