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

class Mission_Status:
    def __init__(self, rover_id:int, mission_id:int, position:tuple[int,int], task:int, max_duration: int, current_duration: int, status:int):
        self.rover_id:int = rover_id
        self.mission_id:int = mission_id
        self.task:int= task
        self.position:tuple[int,int] = position
        self.max_duration = max_duration
        self.current_duration:int = current_duration
        self.status:int = status
        self.completion = int(self.current_duration * 100 / self.max_duration)
    
    def setCompletion(self, current_duration):
        self.current_duration = current_duration
        if self.max_duration > 0:
            self.completion = int(self.current_duration * 100 / self.max_duration)

    def setPosition(self, positon):
        self.position = positon

    def message(self):
        message = f"Rover ID :{self.rover_id}, Mission ID:{self.mission_id}, Completion:{self.completion}, Maximum_Time:{self.max_duration}, Current_Duration:{self.current_duration}, Status:{self.status}"
        return message


    def encode(self) -> bytes:
        data = bytearray()
        data += self.rover_id.to_bytes(length=4,byteorder='big')
        data += self.mission_id.to_bytes(length=4,byteorder='big')
        
        data += self.task.to_bytes(length=2,byteorder='big')
        
        data += self.position.__len__().to_bytes(length=2,byteorder='big')

        for positon in self.position:
            data += positon.to_bytes(length=4,byteorder='big')
        
        data += self.max_duration.to_bytes(length=4,byteorder='big')
        data += self.current_duration.to_bytes(length=4,byteorder='big')
        data += self.status.to_bytes(length=4,byteorder='big')

        return bytes(data)
    
    def decode(data:bytes):
        offset = 0

        rover_id = int.from_bytes(data[offset:offset+4], 'big')
        offset +=4

        mission_id = int.from_bytes(data[offset:offset+4], 'big')
        offset +=4

        task = int.from_bytes(data[offset:offset+2], 'big')
        offset +=2

        position_length = int.from_bytes(data[offset:offset+2], 'big')
        offset += 2

        position = []

        for _ in range(position_length):
            value = int.from_bytes(data[offset:offset+4], 'big')
            offset += 4
            position.append(value)

        max_duration = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        current_duration = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        status = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        return Mission_Status(rover_id,mission_id,tuple(position),task,max_duration,current_duration,status)
