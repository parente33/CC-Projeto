import asyncio
from Telemetry import Telemetry
from MissionLink_Client import MissionLink_Client
from rover import *
from cache import Mission

async def send_telemetry_loop(client: Telemetry, rover:Rover):
    """Envia telemetria normal a cada 10s."""
    try:
        while True:
            try:
                payload = await rover.createReport()
            except Exception as e:
                print("Erro ao criar report:", e)
                raise
            
            interval = await rover.getAtualization_Interval()
            await client.send_telemetry(payload)
            print(f"[CLIENT] Telemetria enviada {interval}")
            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        print("[CLIENT] Task de telemetria cancelada.")
        raise


async def send_MissionLink_loop(missionLink: MissionLink_Client, rover:Rover):

    

    try:
        while True:
            result:Mission = await missionLink.send_request(bytes([0b0001]))
            mission:Mission = Mission.decode(result)
            print("[CLIENT] REQUEST ENVIADO E RECEBIDO")
            print(mission.message())
            await rover.setTask(mission)
            await rover.doingTask()
            print("[CLIENT] MissionLink enviado (60s)")
            await asyncio.sleep(60)

    except asyncio.CancelledError:
        print("[CLIENT] Task de MissionLink cancelada.")
        raise


async def main():
    telemetria = Telemetry(mode = "client", host = 'localhost')
    missionLink = MissionLink_Client(host = 'localhost', port = 50000)
    rover = Rover()
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
    asyncio.run(main())
