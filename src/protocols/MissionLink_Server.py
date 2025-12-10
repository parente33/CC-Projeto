import socket
import asyncio
import secrets
from .MissionHeader import MissionHeader
import time

class MissionLink_Server :

    MSS = 1448  # 1500-20(IPv4 forcado no CORE sem options) - 8(Header UDP sem padding) - 21(MissionHeader)
    HANDSHAKE_TIMEOUT = 1
    MAX_TRIES = 5

    async def start(self) :
        """
        Starts the server's receiver and sender tasks
        """
        self.receive_task = asyncio.create_task(self.receiver())
        self.send_task = asyncio.create_task(self.sender())
        await asyncio.gather(self.receive_task, self.send_task)

    def __init__(self, host = 'localhost', port = 50000, callback_data = None, callback_request = None):
        """
        Initialize the MissionLink Server

        Args:
        host (str)              : Server's address
        port (int)              : Server's dock
        callback_data (callable): Function to handle received DATA messages
        callback_request (callable): Function to handle REQ messages and return response
        """
        self.connections_id             = {}                                                # Dict {connection_ID: (addr, rtt)}
        self.seq_number                 = 0                                                 # Sequence Number
        self.pending                    = {}                                                # Dict {(connection_ID, seq): 'Pending' or (header, payload)}
        self.pending_events             = {}                                                # Dict {(connection_ID, seq): Event}
        self.send_queue                 = asyncio.Queue()                                   # Queue of messages to send
        self.receive_task               = None                                              # Receiver task
        self.send_task                  = None                                              # Sender task
        self.socket                     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Server's socket
        self.socket.bind((host,port))
        self.socket.setblocking(False)                                                      # Non-blocking socket
        self.max_tries                  = self.MAX_TRIES                                    # Max tries to timeout
        self.callback_data              = callback_data                                     # Callback for DATA messages
        self.callback_request           = callback_request                                  # Callback for REQ messages
        self.shutdown_flag              = False                                             # Shutdown flag

    async def wait_acks(self, connection_ID : int, seq:bytes, header : MissionHeader, payload : bytes):
        """
        Waits for client's acks and retransmit message

        Args:
        connection_ID (int)     : Connection identifier
        seq     (bytes)         : Bytes to identify the right answer (type+seq_number)
        header  (MissionHeader) : Message's header
        payload (bytes)         : Message's payload

        Return:
        (MissionHeader, Bytes): Client's answer
        None                  : Timeout Exceeded
        """
        key = (connection_ID, seq)
        event = asyncio.Event()
        self.pending_events[key] = event
        self.pending[key] = 'Pending'

        tries = 0
        addr, rtt = self.connections_id[connection_ID]
        timeout = (rtt if rtt != 0 else self.HANDSHAKE_TIMEOUT)
        start = time.time()

        while self.pending.get(key, None) == 'Pending':
            try:
                await asyncio.wait_for(event.wait(), timeout)

            except asyncio.TimeoutError:
                tries += 1
                if tries > self.max_tries:
                    self.pending.pop(key, None)
                    self.pending_events.pop(key, None)
                    return None

                header.retr = MissionHeader.RETR                    # Set flag retransmit in message's header
                packet = header.pack() + payload
                self.socket.sendto(packet, addr)                    # Retransmit message
                timeout += timeout * 2 ** tries
                event.clear()                                       # Clear event before retry
                continue

        # Received the right answer
        end = time.time()
        ans_header, ans_payload = self.pending.pop(key)
        self.pending_events.pop(key, None)

        # Update RTT only if NOT a retransmission
        if ans_header.retr == MissionHeader.DEF:
            rtt = end - start
            self.connections_id[connection_ID] = (addr, rtt)

        return (ans_header, ans_payload)


    async def sender(self):
        """
        Loop to send messages to clients from the send queue
        """
        while not self.shutdown_flag:
                try:
                    (header, payload) = await asyncio.wait_for(self.send_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue

                connection_ID = header.connection_ID
                seq = MissionHeader.TYPE_ACK + header.seq_number
                if self.connections_id.get(connection_ID, None) is None :
                    continue
                addr, rtt = self.connections_id[connection_ID]
                packet = header.pack() + (payload if payload is not None else b'')
                self.socket.sendto(packet, addr)
                # Only wait for ACKs on DATA messages
                if header.type == MissionHeader.TYPE_DATA :
                    asyncio.create_task(self.wait_acks(connection_ID, seq, header, payload))

    def genereate_conID(self):
        """
        Generate a unique connection ID

        Return:
        int: Unique connection ID
        """
        for _ in range(1000):
            conn_id = secrets.randbelow(2**32)

            if conn_id not in self.connections_id:
                return conn_id

    async def handle_answer(self, header, payload, addr):
        """
        Handle incoming messages from clients

        Args:
        header  (MissionHeader) : Received message's header
        payload (bytes)         : Received message's payload
        addr    (tuple)         : Client's address (host, port)
        """
        type = header.type
        connection_ID = header.connection_ID
        seq_number = header.seq_number
        ack_number = header.ack_number

        if type == MissionHeader.TYPE_ACK :
            # Handle ACK messages
            key = (connection_ID, type + ack_number)
            if self.pending.get(key, None) == 'Pending':
                self.pending[key] = (header, payload)
                event = self.pending_events.get(key)
                if event:
                    event.set()
                return

        elif type == MissionHeader.TYPE_SYN :
            # Handle SYN messages (handshake initialization)
            if self.connections_id.get(connection_ID, None) is None :
                connection_ID = self.genereate_conID()
            self.connections_id[connection_ID] = (addr, 0)
            answer = MissionHeader(
                    connection_ID = connection_ID,
                    type = MissionHeader.TYPE_SYNACK,
                    ack_number = seq_number
                    )
            await self.send_queue.put((answer, None))
            return

        elif type == MissionHeader.TYPE_DATA :
                # Handle DATA messages - call callback if provided
                if self.callback_data:
                    if asyncio.iscoroutinefunction(self.callback_data):
                        asyncio.create_task(self.callback_data(connection_ID, payload))
                    else:
                        self.callback_data(connection_ID, payload)

                answer = MissionHeader(connection_ID = connection_ID,
                                       type = MissionHeader.TYPE_ACK,
                                       ack_number = seq_number
                                       )

                await self.send_queue.put((answer, None))
                return

        elif type == MissionHeader.TYPE_REQ :
                # Handle REQ messages - send ACK then DATA response
                response_payload = b''
                ack = MissionHeader(connection_ID = connection_ID,
                                       type = MissionHeader.TYPE_ACK,
                                       ack_number = seq_number
                                       )
                await self.send_queue.put((ack, None))

                # Call callback to get response payload
                if self.callback_request:
                    if asyncio.iscoroutinefunction(self.callback_request):
                        response_payload = await self.callback_request(connection_ID, payload)
                    else:
                        response_payload = self.callback_request(connection_ID, payload)

                answer = MissionHeader(connection_ID = connection_ID,
                                       type = MissionHeader.TYPE_DATA,
                                       seq_number = self.seq_number,
                                       req_number = header.req_number
                                       )
                self.seq_number += 1
                await self.send_queue.put((answer, response_payload))
                return

    async def receiver(self) :
        """
        Loop to receive messages from clients
        """
        loop = asyncio.get_event_loop()
        while not self.shutdown_flag:
            try:
                data, addr = await asyncio.wait_for(
                    loop.sock_recvfrom(self.socket, MissionHeader.size + MissionLink_Server.MSS),
                    timeout=0.1
                )
                header = MissionHeader.unpack(data[:MissionHeader.size])
                payload = data[MissionHeader.size:]
                asyncio.create_task(self.handle_answer(header, payload, addr))
            except asyncio.TimeoutError:
                continue

    async def end(self):
        """
        Gracefully end the server after all pending messages are sent and acknowledged
        """
        print("Waiting for pending operations to complete...")

        # Wait until no pending ACKs and send queue is empty
        while True:
            has_pending = any(value == 'Pending' for value in self.pending.values())
            queue_empty = self.send_queue.empty()

            if not has_pending and queue_empty:
                break


        print("All operations complete. Shutting down...")
        self.shutdown_flag = True

        if self.receive_task:
            self.receive_task.cancel()
        if self.send_task:
            self.send_task.cancel()
        try:
            await asyncio.gather(self.receive_task, self.send_task, return_exceptions=True)
        except Exception:
            pass
        self.socket.close()
        print("Server ended successfully")
