from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import pandas as pd
import requests
import time
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        column = int(request.form['column'])  # Receber a coluna como número
        api_key = request.form['api_key']

        # Carregar a planilha
        df = pd.read_excel(file)

        # Verificar se a coluna está dentro do intervalo de colunas
        if column < 1 or column > len(df.columns):
            return "Número de coluna inválido!"

        # Acessar a coluna correta usando iloc (baseado no índice)
        ips = df.iloc[:, column - 1].dropna().tolist()  # Ajuste aqui para usar o índice correto (coluna-1)

        proxy_results = []
        vpn_results = []

        # Consultar cada IP individualmente
        for ip in ips:
    try:
        # Construir URL
        url = f"https://proxycheck.io/v2/{ip}"
        params = {
            "key": api_key,
            "vpn": 1,
            "risk": 1
        }

        # Realizar requisição
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Acessar resultado com verificação de chave
        vpn_status = data.get(ip, {}).get("vpn", "Não Disponível")
        proxy_status = data.get(ip, {}).get("proxy", "Não Disponível")

        proxy_results.append(proxy_status)
        vpn_results.append(vpn_status)
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
