import asyncio
import time

class Telemetry:
    """
    PROTOCOLO TelemetryStream sobre TCP com AsyncIO
    Comunicação unidirecional: Rover (cliente) → Nave-Mãe (servidor)
    Cliente envia telemetria, servidor apenas recebe
    """

    def __init__(self, mode='client', host ='localhost', port=50001):
        """
        Inicializa o protocolo Telemetry
        Args:
            mode: 'client' ou 'server'
            host: hostname ou IP
            port: porta TCP
        """
        self.mode = mode
        self.host = host
        self.port = port

        self.active_clients = {}  # {addr: {'reader': reader, 'writer': writer, 'last_activity': timestamp}}

        self.callback_data = None

        self.shutdown_flag = False
        self.inactivity_timeout = 60  # segundos sem receber dados
        self.check_interval = 10      # verifica timeouts a cada 10s

        # Cliente
        self.reader = None
        self.writer = None

        # Servidor
        self.server = None
        self.server_task = None
        self.timeout_checker_task = None


    async def connect(self):
        """
        Conecta ao servidor (modo cliente)
        """
        if self.mode != 'client':
            raise Exception("connect() só funciona em modo cliente")

        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        print(f"[Telemetry Client] Conectado a {self.host}:{self.port}")


    async def send_telemetry(self, payload):
        """
        Envia telemetria para o servidor (modo cliente)
        Args:
            payload: bytes a enviar
        """
        if self.mode != 'client':
            raise Exception("send_telemetry() só funciona em modo cliente")

        if not self.writer:
            raise Exception("Cliente não conectado")

        try:
            # Formato simples: 4 bytes tamanho + payload
            tamanho = len(payload).to_bytes(4, 'big')
            self.writer.write(tamanho + payload)
            await asyncio.wait_for(self.writer.drain(), timeout = 5.0)
        except asyncio.TimeoutError:
            print(f"[Telemetry] Timeout ao enviar dados")
            raise
        except Exception as e:
            print(f"[Telemetry] Erro ao enviar: {e}")
            raise


    async def _receive_telemetry(self, reader):
        """
        Recebe uma mensagem de telemetria
        Args:
            reader: StreamReader
        Returns:
            bytes recebidos ou None se conexão fechada
        """
        try:
            # Lê tamanho (4 bytes)
            size_data = await asyncio.wait_for(reader.readexactly(4), timeout = self.inactivity_timeout)
        except asyncio.TimeoutError:
            print("[Telemetry] Timeout ao receber dados")
            return None
        except asyncio.IncompleteReadError:
            # Conexão fechada
            return None
        except Exception as e:
            print(f"[Telemetry] Erro ao receber tamanho: {e}")
            return None

        if not size_data:
            return None

        size = int.from_bytes(size_data, 'big')

        try:
            # Lê payload
            payload = await asyncio.wait_for(reader.readexactly(size), timeout=10.0)
            return payload
        except asyncio.TimeoutError:
            print("[Telemetry] Timeout ao receber payload")
            return None
        except asyncio.IncompleteReadError:
            return None
        except Exception as e:
            print(f"[Telemetry] Erro ao receber payload: {e}")
            return None


    async def _handle_client(self, reader, writer):
        """
        Gestão de um cliente individual (modo servidor)
        Recebe telemetria continuamente até desconexão
        Args:
            reader: StreamReader
            writer: StreamWriter
        """
        addr = writer.get_extra_info('peername')

        self.active_clients[addr] = {
            'reader': reader,
            'writer': writer,
            'last_activity': time.time()
        }

        print(f"[Telemetry Server] Cliente conectado: {addr}")

        try:
            # Loop de recepção contínua
            while not self.shutdown_flag:
                data = await self._receive_telemetry(reader)

                if data is None:
                    # Conexão fechada ou timeout
                    break

                self.active_clients[addr]['last_activity'] = time.time()

                # Callback de dados recebidos
                if self.callback_data:
                    if asyncio.iscoroutinefunction(self.callback_data):
                        asyncio.create_task(self.callback_data(data, addr))
                    else:
                        self.callback_data(data, addr)

        except Exception as e:
            print(f"[Telemetry Server] Erro com cliente {addr}: {e}")

        finally:
            await self._remove_client(addr)


    async def _remove_client(self, addr):
        """
        Remove cliente da lista de ativos e fecha conexão
        Args:
            addr: endereço do cliente
        """
        if addr not in self.active_clients:
            return

        print(f"[Telemetry Server] Cliente desconectado: {addr}")

        writer = self.active_clients[addr]['writer']
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

        del self.active_clients[addr]



    async def _check_inactive_clients(self):
        """
        Verifica clientes inativos e remove os que excederam timeout (modo servidor)
        Timeout passivo: se não recebe dados há X segundos, desconecta
        """
        while not self.shutdown_flag:
            await asyncio.sleep(self.check_interval)

            current_time = time.time()
            disconnected = []

            for addr, info in list(self.active_clients.items()):
                if current_time - info['last_activity'] > self.inactivity_timeout:
                    print(f"[Telemetry Server] Cliente {addr} inativo há {self.inactivity_timeout}s")
                    disconnected.append(addr)

            for addr in disconnected:
                await self._remove_client(addr)


    async def start_server(self):
        """
        Inicia o servidor (modo servidor)
        """
        if self.mode != 'server':
            raise Exception("start_server() só funciona em modo servidor")

        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )

        print(f"[Telemetry Server] A ouvir em {self.host}:{self.port}")

        self.timeout_checker_task = asyncio.create_task(self._check_inactive_clients())

        # Task do servidor
        self.server_task = asyncio.create_task(self.server.serve_forever())


    async def disconnect(self):
        """
        Desconecta do servidor (modo cliente)
        """
        if self.mode != 'client':
            raise Exception("disconnect() só funciona em modo cliente")

        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
                print("[Telemetry Client] Desconectado")
            except Exception as e:
                print(f"[Telemetry Client] Erro ao desconectar: {e}")


    async def shutdown(self):
        """
        Desliga o servidor/cliente gracefully
        Fecha todas as conexões e aguarda tasks terminarem
        """
        print("[Telemetry] Iniciando shutdown...")
        self.shutdown_flag = True

        if self.mode == 'server':
            # Para de aceitar novas conexões
            if self.server:
                self.server.close()
                await self.server.wait_closed()

            # Desconecta todos os clientes
            for addr in list(self.active_clients.keys()):
                await self._remove_client(addr)

            # Cancela tasks
            if self.timeout_checker_task:
                self.timeout_checker_task.cancel()
                try:
                    await self.timeout_checker_task
                except asyncio.CancelledError:
                    pass

            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass

        else:  # cliente
            await self.disconnect()

        print("[Telemetry] Shutdown completo")
