import sys
from .Rover import *

async def main(argv:list[str]):
    telemetria = Telemetry(mode = "client", host = "localhost",port=50001)
    missionLink = MissionLink_Client(host = "localhost", port = 50000)
    rover = Rover(int(argv[1]))
    # Conectar ao servidor
    try:
        await telemetria.connect()
    except Exception as e:
        print(f"[CLIENT] Erro ao conectar: {e}")
        return

    # Criar tasks das rotinas
    telemetry_task = asyncio.create_task(rover.send_telemetry_loop(telemetria))
    MissionLink_task = asyncio.create_task(rover.send_MissionLink_loop(missionLink))


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
        asyncio.run(main(sys.argv))
    except KeyboardInterrupt:
        print("\n[MAIN] Cliente encerrado.")