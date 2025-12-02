import asyncio
from Mission import *
from protocols.MissionLink_Client import *
from Message import *


status_dict = {
    0 : "Waiting",
    1 : "In Mission",
    2 : "Walking",
    3 : "Sleep"
}

class Rover:
    def __init__(self,id : int):
        self.id = id
        self.positions = (0,0)
        self.task:Mission = None
        self.status:int =  0 #Waiting
        self.mission_status = None

    async def setId(self, id:int):
        self.id = id

    async def setTask(self, task:Mission):
        self.task = task

    async def getAtualization_Interval(self):
        while self.task is None:
            await asyncio.sleep(0.1)

        return self.task.atualization_interval




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
        return (x, y)

    async def doingTask(self, missionLink:MissionLink_Client):
        current_duration = 0
        mission_status = Message_Status(self.id, self.task.mission_id, self.task.max_duration,
                         current_duration,self.status)

        while True:
            payload = mission_status.encode()

            await missionLink.send_message(payload)

            await asyncio.sleep(self.task.atualization_interval)

            self.positions = await self.doMove(
                self.positions,
                (self.task.geographic_area[0], self.task.geographic_area[1]),
                self.task.geographic_area[2],
                self.task.atualization_interval
            )
            if self.positions[0] == self.task.geographic_area[0] and self.positions[1] == self.task.geographic_area[1]:
                self.status = 1 #in mission
                mission_status.status = 1
                break

        while current_duration < self.task.max_duration:
            await asyncio.sleep(self.task.atualization_interval)
            current_duration += self.task.atualization_interval
            mission_status.setCompletion(current_duration)
            payload = mission_status.encode()
            await missionLink.send_message(payload)

    async def createReport(self):
        report = Message_Telemetry(self.id,self.status,self.positions)
        return await report.encode()