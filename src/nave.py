import asyncio
import json
from protocols.Telemetry import Telemetry
from protocols.MissionLink_Server import MissionLink_Server
from Mission import Mission
from Message import *
from http.server import BaseHTTPRequestHandler, HTTPServer
from Database import Database
import threading

bd = Database() #Inicia a base de dados e cria as tabelas

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
            rovers = bd.get_rovers()
            self.json_data(rovers)

        if self.path == "/missions":
            missions = bd.get_missions()
            self.json_data(missions)
        
        if self.path == "/reports":
            reports = bd.get_RoversMissions()
            self.json_data(reports)
             

mission = MissionLink_Server()
telemetry = Telemetry(
        mode="server",
        host="localhost",
        port=50001
    )

async def telemetry_rx(payload, addr):
    result:Message_Telemetry = await Message_Telemetry.decode(payload)
    bd.insert_or_update_rover(result)
    print("Telemetry carregada")

async def mission_rx(connection_ID, payload):
    result:Message_Status = Message_Status.decode(payload)
    bd.insert_rover_mission(result)
    print("Informaçao missao carregada")

async def mission_req(connection_ID, payload) :
    missao : Mission = bd.get_mission()
    print("Request recebido " + missao.message())
    return missao.encode()

async def main():
    bd.load_missions_from_csv("missions.csv")
    telemetry.callback_data = telemetry_rx
    mission.callback_data = mission_rx
    mission.callback_request = mission_req

    # --- Criar tasks ---
    t1 = asyncio.create_task(telemetry.start_server())
    t2 = asyncio.create_task(mission.start())
    threading.Thread(target=ObservationApi.start_ObservationApi, daemon=True).start()


    print("[SERVERS] Telemetry e MissionLink iniciados. CTRL+C para parar.")

    try:
        await asyncio.gather(t1, t2)

    except asyncio.CancelledError:
        print("\n[SHUTDOWN] A terminar servidores...")

    finally:
        # Encerrar Telemetry
        try:
            await telemetry.shutdown()
        except:
            pass

        # Encerrar MissionLink
        try:
            await mission.end()
        except:
            pass

        print("[SHUTDOWN] Todos os servidores terminados.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[MAIN] Interrompido pelo utilizador.")
