import asyncpg
from models.student import StudentCreate
from models.user import UserLogin
from utils.security import get_password_hash, verify_password, create_access_token

async def register_student(data: StudentCreate, db: asyncpg.Connection):
    try:
        # Check if student exists
        existing = await db.fetchrow("SELECT id FROM students WHERE dni = $1", data.dni)
        if existing:
            return {"error": "DNI registrado previamente, por favor ingrese otro"}
        
        password_hash = get_password_hash(data.password)
        
        result = await db.fetchrow(
            """INSERT INTO students (dni, first_name, last_name, phone, parent_name, parent_phone, password_hash)
               VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
            data.dni, data.first_name, data.last_name, data.phone,
            data.parent_name, data.parent_phone, password_hash
        )
        
        token = create_access_token({"id": result['id'], "role": "student"})
        
        return {
            "token": token,
            "user": {
                "id": result['id'],
                "dni": data.dni,
                "role": "student",
                "first_name": data.first_name,
                "last_name": data.last_name
            }
        }
    except asyncpg.exceptions.UniqueViolationError:
        return {"error": "DNI registrado previamente, por favor ingrese otro"}

async def login_user(credentials: UserLogin, db: asyncpg.Connection):
    """Login - matches Node.js logic: check users table first, then students"""
    # First try users table (admin/teacher) - like Node.js
    user = await db.fetchrow(
        "SELECT id, username, role, password_hash, related_id FROM users WHERE username = $1",
        credentials.dni
    )
    
    if user:
        if not verify_password(credentials.password, user['password_hash']):
            return {"error": "DNI o contraseña incorrectos. Intenta de nuevo."}
        
        # Build user data
        user_data = {
            "id": user['id'],
            "username": user['username'],
            "role": user['role']
        }
        
        # Get additional info for teacher (like Node.js)
        if user['role'] == 'teacher' and user['related_id']:
            teacher = await db.fetchrow(
                "SELECT first_name, last_name, email FROM teachers WHERE id = $1",
                user['related_id']
            )
            if teacher:
                user_data['name'] = f"{teacher['first_name']} {teacher['last_name']}"
                user_data['email'] = teacher['email']
                user_data['related_id'] = user['related_id']
        
        token = create_access_token({"id": user['id'], "role": user['role']})
        return {"token": token, "user": user_data}
    
    # If not in users, try student table - like Node.js
    student = await db.fetchrow(
        "SELECT id, dni, first_name, last_name, password_hash FROM students WHERE dni = $1",
        credentials.dni
    )
    
    if not student:
        return {"error": "No se encontró este DNI. Verifica el número o regístrate primero."}
    
    if not verify_password(credentials.password, student['password_hash']):
        return {"error": "DNI o contraseña incorrectos. Intenta de nuevo."}
    
    token = create_access_token({"id": student['id'], "role": "student"})
    
    return {
        "token": token,
        "user": {
            "id": student['id'],
            "dni": student['dni'],
            "role": "student",
            "name": f"{student['first_name']} {student['last_name']}"
        }
    }
