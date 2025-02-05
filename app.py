from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
from dateutil.relativedelta import relativedelta
from weasyprint import HTML
import io

# 🔹 Definir la aplicación ANTES de usar @app.route
app = Flask(__name__)

# 🔹 Datos predefinidos
porcentajes_anuales = {
    2020: 10.075,
    2021: 10.075,
    2022: 10.075,
    2023: 11.666,
    2024: 12.257,
    2025: 13.348
}

valores_uma_anuales = {
    2020: 86.88,
    2021: 89.62,
    2022: 96.22,
    2023: 103.74,
    2024: 108.57,
    2025: 113.14
}

# 🔹 Función para calcular cuota
def calcular_cuota(fecha_inicio, fecha_fin, numero_umas):
    inicio = datetime.strptime(fecha_inicio, "%d/%m/%Y")
    fin = datetime.strptime(fecha_fin, "%d/%m/%Y")

    if inicio > fin:
        raise ValueError("La fecha de inicio debe ser anterior a la fecha fin.")

    pago_total = 0
    detalles_meses = []
    numero_meses = 0
    fecha_actual = inicio
    recargo_mensual = 1.7  # Valor fijo
    inflacion_mensual = 0.5  # Valor fijo

    while fecha_actual <= fin:
        año = fecha_actual.year
        porcentaje_actual = porcentajes_anuales.get(año, 0) / 100
        valor_uma = valores_uma_anuales.get(año, 0)

        salario_base = numero_umas * valor_uma * 30.4
        cuota_mensual = salario_base * porcentaje_actual
        cuota_con_recargo = cuota_mensual * (1 + recargo_mensual / 100)
        cuota_con_inflacion = cuota_con_recargo * (1 + inflacion_mensual / 100)

        detalles_meses.append({
            'fecha': fecha_actual.strftime("%m/%Y"),
            'salario_base': round(salario_base, 2),
            'cuota_mensual': round(cuota_mensual, 2),
            'recargo': round(cuota_con_recargo - cuota_mensual, 2),
            'inflacion': round(cuota_con_inflacion - cuota_con_recargo, 2),
            'total_mes': round(cuota_con_inflacion, 2)
        })

        pago_total += cuota_con_inflacion
        fecha_actual += relativedelta(months=1)
        numero_meses += 1

    return round(pago_total, 2), detalles_meses, numero_meses

# 🔹 Ruta principal
@app.route('/')
def inicio():
    return render_template('index.html')

# 🔹 Ruta para calcular cuotas
@app.route('/calcular', methods=['POST'])
def calcular():
    data = request.get_json()
    try:
        pago_total, detalles_meses, numero_meses = calcular_cuota(
            data['fecha_inicio'],
            data['fecha_fin'],
            float(data['numero_umas'])
        )
        return jsonify({'pago_total': pago_total, 'detalles_meses': detalles_meses, 'numero_meses': numero_meses})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# 🔹 Ruta para generar PDF
@app.route('/generar_pdf', methods=['POST'])
def generar_pdf():
    try:
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        numero_umas = float(request.form['numero_umas'])

        # Obtener el año de inicio
        año_inicio = datetime.strptime(fecha_inicio, "%d/%m/%Y").year

        # Obtener el valor de la UMA del año de inicio
        valor_uma_inicio = valores_uma_anuales.get(año_inicio, "Desconocido")

        pago_total, detalles_meses, numero_meses = calcular_cuota(fecha_inicio, fecha_fin, numero_umas)

        contenido_html = render_template(
            'pdf_template.html',
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            numero_umas=numero_umas,
            valor_uma_inicio=valor_uma_inicio,
            año_inicio=año_inicio,
            recargo_mensual=1.7,  # Valor fijo
            inflacion_mensual=0.5,  # Valor fijo
            detalles=detalles_meses,
            pago_total=pago_total,
            numero_meses=numero_meses
        )

        # Generar el PDF
        pdf_resultado = HTML(string=contenido_html).write_pdf()

        return send_file(io.BytesIO(pdf_resultado),
                         download_name="Pago_Retroactivo_Modalidad_40.pdf",
                         mimetype='application/pdf',
                         as_attachment=True)
    except Exception as e:
        return str(e), 400

# 🔹 Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
