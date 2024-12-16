import os
import pandas as pd
import requests
from flask import Flask, request, render_template, send_file, redirect, url_for, send_from_directory
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app)

# Rota inicial
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        column = int(request.form['column'])
        api_key = request.form['api_key']

        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            return f"Erro ao abrir o arquivo: {e}"

        if column < 1 or column > len(df.columns):
            return "Número de coluna inválido."

        ips = df.iloc[:, column - 1]
        results = []
        max_queries = 1000

        for i, ip in enumerate(ips, start=1):
            if i > max_queries:
                results.append("Consulta não realizada (limite de 1000 atingido)")
                continue

            # Emite progresso a cada IP
            socketio.emit('progress', {
                'message': f"Lendo IP {i} de {len(ips)}...",
                'progress': int((i / len(ips)) * 100)
            })
            socketio.sleep(0.1)

            try:
                response = requests.get(f"https://proxycheck.io/v2/{ip}?key={api_key}&vpn=1&asn=0")
                result = response.json()
                proxy_status = result.get(ip, {}).get("proxy", "Não disponível")
                vpn_status = result.get(ip, {}).get("vpn", "Não disponível")

                if proxy_status == "yes":
                    vpn_status = "yes"
                else:
                    vpn_status = "no"
            except Exception:
                proxy_status = "Erro na consulta"
                vpn_status = "Erro na consulta"

            results.append((proxy_status, vpn_status))

        df['PROXY'], df['VPN'] = zip(*results)

        result_file = os.path.join(app.config['UPLOAD_FOLDER'], 'resultado.xlsx')
        df.to_excel(result_file, index=False, engine='openpyxl')

        # Emite o progresso final
        socketio.emit('progress', {
            'message': "Processo concluído!",
            'progress': 100
        })

        return send_file(result_file, as_attachment=True)

    return render_template('index.html')

@app.route('/filtro', methods=['GET', 'POST'])
def filtro():
    if request.method == 'POST':
        file = request.files['file']  # Arquivo enviado pelo usuário com os resultados
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Carregar a planilha com os resultados
        df = pd.read_excel(file_path)

        # Filtrar os dados onde "PROXY" e "VPN" são "yes"
        filtered_df = df[(df['PROXY'] == 'yes') & (df['VPN'] == 'yes')]

        # Salvar a nova planilha filtrada
        filtered_filename = 'resultado_filtrado.xlsx'
        filtered_path = os.path.join(app.config['UPLOAD_FOLDER'], filtered_filename)
        filtered_df.to_excel(filtered_path, index=False)

        # Disponibilizar para download a planilha filtrada
        return redirect(url_for('download_file', filename=filtered_filename))

    return render_template('filtro.html')


@app.route('/download/<filename>')
def download_file(filename):
    # Retornar o arquivo para o download
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


# Rodar o app
if __name__ == '__main__':
    socketio.run(app, debug=True)
