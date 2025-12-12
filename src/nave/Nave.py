from protocols.Telemetry import Telemetry
from protocols.MissionLink_Server import MissionLink_Server
from common.Mission import Mission
from common.Message import *
from database.Database import Database
from .ObservationApi import ObservationApi
class Nave :
    def __init__(self,host_adress = "localhost",telem_port=50001,mission_port=50000,api_port=800):
        self.bd : Database = Database()
        self.mission = MissionLink_Server(host=host_adress,port=mission_port,callback_data = self.mission_rx,
                                          callback_request = self.mission_req)
        self.telemetry = Telemetry(
                mode="server",
                host=host_adress,
                port=telem_port,
                callback_data = self.telemetry_rx)

        ObservationApi.bd = self.bd
        ObservationApi.host =host_adress
        ObservationApi.port = api_port

    async def telemetry_rx(self,payload, addr):
        result:Message_Telemetry = await Message_Telemetry.decode(payload)
        if self.bd.closed == True : return
        await self.bd.insert_or_update_rover(result)
        print("Telemetry carregada")

    async def mission_rx(self,connection_ID, payload):
        result:Message_Status = Message_Status.decode(payload)
        if self.bd.closed == True : return
        await self.bd.insert_rover_mission(result)
        print("Informaçao missao carregada")

    async def mission_req(self,connection_ID, payload) :
        mission_id = int.from_bytes(payload[0:4])
        if self.bd.closed == True : return
        if mission_id != 0:
            await self.bd.update_missions(int.from_bytes(payload[0:4], 'big'),2)
        missao : Mission = await self.bd.get_mission()
        await self.bd.update_missions(missao.mission_id, 1)
        print("Request recebido " + missao.message())
        return missao.encode()

    async def shutdown(self) :
        if self.telemetry :
            await self.telemetry.shutdown()
        if self.mission :
            await self.mission.end()
        if self.bd :
            await self.bd.close()
