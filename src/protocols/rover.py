import asyncio
from threading import *
from cache import *
from Mission import *
import time
from MissionLink_Client import *

class Rover:
    def __init__(self):
        self.id = 10
        self.positions = (0,0)
        self.task:Mission = None
        self.lock = Lock()
        self.status:Status = Status.WAITING.value
        self.mission_status = None 

    async def setId(self, id:int):
        self.id = id     

    async def setTask(self, task:Mission):
        self.task = task

    async def getAtualization_Interval(self):
        while self.task is None:
            await asyncio.sleep(0.1)

        return self.task.atualizations_interval
                

        

    async def doMove(self,current_position: tuple[int, int], objective_position: tuple[int, int], raio: int, time_passed: int):

        x, y = current_position
        ox, oy = objective_position

        for _ in range(time_passed):

            if x < ox:
                x += 1
            elif x > ox:
                x -= 1
            elif y < oy:
                y += 1
            elif y > oy:
                y -= 1

            dist = abs(x - ox) + abs(y - oy)
            if dist < raio:
                if x < ox: x -= 1
                elif x > ox: x += 1
                elif y < oy: y -= 1
                elif y > oy: y += 1
                break
        print(x,y)
        return (x, y)

    async def doingTask(self, missionLink:MissionLink_Client):
        current_duration = 0
        mission_status = Mission_Status(self.id, self.task.mission_id, self.positions, self.task.task, self.task.max_duration,
                         current_duration,self.status)

        while True:
            payload = mission_status.encode()
        
            await missionLink.send_message(payload)
            
            await asyncio.sleep(self.task.atualizations_interval)
            
            self.positions = await self.doMove(
                self.positions,
                (self.task.geographic_area[0], self.task.geographic_area[1]),
                self.task.geographic_area[2],
                self.task.atualizations_interval
            )
            mission_status.setPosition(self.positions)

            if self.positions[0] == self.task.geographic_area[0] and self.positions[1] == self.task.geographic_area[1]:
                self.status = Status.IN_MISSION.value
                mission_status.status = (Status.IN_MISSION).value
                break

        while current_duration < self.task.max_duration:
            await asyncio.sleep(self.task.atualizations_interval)
            current_duration += self.task.atualizations_interval
            mission_status.setCompletion(current_duration)
            payload = mission_status.encode()
            await missionLink.send_message(payload)

    async def createReport(self):
        report = Rover_Telemetry(self.id,self.status,self.positions)
        return await report.encode()







class Rover_Telemetry:

    def __init__(self, rover_id:int, rover_status:int, rover_position:tuple[int,int]):
        self.rover_id = rover_id
        self.rover_status = rover_status
        self.rover_position = rover_position

    async def decode(data: bytes):
        offset = 0

        rover_id = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        rover_status = Status(int.from_bytes(data[offset:offset+4], 'big'))
        offset += 4

        position_length = int.from_bytes(data[offset:offset+2], 'big')
        offset += 2

        position = []

        for _ in range(position_length):
            value = int.from_bytes(data[offset:offset+4], 'big')
            offset += 4
            position.append(value)
        tuple(position)

        return Rover_Telemetry(rover_id,rover_status,position)

    async def encode(self):
        data = bytearray()
        data += self.rover_id.to_bytes(length=4,byteorder='big')
        data += self.rover_status.to_bytes(length=4,byteorder='big')
        data += self.rover_position.__len__().to_bytes(length=2,byteorder='big')
        data += self.rover_position[0].to_bytes(length=2,byteorder='big')
        data += self.rover_position[1].to_bytes(length=2,byteorder='big')

        return data