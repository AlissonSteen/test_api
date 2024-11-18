from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import requests
import time
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        column = request.form['column']
        api_key = request.form['api_key']

        # Carregar a planilha
        df = pd.read_excel(file)

        # Obter valores da coluna
        ips = df[column].dropna().tolist()
        proxy_results = []
        vpn_results = []

        # Consultar cada IP individualmente
        for ip in ips:
            try:
                # Construir URL
                url = f"https://proxycheck.io/v2/{ip}"
                params = {
                    "key": api_key,  # Chave API
                    "vpn": 1,  # Incluir informações de VPN
                    "risk": 1  # Incluir nível de risco
                }

                # Realizar requisição
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Analisar o resultado para o IP
                if ip in data:
                    proxy_results.append(data[ip].get("proxy", "Erro"))
                    vpn_results.append(data[ip].get("vpn", "Erro"))
                else:
                    proxy_results.append("Erro")
                    vpn_results.append("Erro")
            except Exception as e:
                proxy_results.append("Erro")
                vpn_results.append("Erro")
            time.sleep(0.5)  # Delay para evitar limite de requisições

        # Adicionar resultados ao DataFrame
        df['Resultado API'] = pd.Series(proxy_results)
        df['VPN'] = pd.Series(vpn_results)

        # Salvar o arquivo Excel com os resultados
        output_filename = 'resultado.xlsx'
        df.to_excel(output_filename, index=False)

        # Disponibilizar para download
        return redirect(url_for('download_file', filename=output_filename))

    return render_template('index.html')


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(os.getcwd(), filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)  # Para o Render, use a porta 5000
