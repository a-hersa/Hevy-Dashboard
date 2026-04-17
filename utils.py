def filtrar_outliers_series(series):
    """
    Detecta outliers en series individuales (reps * weight_kg por serie)
    y los reemplaza por la mediana de las otras series del mismo día.
    """
    if len(series) < 4:
        return series

    volumenes = [s["volumen_serie"] for s in series]

    ordenados = sorted(volumenes)
    n = len(ordenados)
    q1 = ordenados[n // 4]
    q3 = ordenados[(3 * n) // 4]
    iqr = q3 - q1
    limite_superior = q3 + 1.5 * iqr

    resultado = []
    for serie in series:
        if serie["volumen_serie"] > limite_superior:
            # Buscamos la mediana de las otras series del mismo día
            series_mismo_dia = [
                s["volumen_serie"] for s in series
                if s["fecha"] == serie["fecha"]
                and s["volumen_serie"] <= limite_superior
            ]
            if series_mismo_dia:
                mediana = sorted(series_mismo_dia)[len(series_mismo_dia) // 2]
                print(f"⚠️  Outlier en {serie['fecha']} serie {serie['set_index']}: {serie['volumen_serie']} → {mediana}")
                resultado.append({**serie, "volumen_serie": mediana, "outlier": True})
            else:
                resultado.append(serie)
        else:
            resultado.append(serie)

    return resultado