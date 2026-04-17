import pandas as pd
import math
from database import get_connection

# FUNCIONES DE LIMPIEZA
# Cada función tiene una responsabilidad:
# Limpiar un solo tipo de dato

def limpiar_fecha(texto):
    """
    Convierte '5 ene 2026, 10:58' a un datetime.
    pandas.to_datetime no entiende meses en español,
    así que lo traducimos manualmente antes.
    """
    meses = {
        'ene': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'abr': 'Apr',
        'may': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug',
        'sep': 'Sep', 'oct': 'Oct', 'nov': 'Nov', 'dic': 'Dec'
    }
    if pd.isna(texto):
        return None
    for es, en in meses.items():
        texto = texto.replace(es, en)
    return pd.to_datetime(texto, format='%d %b %Y, %H:%M').isoformat()


def limpiar_reps(valor):
    """
    Reps debe ser entero. Si viene como 9.0 (float),
    lo convertimos. Si viene como 3.5, avisamos y redondeamos.
    Si es NaN (celda vacía), devolvemos None (NULL en SQLite).
    """
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return None
    if valor != int(valor):
        print(f"Reps con decimal inesperado: {valor} → {round(valor)}")
    return int(round(valor))


def limpiar_real(valor):
    """
    Para weight_kg, distance_km, etc.
    Solo convierte NaN a None para que SQLite lo guarde como NULL.
    None y NaN son cosas distintas: None es Python, NULL es SQL,
    NaN es un valkor especial de float que significa "no es un número".
    """
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return None
    return float(valor)


def limpiar_texto(valor):
    """
    Para columnas TEXT. Convierte NaN a None.
    pandas lee celdas vacías como float NaN, no como None ni como "".
    """
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return None
    return str(valor).strip()  # Elimina espacios al principio y al final

# FUNCIÓN PRINCIPAL

def cargar_csv(ruta_csv):
    """
    Lee el CSV, limpia cada fila e inserta en la BD.
    Devuelve un resumen de cuántas filas se insertaron y cuántas se ignoraron.
    """
    df = pd.read_csv(ruta_csv)

    insertadas = 0
    ignoradas = 0  # filas duplicadas (las captura el UNIQUE)
    errores = 0

    con = get_connection()
    cur = con.cursor()

    for _, fila in df.iterrows():
        # iterrows() recorre el DataFrame fila a fila.
        # El _ es el índice de la fila (0, 1, 2...), no nos interesa.

        try:
            cur.execute("""
                INSERT OR IGNORE INTO workout_sets (
                    title, start_time, end_time, description,
                    exercise_title, superset_id, exercise_notes,
                    set_index, set_type,
                    weight_kg, reps, distance_km, duration_seconds, rpe
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?
                )
            """, (
                limpiar_texto(fila["title"]),
                limpiar_fecha(fila["start_time"]),
                limpiar_fecha(fila["end_time"]),
                limpiar_texto(fila["description"]),

                limpiar_texto(fila["exercise_title"]),
                limpiar_texto(fila["superset_id"]),
                limpiar_texto(fila["exercise_notes"]),

                int(fila["set_index"]),  # set_index siempre viene como número
                limpiar_texto(fila["set_type"]),

                limpiar_real(fila["weight_kg"]),
                limpiar_reps(fila["reps"]),
                limpiar_real(fila["distance_km"]),
                limpiar_real(fila["duration_seconds"]),
                limpiar_real(fila["rpe"]),
            ))

            # rowcount indica cuántas filas afectó el último execute().
            # Si fue IGNORE (duplicado), rowcount es 0.
            if cur.rowcount == 1:
                insertadas += 1
            else:
                ignoradas += 1

        except Exception as e:
            print(f"Error en fila {_}: {e}")
            errores += 1

    con.commit()  # Guarda todos los cambios. Sin esto no se escribe nada en disco.
    con.close()

    print(f"Insertadas: {insertadas} | Ignoradas (duplicadas): {ignoradas} | Errores: {errores}")
    return insertadas, ignoradas, errores


# PARA PROBAR DIRECTAMENTE

if __name__ == "__main__":
    cargar_csv("data/workout_data.csv")  # cambia por el nombre real
