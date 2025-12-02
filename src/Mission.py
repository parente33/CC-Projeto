import ast



class Mission:
    def __init__(self,mission_id:int, geographic_area: str|tuple, task:str, max_duration: int, atualization_interval: int):
        self.mission_id = mission_id
        if isinstance(geographic_area, str):
            self.geographic_area = ast.literal_eval(geographic_area)
        else:
            self.geographic_area = geographic_area
        self.task = task
        self.max_duration = max_duration
        self.atualization_interval = atualization_interval

    def message(self):
        message = f"{self.mission_id},{self.geographic_area},{self.task},{self.max_duration},{self.atualization_interval}"
        return message


    def encode(self) -> bytes:
        data = bytearray()
        data += self.mission_id.to_bytes(length=4,byteorder='big')

        data += self.geographic_area.__len__().to_bytes(length=2,byteorder='big')
        for geographic_area_camps in self.geographic_area:
            data += geographic_area_camps.to_bytes(length=4,byteorder='big')

        # task (string sem tamanho fixo)
        task_bytes = self.task.encode("utf-8")
        data += len(task_bytes).to_bytes(2, 'big')   # tamanho da string
        data += task_bytes                           # conteúdo UTF-8

        data += self.max_duration.to_bytes(length=4,byteorder='big')
        data += self.atualization_interval.to_bytes(length=4,byteorder='big')

        return bytes(data)

    def decode(data: bytes):
        offset = 0

        mission_id = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        geographic_area_length = int.from_bytes(data[offset:offset+2], 'big')
        offset += 2

        geographic_area = []

        for _ in range(geographic_area_length):
            value = int.from_bytes(data[offset:offset+4], 'big')
            offset += 4
            geographic_area.append(value)

        # 1. Lê o tamanho da string task (2 bytes)
        task_len = int.from_bytes(data[offset:offset+2], 'big')
        offset += 2   # offset anda 2 bytes

        # 2. Lê a string com o tamanho indicado
        task = data[offset : offset + task_len].decode('utf-8')
        offset += task_len   # offset anda task_len bytes


        max_duration = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        atualization_interval = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4

        return Mission(
            mission_id,
            tuple(geographic_area),
            task,
            max_duration,
            atualization_interval
        )