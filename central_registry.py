from flask import Flask, request, jsonify

app = Flask(__name__)

registered_servers = {}

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    server_name = data.get('server_name')
    ip_address = data.get('ip_address')
    port = data.get('port')
    
    if not (server_name and ip_address and port):
        return jsonify({'error': 'Missing data'}), 400
    
    registered_servers[server_name] = {'ip_address': ip_address, 'port': port}
    return jsonify({'message': 'Registered successfully'}), 200

@app.route('/servers/<server_name>', methods=['GET'])
def get_server(server_name):
    server_info = registered_servers.get(server_name)
    if server_info:
        return jsonify(server_info), 200
    else:
        return jsonify({'error': 'Server not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
