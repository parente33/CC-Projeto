import csv
import ast
from enum import Enum 
from Mission import *

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