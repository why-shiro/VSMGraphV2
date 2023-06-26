import io
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, url_for, request, redirect, jsonify
import webbrowser


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', image_path='output/output.png')

@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        filename = f.filename
        f.save(filename)
        t = histeresis_calculation(filename)
        return jsonify({'message': 'File uploaded successfully.', 't': float(t[1])})
    else:
        return "This route only supports file uploads via POST method."



@app.route('/output')
def show_output():
    filename = request.args.get('filename')
    t = request.args.get('t')
    return render_template('output.html', output_filename=filename, t=t)



def histeresis_calculation(file_path):
    # CSV dosyasını okuyun.
    df = pd.read_csv(file_path, encoding="ISO-8859-1")
    # Convert the data to numpy arrays
    H = df['H GaussMeter (Oe)'].to_numpy()
    Mx = df['Mx (emu)'].to_numpy()

    # Shift the Y-axis if it doesn't start from 0
    if Mx[0] != 0:
        offset = Mx[0]
        Mx = Mx - offset

    # Başlangıç threshold değeri
    initial_threshold = 1e-3
    final_threshold = 1e-20

    # En az elemana sahip düşük eğimli küme ve eğim değeri
    min_elements = len(H)
    min_elements_set = []
    min_slope = None

    # Threshold değerini azaltarak eğim noktalarını bul
    threshold_values = np.logspace(np.log10(initial_threshold), np.log10(final_threshold), 10000)
    for threshold in threshold_values:
        # Düşük eğimli noktaları belirleyecek listeler
        dusuk_egim_noktalari = []

        # Açı aralığını yüksekten başlayarak azalt
        for i in range(len(H)-1):
            x_degeri = H[i+1] - H[i]
            y_degeri = Mx[i+1] - Mx[i]
            eğim = abs(y_degeri / x_degeri)
            if eğim < threshold and i not in dusuk_egim_noktalari and i+1 not in dusuk_egim_noktalari:
                dusuk_egim_noktalari.append(i)
                dusuk_egim_noktalari.append(i+1)

        # Düşük eğimli kümenin eleman sayısını kontrol et
        num_elements = len(dusuk_egim_noktalari) // 2
        if num_elements >= 20 and num_elements < min_elements:
            min_elements = num_elements
            min_elements_set = dusuk_egim_noktalari.copy()
            min_slope = threshold

    # En düşük eğimli noktaların indekslerini ve karşılık gelen H ve Mx değerlerini saklayacak listeler
    dusuk_egim_indeksleri = []
    dusuk_egim_H_degerleri = []
    dusuk_egim_Mx_degerleri = []

    # Düşük eğimli noktaların indekslerini ve karşılık gelen H ve Mx değerlerini bul ve listelere ekle
    for indeks in min_elements_set:
        dusuk_egim_indeksleri.append(indeks)
        dusuk_egim_H_degerleri.append(H[indeks])
        dusuk_egim_Mx_degerleri.append(Mx[indeks])

    # Saturation noktasını bul
    saturation_index = dusuk_egim_indeksleri[-1]  # En son nokta

    # Mx'in saturation değeri
    saturation_Mx = Mx[saturation_index]

    # t değerini hesapla
    t = (-saturation_Mx / H[saturation_index]) / 2

    # Mxnew değerlerini hesapla
    Mxnew = Mx + (H * t) - offset

    # Mxnew'in max ve min değerlerinin farkını hesapla
    Mxnew_max = np.max(Mxnew)
    Mxnew_min = np.min(Mxnew)
    Mxnew_range = Mxnew_max - Mxnew_min

    # Mxnew değerlerini ortala
    Mxnew_centered = (Mxnew - Mxnew_min) - (Mxnew_range / 2)

    # Saturation bölgesini belirle
    saturation_region = np.where(Mx == saturation_Mx)[0]

    # Saturasyon noktasının aşağı yönde kaymasını engelle
    for i in range(saturation_index, len(H)):
        if Mxnew[i] < saturation_Mx:
            Mxnew[i] = saturation_Mx

    # Histeris grafiğini çiz
    plt.figure(figsize=(8, 6))
    plt.plot(H, Mx, color='orange', label='Histeris Grafiği')

    # Düşük eğimli noktaları mavi çizgilerle birleştir
    for i in range(0, len(dusuk_egim_indeksleri)-1, 2):
        nokta1 = dusuk_egim_indeksleri[i]
        nokta2 = dusuk_egim_indeksleri[i+1]
        plt.plot(H[nokta1:nokta2+1], Mx[nokta1:nokta2+1], color='blue')

    # Saturation noktalarını kırmızı renkle işaretle
    plt.scatter(H[saturation_region], Mx[saturation_region], color='red', label='Saturation Noktaları', s=30)

    # Mxnew grafiğini çiz
    plt.plot(H, Mxnew_centered, color='black', linestyle='--', label='Mxnew (Shifted and Centered)')

    plt.xlabel('H GaussMeter (Oe)')
    plt.ylabel('Mx (emu)')
    plt.title('Histeris Grafiği')
    fig = plt.gcf()  # Get the current figure
    print(f"En düşük eğimli açı (threshold): {min_slope}")
    print(f"t değeri: {t}")
    canvas = FigureCanvas(fig)  # Place it onto the canvas
    png_output = io.BytesIO()  # Prepare output stream
    canvas.print_png(png_output)  # Output to stream
    png_output.seek(0)  # Seek the stream to the beginning

    output_filename = 'static/output/output.png'
    with open(output_filename, 'wb') as out_file:
        out_file.write(png_output.read())

    # Return the name of the output file and the value of t
    return output_filename, t

@app.route('/redirect')
def redirect_to_output():
    return redirect('/output')

if __name__ == '__main__':
    app.run(debug=True, port=5500)
