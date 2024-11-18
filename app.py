import os
import time
import requests
import pandas as pd
from flask import Flask, render_template, request, send_from_directory, redirect, url_for

app = Flask(__name__)

# Configurações do app
UPLOAD_FOLDER = 'uploads'  # Diretório para salvar arquivos temporários
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']  # Arquivo enviado pelo usuário
        column = int(request.form['column'])  # Número da coluna selecionada (começa de 1)
        api_key = request.form['api_key']  # Chave da API

        # Salvar o arquivo no diretório temporário
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Carregar a planilha
        df = pd.read_excel(file_path)

        # Verificar se a coluna é válida
        if column < 1 or column > len(df.columns):
            return "Número de coluna inválido!"

        # Acessar a coluna selecionada usando o índice (coluna-1)
        ips = df.iloc[:, column - 1].dropna().tolist()  # Remover valores NaN

        proxy_results = []
        vpn_results = []

        # Consultar cada IP individualmente na API
        for ip in ips:
            try:
                # Construir URL da API
                url = f"https://proxycheck.io/v2/{ip}"
                params = {
                    "key": api_key,
                    "vpn": 1,
                    "risk": 1
                }

                # Realizar requisição para a API
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Verificar o resultado e obter valores para "proxy" e "vpn"
                vpn_status = data.get(ip, {}).get("vpn", "Não Disponível")
                proxy_status = data.get(ip, {}).get("proxy", "Não Disponível")

                # Armazenar os resultados
                proxy_results.append(proxy_status)
                vpn_results.append(vpn_status)

            except Exception as e:
                proxy_results.append("Erro")
                vpn_results.append("Erro")
            
            time.sleep(0.5)  # Delay para evitar limite de requisições

        # Adicionar os resultados no DataFrame
        df['Resultado API'] = pd.Series(proxy_results)
        df['VPN'] = pd.Series(vpn_results)

        # Salvar o arquivo com os resultados
        output_filename = 'resultado.xlsx'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        df.to_excel(output_path, index=False)

        # Disponibilizar para download
        return redirect(url_for('download_file', filename=output_filename))

    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    # Retornar o arquivo para o download
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
