import base64
from flask import Flask, redirect, request, url_for, jsonify
import requests
from urllib.parse import urlencode

app = Flask(__name__)

# Credenciais fixas da aplicação (não estão no .env, como solicitado)
CLIENT_ID = '' # Insira seu Client ID aqui
CLIENT_SECRET = '' # Insira seu Client Secret aqui

# URL de redirecionamento configurada no painel do Tiny
REDIRECT_URI = '/oauth/tiny' # Insira sua URL de redirecionamento aqui

# Variável global para armazenar o token de acesso
access_token_global = None

# Rota inicial: redireciona para autenticação do Tiny
@app.route('/', methods=['GET'])
def auth_tiny():
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI
    }

    AUTH_URL = 'https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/auth'
    redirect_url = f'{AUTH_URL}?{urlencode(params)}'

    return redirect(redirect_url)

# Rota de callback do OAuth2
@app.route('/oauth/tiny', methods=['GET'])
def oauth_callback():
    global access_token_global

    code = request.args.get('code')
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    headers = {
        'Authorization': f"Basic {auth_header}",
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }

    TOKEN_URL = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/token"
    response = requests.post(TOKEN_URL, headers=headers, data=data)

    print('STATUS:', response.status_code)
    print('RESPONSE:', response.text)

    try:
        token_data = response.json()
        if 'access_token' in token_data:
            access_token_global = token_data['access_token']
            print('TINY (ACCESS TOKEN):', access_token_global)
            return redirect(url_for('sucesso'))
        else:
            return f"Erro ao obter token: {token_data}", 400
    except Exception as e:
        return f"Erro inesperado: {str(e)}", 500

# Página de confirmação após autenticação
@app.route('/sucesso')
def sucesso():
    return "✅ Token obtido com sucesso! Agora acesse: <a href='/pedidos'>/pedidos</a>"

# Endpoint funcional para testar: GET /sales/orders
@app.route('/pedidos', methods=['GET'])
def listar_pedidos():
    global access_token_global

    if not access_token_global:
        return "⚠️ Token não encontrado. Faça a autenticação primeiro acessando /", 401

    headers = {
        "Authorization": f"Bearer {access_token_global}",
        "Content-Type": "application/json"
    }

    url = "https://erp.tiny.com.br/api/v3/sales/orders" # Insira a URL do endpoint de pedidos

    try:
        response = requests.get(url, headers=headers)
        print("STATUS:", response.status_code)
        print("RESPONSE RAW:", response.text)

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return f"Erro ao acessar a API: {response.text}", response.status_code
    except Exception as e:
        return f"Erro ao acessar a API: {str(e)}", 500

# Inicia o servidor Flask
if __name__ == '__main__':
    app.run(debug=True, port=8080)
