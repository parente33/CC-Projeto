import csv
import ast
from enum import Enum 

class Status(Enum):
    WAITING = 0
    IN_MISSION = 1
    WALKING = 2
    SLEEP = 3

class TASK(Enum):
    CLEANING_AREA = 0
    ANALYSING_TERRAIN = 1
    REPAIRING_SATELITE = 2


        
        


class Mission:
    def __init__(self, rover_id:int, mission_id:int, geographic_area:tuple[int,int,int], task:int, max_duration: int, atualizations_interval: int):
        self.rover_id = rover_id
        self.mission_id = mission_id
        self.geographic_area = geographic_area
        self.task = task
        self.max_duration = max_duration
        self.atualizations_interval = atualizations_interval
    
    def message(self):
        message = f"{self.rover_id},{self.mission_id},{self.geographic_area},{self.task},{self.max_duration},{self.atualizations_interval}"
        return message

    
    def encode(self) -> bytes:
        data = bytearray()
        data += self.rover_id.to_bytes(length=4,byteorder='big')
        data += self.mission_id.to_bytes(length=4,byteorder='big')
        
        data += self.geographic_area.__len__().to_bytes(length=2,byteorder='big')
        for geographic_area_camps in self.geographic_area:
            data += geographic_area_camps.to_bytes(length=4,byteorder='big')
        
        data += self.task.to_bytes(length=2,byteorder='big')

        data += self.max_duration.to_bytes(length=4,byteorder='big')
        data += self.atualizations_interval.to_bytes(length=4,byteorder='big')

        return bytes(data)

    def decode(data: bytes):
        offset = 0

        rover_id = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        mission_id = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        geographic_area_length = int.from_bytes(data[offset:offset+2], 'big')
        offset += 2

        geographic_area = []

        for _ in range(geographic_area_length):
            value = int.from_bytes(data[offset:offset+4], 'big')
            offset += 4
            geographic_area.append(value)
        tuple(geographic_area)

        task = int.from_bytes(data[offset:offset+2], 'big')
        offset += 2

        max_duration = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        atualization_interval = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        return Mission(
            rover_id,
            mission_id,
            tuple(geographic_area),
            task,
            max_duration,
            atualization_interval
        )


class Cache:
    def __init__(self):
        with open("missions.csv", newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.tasks = list()
            for row in reader:
                rover_id = int(row["rover_id"])
                mission_id = int(row["mission_id"])
                geographic_area = ast.literal_eval(row["geographic_area"])
                task = int(row["task"])
                max_duration = int(row["max_duration"])
                atualizations_interval = int(row["atualization_interval"])

                ml = Mission(rover_id, mission_id, geographic_area, task, max_duration, atualizations_interval)
                self.tasks.append(ml)

    async def get_Task(self) -> Mission:
        return self.tasks.pop(0)