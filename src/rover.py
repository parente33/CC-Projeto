from threading import *
from protocols.cache import *
from socket import *
from protocols.cache import protocolMissionLink
import time

class Rover:
    def __init__(self):
        self.id = 10
        self.positions = (0,0)
        self.task:protocolMissionLink = None
        self.lock = Lock()
        self.status:Status = Status.WAITING 

    def setId(self, id:int):
        #self.lock.acquire()
        self.id = id
        #self.lock.release()        

    def setTask(self, task:protocolMissionLink):
        #self.lock.acquire()
        self.task = task
        #self.lock.release()

    def getTask(self, addr):
        s:socket = socket(AF_INET, SOCK_DGRAM)
        s.sendto("Need".encode('utf-8'),addr)
        dados,addr = s.recvfrom(1000)
        self.task = protocolMissionLink.decode(dados)
        self.status = Status.WALKING
        self.doingTask(addr)
    

    def doMove(self,current_position: tuple[int, int], objective_position: tuple[int, int], raio: int, time_passed: int):

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

    def doingTask(self, addr):
        current_duration = 0

        while True:

            time.sleep(self.task.atualizations_interval)

            self.positions = self.doMove(
                self.positions,
                (self.task.geographic_area[0], self.task.geographic_area[1]),
                self.task.geographic_area[2],
                self.task.atualizations_interval
            )

            if self.positions[0] == self.task.geographic_area[0] and self.positions[1] == self.task.geographic_area[1]:
                self.status = Status.IN_MISSION
                break

        while current_duration < self.task.max_duration:
            time.sleep(self.task.atualizations_interval)
            current_duration += self.task.atualizations_interval



        self.getTask(addr)
    
    def sendRoverReport(self,addr):
        s:socket = socket(AF_INET, SOCK_STREAM)
        s.connect(addr)
        while True:
            report:TelemetryStream = TelemetryStream(self.id,self.status,self.positions)
            s.sendall(report.encode())
            




def main():
    rover:Rover = Rover()
    address = '10.0.0.20'
    port = 125
    if rover.task == None:
        Thread(target=rover.getTask, args=((address, port),)).start()
    Thread(target=rover.sendRoverReport,args=((address, 120),)).start()
        
if __name__ == "__main__":
    main()