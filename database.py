import sqlite3

DB_PATH = "workouts.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    con = get_connection()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS workout_sets (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            title            TEXT NOT NULL,
            start_time       DATETIME,
            end_time         DATETIME,
            description      TEXT,
            exercise_title   TEXT NOT NULL,
            superset_id      TEXT,
            exercise_notes   TEXT,
            set_index        INTEGER,
            set_type         TEXT,
            weight_kg        REAL,
            reps             INTEGER,
            distance_km      REAL,
            duration_seconds REAL,
            rpe              REAL,
            created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE (start_time, exercise_title, set_index)
        )
    """)
    con.commit()
    con.close()

if __name__ == "__main__":
    create_tables()
    print("Base de datos creada correctamente")