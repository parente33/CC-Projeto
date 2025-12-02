class Message_Telemetry :


    def __init__(self, rover_id:int, rover_status:int, rover_position:tuple[int,int]):
        self.rover_id = rover_id
        self.rover_status = rover_status
        self.rover_position = rover_position

    @staticmethod
    async def decode(data: bytes):
        offset = 0

        rover_id = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        rover_status = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        position_length = int.from_bytes(data[offset:offset+2], 'big')
        offset += 2

        position = []

        for _ in range(position_length):
            value = int.from_bytes(data[offset:offset+4], 'big')
            offset += 4
            position.append(value)
        tuple(position)

        return Message_Telemetry(rover_id,rover_status,position)

    async def encode(self):
        data = bytearray()
        data += self.rover_id.to_bytes(length=4,byteorder='big')
        data += self.rover_status.to_bytes(length=4,byteorder='big')
        data += self.rover_position.__len__().to_bytes(length=2,byteorder='big')
        data += self.rover_position[0].to_bytes(length=2,byteorder='big')
        data += self.rover_position[1].to_bytes(length=2,byteorder='big')

        return data


class Message_Status :

    def __init__(self, rover_id:int, mission_id:int, max_duration: int, current_duration: int, status:int):
        self.rover_id:int = rover_id
        self.mission_id:int = mission_id
        self.max_duration = max_duration
        self.current_duration:int = current_duration
        self.status:int = status
        self.completion = int(self.current_duration * 100 / self.max_duration)

    def setCompletion(self, current_duration):
        self.current_duration = current_duration
        if self.max_duration > 0:
            self.completion = int(self.current_duration * 100 / self.max_duration)



    def decode(data:bytes):
        offset = 0

        rover_id = int.from_bytes(data[offset:offset+4], 'big')
        offset +=4

        mission_id = int.from_bytes(data[offset:offset+4], 'big')
        offset +=4

        max_duration = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        current_duration = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        status = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        m = Message_Status(rover_id,mission_id,max_duration,current_duration,status)
        return m

    def encode(self) -> bytes:
        data = bytearray()
        data += self.rover_id.to_bytes(length=4,byteorder='big')
        data += self.mission_id.to_bytes(length=4,byteorder='big')
        data += self.max_duration.to_bytes(length=4,byteorder='big')
        data += self.current_duration.to_bytes(length=4,byteorder='big')
        data += self.status.to_bytes(length=4,byteorder='big')
        return bytes(data)

