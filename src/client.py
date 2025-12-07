import asyncio
from protocols.Telemetry import Telemetry
from protocols.MissionLink_Client import MissionLink_Client
from rover import *
import random

async def send_telemetry_loop(client: Telemetry, rover:Rover):
    """Envia telemetria normal a cada 10s."""
    try:
        while True:
            payload = await rover.createReport()

            await client.send_telemetry(payload)
            print(f"[CLIENT] Telemetria enviada (10s)")
            await asyncio.sleep(10)

    except asyncio.CancelledError:
        print("[CLIENT] Task de telemetria cancelada.")
        raise


async def send_MissionLink_loop(missionLink: MissionLink_Client, rover:Rover):

    try:
        while True:
            if rover.task != None:
                result:Mission = await missionLink.send_request(rover.task.mission_id.to_bytes(length=4,byteorder='big'))
            else:
                payload = bytes(4)
                result:Mission = await missionLink.send_request(payload)
            mission:Mission = Mission.decode(result)
            print("[CLIENT] REQUEST ENVIADO E RECEBIDO")
            await rover.setTask(mission)
            await rover.doingTask(missionLink)
            await asyncio.sleep(3)

    except asyncio.CancelledError:
        print("[CLIENT] Task de MissionLink cancelada.")
        raise


async def main():
    telemetria = Telemetry(mode = "client", host = 'localhost')
    missionLink = MissionLink_Client(host = 'localhost', port = 50000)
    rover = Rover(random.randint(1,1000)) #Exemplo, cada rover tera o seu IP
    # Conectar ao servidor
    try:
        await telemetria.connect()
    except Exception as e:
        print(f"[CLIENT] Erro ao conectar: {e}")
        return

    # Criar tasks das rotinas
    telemetry_task = asyncio.create_task(send_telemetry_loop(telemetria,rover))
    MissionLink_task = asyncio.create_task(send_MissionLink_loop(missionLink,rover))


    print("[CLIENT] Cliente iniciado. CTRL+C para parar.")

    try:
        # Mantém o programa vivo
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("\n[CLIENT] CTRL+C detectado. A encerrar cliente...")

    finally:
        # Cancelar tasks corretamente
        telemetry_task.cancel()
        MissionLink_task.cancel()

        try:
            await telemetry_task
        except asyncio.CancelledError:
            pass

        try:
            await MissionLink_task
        except asyncio.CancelledError:
            pass

        # Desligar o cliente
        await telemetria.disconnect()
        await missionLink.kill_client()

        print("[CLIENT] Encerrado com sucesso.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[MAIN] Cliente encerrado.")