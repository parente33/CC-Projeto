import asyncio
from Telemetry import Telemetry
from MissionLink_Client import MissionLink_Client


async def send_telemetry_loop(client: Telemetry):
    """Envia telemetria normal a cada 10s."""
    try:
        while True:
            payload = b"\x0F"      # exemplo (0b01111)
            await client.send_telemetry(payload)
            print("[CLIENT] Telemetria enviada (10s)")
            await asyncio.sleep(10)

    except asyncio.CancelledError:
        print("[CLIENT] Task de telemetria cancelada.")
        raise


async def send_MissionLink_loop(missionLink: MissionLink_Client):
    result = await missionLink.send_request(bytes([0b0001]))
    print("[CLIENT] REQUEST ENVIADO E RECEBIDO")
    print(result)
    try:
        while True:
            payload = b"\xAA"      # exemplo MissionLink
            await missionLink.send_message(payload)
            print("[CLIENT] MissionLink enviado (60s)")
            await asyncio.sleep(60)

    except asyncio.CancelledError:
        print("[CLIENT] Task de MissionLink cancelada.")
        raise


async def main():
    telemetria = Telemetry(mode = "client", host = 'localhost')
    missionLink = MissionLink_Client(host = 'localhost')

    # Conectar ao servidor
    try:
        await telemetria.connect()
    except Exception as e:
        print(f"[CLIENT] Erro ao conectar: {e}")
        return

    # Criar tasks das rotinas
    telemetry_task = asyncio.create_task(send_telemetry_loop(telemetria))
    MissionLink_task = asyncio.create_task(send_MissionLink_loop(missionLink))

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
