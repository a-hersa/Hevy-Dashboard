from flask import Flask, request, render_template, jsonify
from database import create_tables, get_connection
from upload import cargar_csv
from utils import filtrar_outliers_series
import os

app = Flask(__name__)
app.json.ensure_ascii = False # Para solventar las tildes

# Carpeta temporal donde Flask guarda el CSV antes de procesarlo
UPLOAD_FOLDER = 'uploads_tmp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # La carpeta se crea si no existe

create_tables() # Se ejecuta una vez al arrancar el servidor


@app.route("/")
def index():
    # Renderiza el HTML de templates/index.html
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    # Flask recibe el archivo del formulario HTML
    archivo = request.files.get("csv_file")

    # Añade esto temporalmente para debuggear
    print("Archivo recibido:", archivo)
    print("Filename:", archivo.filename if archivo else "None")

    if not archivo or not archivo.filename.endswith(".csv"):
        return jsonify({"error": "Por favor, sube un archivo CSV."}), 400
    
    # Guardamos el archivo temporalmente en disco
    ruta = os.path.join(UPLOAD_FOLDER, archivo.filename)
    archivo.save(ruta)

    # Procesamos con la función que ya teníamos
    insertadas, ignoradas, errores = cargar_csv(ruta)

    # Borramos el archivo temportal, ya no lo necesitamos
    os.remove(ruta)

    # Devolvemos el resultado como JSON
    # Javascript lo leerá y actulizará la página sin recargarla
    return jsonify({
        "insertadas": insertadas,
        "ignoradas": ignoradas,
        "errores": errores
    })


@app.route("/ejercicios")
def ejercicios():
    """Devuelve la lista de ejercicios únicos para el selector"""
    con = get_connection()
    cur = con.cursor()
    cur.execute("""
        SELECT DISTINCT exercise_title 
        FROM workout_sets 
        ORDER BY exercise_title
    """)
    lista = [fila[0] for fila in cur.fetchall()]
    con.close()
    return jsonify(lista)


@app.route("/volumen")
def volumen():
    ejercicio = request.args.get("ejercicio")
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")

    if not ejercicio:
        return jsonify({"error": "Falta el parámetro ejercicio"}), 400

    con = get_connection()
    cur = con.cursor()

    # Ahora pedimos series individuales, no agrupadas
    query = """
        SELECT
            DATE(start_time) as fecha,
            set_index,
            reps,
            CASE WHEN weight_kg = 0 OR weight_kg IS NULL THEN 1 ELSE weight_kg END as weight_kg,
            reps * CASE WHEN weight_kg = 0 OR weight_kg IS NULL THEN 1 ELSE weight_kg END as volumen_serie
        FROM workout_sets
        WHERE exercise_title = ?
            AND reps IS NOT NULL
    """
    params = [ejercicio]

    if fecha_inicio:
        query += " AND DATE(start_time) >= ?"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND DATE(start_time) <= ?"
        params.append(fecha_fin)

    query += " ORDER BY fecha, set_index"

    cur.execute(query, params)
    filas = cur.fetchall()
    con.close()

    series = [
        {
            "fecha": fila[0],
            "set_index": fila[1],
            "reps": fila[2],
            "weight_kg": fila[3],
            "volumen_serie": fila[4]
        }
        for fila in filas
    ]

    # Primero corregimos outliers a nivel de serie
    series = filtrar_outliers_series(series)

    # Luego agrupamos por día
    from collections import defaultdict
    por_dia = defaultdict(float)
    for serie in series:
        por_dia[serie["fecha"]] += serie["volumen_serie"]

    datos = [
        {"fecha": fecha, "volumen": round(volumen, 1)}
        for fecha, volumen in sorted(por_dia.items())
    ]

    return jsonify(datos)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0") # debug=True recarga el servidor al guardar cambios