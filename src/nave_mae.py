from socket import *
from threading import *
from protocols.cache import *

def Mission_Link_Service(s:socket, addr:tuple[str,int],cache:Cache):
    task:protocolMissionLink = cache.get_Task()
    s.sendto(task.encode(),addr)

def TelemetryService(s:socket,cache:Cache,addr):
    data,addr = s.recvfrom(1000)
    report:TelemetryStream = TelemetryStream.decode(data)
    print(report.rover_status,report.rover_position,report.rover_id)
    s.close

def Run_Mission_Link_Service(cache:Cache):
    s:socket = socket(AF_INET,SOCK_DGRAM)
    address = '10.0.0.20'
    port = 125

    try:
        s.bind((address,port))
    except OSError as e:
        print(e)
    
    while True:
        data,addr = s.recvfrom(1000)
        print(data.decode('utf-8'))
        Thread(target=Mission_Link_Service, args=(s,addr,cache)).start()
        
    s.close()

def Run_TelemetryService(cache: Cache):
    s = socket(AF_INET, SOCK_STREAM)
    address = '10.0.0.20'
    port = 120

    try:
        s.bind((address, port))
        print(f"Telemetry TCP server listening on {address}:{port}")
    except OSError as e:
        print("Erro no bind TCP:", e)
        return

    s.listen()  # IMPORTANTE — transforma em servidor TCP

    while True:
        conn, addr = s.accept()  # aceitando conexões
        Thread(target=TelemetryService, args=(conn, addr, cache)).start()

def main():
    threads : list = list()
    cache : Cache = Cache()
    threads.append(Thread(target=Run_Mission_Link_Service, args=(cache,)))
    threads.append(Thread(target=Run_TelemetryService, args=(cache,)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()

