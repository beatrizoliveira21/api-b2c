from flask import Flask, make_response, jsonify, request
from bson import json_util
from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
import json
from datetime import datetime
import openpyxl
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)

try:  
    ssh_preprod = SSHTunnelForwarder(
        ('200.148.80.252',22018),
        ssh_username='hulrich',
        ssh_password='hulrich',
        local_bind_address=('localhost',27020),
        remote_bind_address=('localhost', 27020)
        )
    ssh_preprod.start()
except Exception as erro:
    
    print(erro)

# estabelecendo conexão com o banco de dados
conn = MongoClient("mongodb://mongo_admin:hY3YQ!G%25HqJ%24Cjz%26%26in5@localhost:27020/?authMechanism=DEFAULT")
db_name = conn.inventory_control
collection_users = db_name.users
collection_devices = db_name.devices

@cross_origin
@app.route("/usuarios", methods=["GET", "POST"])
def get_users():
    """Ver todos ps usuarios na base"""
    users = []
    try:
        for i in collection_users.find():
            users.append(i)
    
    except Exception as erro:
        print(erro)
    users_json = json.loads(json_util.dumps(users))
    return make_response(jsonify(users_json))

@cross_origin
@app.route("/create-user", methods=["POST"])
def create_user():
    """Adicionar um novo usuario na base"""
    user = {
        "username" : request.json["username"],
        "password" : request.json["password"],
        "devices" : []
        }
    try:
        collection_users.insert_one(json.loads(json_util.dumps(user)))
        return make_response(jsonify(user))

    except Exception as erro:
        print(erro)
        error = {"message" : "no_create"}
        return make_response( jsonify(error))
    
@cross_origin
@app.route("/usuario/login-user", methods=["POST", "GET"])
def login():
    """Tentativa de Login do usuario"""
    user = {
        "username" : request.json["username"],
        "password" : request.json["password"]
        }
    try:
        usuarios = collection_users.find_one(user)
        if usuarios == None:
            error = {"message" : "usuário não encontrado na base de dados"}
            return make_response(jsonify(error))
        return make_response(jsonify((json.loads(json_util.dumps(usuarios)))))
    except Exception as erro:
        print(erro)
        error = {"message" : "Erro"}
        return make_response( jsonify(error))

@cross_origin
@app.route("/devices", methods=["GET"])
def devices():
    """Ver todos dispositivos disponiveis"""
    devices = []
    try:
        for i in collection_devices.find():
            devices.append(i)
    
    except Exception as erro:
        print(erro)
    devices_json = json.loads(json_util.dumps(devices))
    return make_response( jsonify(devices_json))

@cross_origin
@app.route("/insert-devices", methods=["POST"])
def new_device():
    """Inserir um novo dispositivo"""
    device = {
        "dispositivo" : {
            "equipamento" : request.json["dispositivo"]["equipamento"],
            "fabricante" : request.json["dispositivo"]["fabricante"],
            "nome_modelo" : request.json["dispositivo"]["nome_modelo"],
            "modelo" : request.json["dispositivo"]["modelo"],
            "serial_number" : request.json["dispositivo"]["serial_number"],
            "device_number" : request.json["dispositivo"]["device_number"],
            "localization" : {
                "armario" : request.json["dispositivo"]["localization"]["armario"],
                "prateleira" : request.json["dispositivo"]["localization"]["prateleira"]
            },
            "data_fabricacao" : request.json["dispositivo"]["data_fabricacao"],
            "log_reversa" : request.json["dispositivo"]["log_reversa"],
            "emprestado" : request.json["dispositivo"]["emprestado"],
            "emprestimo_count" : request.json["dispositivo"]["emprestimo_count"],
            "emprestimo" : {
                "responsavel" : request.json["dispositivo"]["emprestimo"]["responsavel"],
                "data_retirada" : request.json["dispositivo"]["emprestimo"]["data_retirada"],
                "data_devolucao" : request.json["dispositivo"]["emprestimo"]["data_devolucao"],
                "tempo_emprestado" : request.json["dispositivo"]["emprestimo"]["tempo_emprestado"]
            }
        }
        }
    try:
        collection_devices.insert_one(json.loads(json_util.dumps(device)))
        return make_response(jsonify(device))

    except Exception as erro:
        print(erro)
        error = {"message" : "no_create"}
        return make_response( jsonify(error))


@cross_origin
@app.route("/take-device", methods=["POST", "GET"])
def take_device():
    """Pegar um dispositivo emprestado"""
    usuario = request.json["username"]
    # device_number = request.json["device_number"]
    user = {
        "username" : request.json["username"]
    }

    device = {}
    # antigo_valor = []
    try:
        for i in collection_devices.find():
            if i["dispositivo"]["serial_number"] == request.json["serial_number"]:
                device = i


        #atualizar o banco:
        usuario = collection_users.find_one(user)

        #atualizando a lista de dispositivos do usuario
        atualizar_lista = []
        for i in usuario["devices"]:
            atualizar_lista.append(i)

        atualizar_lista.append(device["dispositivo"]["device_number"])
        lista = list(set(atualizar_lista))
        collection_users.update_one({"_id" : usuario["_id"]},{"$set":{"devices" : lista}})
        #----- funcionando
        atl = device["dispositivo"]
        atl["emprestado"] = True
        atl["emprestimo"]["responsavel"] = usuario["username"]
        atl["emprestimo"]["data_retirada"] = str(datetime.now())
        atl["emprestimo_count"] += 1

        # Atualizar a a collection dispositivos
        collection_devices.update_one({"_id" : device["_id"]},{"$set":{"dispositivo":atl}})
        usuario["devices"] = atualizar_lista

        users = json.loads(json_util.dumps(usuario))
        devicer = json.loads(json_util.dumps(device))

        info = {"user" : users,
                "disp" : devicer}
        
        return make_response(info)
    except Exception as erro:
        info = {
            "message" : "ocorreu algum erro tente mais tarde"
        }
        return make_response(info)

    
@cross_origin
@app.route("/give-back-device", methods=["POST", "GET"])
def give_device():
    """Devolver dispositivo emprestado"""
    usuario = request.json["username"]
    # device_number = request.json["device_number"]
    user = {
        "username" : request.json["username"]
    }

    device = {}
    # antigo_valor = []
    try:
        for i in collection_devices.find():
            if i["dispositivo"]["serial_number"] == request.json["serial_number"]:
                device = i

        #atualizar o banco:
        usuario = collection_users.find_one(user)

        #atualizando a lista de dispositivos do usuario
        atualizar_lista = []
        for i in usuario["devices"]:
            atualizar_lista.append(i)
        
        atualizar_lista.remove(device["dispositivo"]["device_number"])
        collection_users.update_one({"_id" : usuario["_id"]},{"$set":{"devices" : atualizar_lista}})
        #----- funcionando
        atl = device["dispositivo"]
        atl["emprestado"] = False
        atl["emprestimo"]["responsavel"] = ""
        atl["emprestimo"]["data_devolucao"] = str(datetime.now())


        # Atualizar a a collection dispositivos
        collection_devices.update_one({"_id" : device["_id"]},{"$set":{"dispositivo":atl}})
        usuario["devices"] = atualizar_lista

        users = json.loads(json_util.dumps(usuario))
        devicer = json.loads(json_util.dumps(device))

        info = {"user" : users,
                "disp" : devicer}
        
        return make_response(info)
    except Exception as erro:
        info = {
            "message" : "verifique se o dispositivo já nao foi devolvido anteriormente"
        }
        return make_response(info)

if __name__ == "__main__":
    app.run(debug=True)
