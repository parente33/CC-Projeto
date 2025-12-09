import asyncio
import json
from protocols.Telemetry import Telemetry
from protocols.MissionLink_Server import MissionLink_Server
from common.Mission import Mission
from common.Message import *
from http.server import BaseHTTPRequestHandler, HTTPServer
from database.Database import Database

bd = Database() #Inicia a base de dados e cria as tabelas
mission = MissionLink_Server()
telemetry = Telemetry(
        mode="server",
        host="localhost",
        port=50001
    )
class ObservationApi(BaseHTTPRequestHandler):

    @classmethod
    def start_ObservationApi(_class_):
        server = HTTPServer(("localhost",8000),_class_)
        print("Servidor rodando em http://localhost:8000")
        server.serve_forever()

    def json_data(self,data, code=200):
        """
        Função para enviar data na forma de json
        """
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        if self.path == "/active_rovers":
            rovers = asyncio.run(bd.get_rovers())

            self.json_data(rovers)

        if self.path == "/missions":
            missions = asyncio.run(bd.get_missions())
            self.json_data(missions)

        if self.path == "/reports":
            reports = asyncio.run(bd.get_RoversMissions())
            self.json_data(reports)


async def telemetry_rx(payload, addr):
    result:Message_Telemetry = await Message_Telemetry.decode(payload)
    await bd.insert_or_update_rover(result)
    print("Telemetry carregada")

async def mission_rx(connection_ID, payload):
    result:Message_Status = Message_Status.decode(payload)
    await bd.insert_rover_mission(result)
    print("Informaçao missao carregada")

async def mission_req(connection_ID, payload) :
    mission_id = int.from_bytes(payload[0:4])
    if mission_id != 0:
        await bd.update_missions(int.from_bytes(payload[0:4], 'big'),2)

    missao : Mission = await bd.get_mission()
    await bd.update_missions(missao.mission_id, 1)
    print("Request recebido " + missao.message())
    return missao.encode()
