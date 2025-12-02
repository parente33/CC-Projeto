import socket
from .MissionHeader import MissionHeader
import time
import asyncio


class MissionLink_Client:
    MSS = 1448                          # 1500-20(IPv4 forçado no CORE sem options) - 8(Header UDP sem padding) - 24(MissionHeader)
    HANDSHAKE_TIMEOUT = 5

    def __init__(self, host, port = 50000):
        self.host         =   host                                            # Server's adress
        self.port         = port                                              # Server's dock
        self.max_tries    = 5                                                 # Max tries to timeout
        self.RTT          = 0                                                 # Roud-Trip Time
        self.RTO          = self.HANDSHAKE_TIMEOUT                            # Retransmission Time
        self.socket       = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Client's socket
        self.seq_number   = 0                                                 # Sequence Number
        self.req_number   = 0                                                 # Request number (Similar ao seq number)
        self.waiting      = None                                              # Message waiting for answer
        self.answer       = None                                              # (header, payload) server's answer
        self.event        = asyncio.Event()                                   # Event to wake up coroutines
        self.receive_task = None                                              # Task to receive messages
        self.socket.setblocking(False)                                        # Non-blocking socket



    def set_RTT(self,new : float) :
        """
        Set RTT and update RTO value

        Arg :
        new (float) : RTT's new value
        """
        self.RTT = new
        self.RTO = new + 0.5*new



    async def receiver(self):
        """
        Loop to receive messages from server
        """
        loop = asyncio.get_event_loop()

        while True:
            data, addr =  await loop.sock_recvfrom(self.socket, MissionHeader.size + MissionLink_Client.MSS)
            header = MissionHeader.unpack(data[:MissionHeader.size])
            payload = data[MissionHeader.size:]

            if self.waiting is not None:
                is_data_match = (
                    header.type == MissionHeader.TYPE_DATA
                    and MissionHeader.TYPE_DATA + header.req_number == self.waiting
                )

                is_ack_match = (header.type + header.ack_number == self.waiting)

                if is_data_match or is_ack_match:
                    self.answer = (header, payload)
                    self.waiting = None
                    self.event.set()


    async def wait_acks(self,seq:bytes, header : MissionHeader, payload : bytes, is_handshake = 0):
        """
        Waits for server's acks and retransmit message

        Args :
        seq     (bytes)         : Bytes to identify the right answer (type+seq_number)
        header  (MissionHeader) : Message's header
        payload (bytes)         : Message's payload

        Return :

        (MissionHeader, Bytes): Server's answer
        None                  : Timeout Exceeded
        """

        self.waiting = seq
        self.answer = None
        self.event.clear()

        tries = 0
        timeout = self.RTO
        start = time.time()

        while self.waiting is not None:
            try:
                await asyncio.wait_for(self.event.wait(), timeout)

            except asyncio.TimeoutError:
                tries += 1
                if tries > self.max_tries:
                    self.waiting = None
                    return None

                header.retr = MissionHeader.RETR                    # Set flag retransmit in message's header
                message = header.pack() + (payload if payload is not None else b'')
                self.socket.sendto(message, (self.host, self.port)) # Retransmit message
                timeout += timeout*2**tries
                continue
        #Received the rigth answer
        end = time.time()

        ans_header,ans_payload = self.answer

        if ans_header.retr == MissionHeader.DEF and is_handshake == 0:
            self.set_RTT(end-start)

        return (ans_header,ans_payload)

    async def wait_data(self,req : bytes) :
        """
        Waits for server's Data

        Arg :

        req (bytes) : Type expected + Request number

        Return :

        (MissionHeader, Bytes): Server's answer
        None                  : Timeout Exceeded

        """

        self.waiting = req
        self.answer = None
        self.event.clear()

        tries = 0
        timeout = self.RTO

        while self.waiting is not None:
            try:
                await asyncio.wait_for(self.event.wait(), timeout)
            except asyncio.TimeoutError:
                tries += 1
                if tries > self.max_tries:
                    self.waiting = None
                    return None
                timeout += timeout*2**tries
                continue
        # Recebeu a resposta correta

        ans_header,ans_payload = self.answer
        return (ans_header, ans_payload)

    async def handle_handshake(self):
        """

        Handle a 3 way Handshake with server
        Sets connection_ID

        """
        seq = self.seq_number
        syn_header = MissionHeader(
            seq_number=seq,
            type=MissionHeader.TYPE_SYN
        )
        self.receive_task = asyncio.create_task(self.receiver())

        self.socket.sendto(syn_header.pack(),(self.host,self.port))
        self.seq_number += 1
        result = await self.wait_acks(MissionHeader.TYPE_SYNACK + seq, syn_header, None,is_handshake=1)

        if result is None:
            raise RuntimeError("Handshake failed: no SYNACK received")

        synack_header, synack_payload = result
        self.connection_ID = synack_header.connection_ID

        ack_header = MissionHeader(
            connection_ID=self.connection_ID,
            ack_number=synack_header.seq_number,
            type=MissionHeader.TYPE_ACK
        )

        self.socket.sendto(ack_header.pack(), (self.host, self.port))

        return True

    async def send_message(self, payload: bytes):
        """
        Sends message to Server

        Args :

        payload (bytes) : Client's data

        Return :

        True : Success
        """

        await self.handle_handshake()

        seq = self.seq_number
        self.seq_number = seq + 1  # incrementa seq para próximas mensagens

        msg_header = MissionHeader(
            connection_ID = self.connection_ID,
            seq_number=seq,
            length=len(payload),
            type = MissionHeader.TYPE_DATA
        )
        message = msg_header.pack() + payload
        self.socket.sendto(message,(self.host,self.port))
        result = await self.wait_acks(MissionHeader.TYPE_ACK + seq, msg_header, payload)
        if result is None:
            raise RuntimeError(f"Message seq={seq} failed (timeout)")
        #TERMINAR A RELAÇAO COM FYN

        await self.end_interact()
        return True

    async def send_request (self,payload) : # Aqui tem de vir payload para futuro se tivermos requests de varios tipos
        """
        Send Server a request for Data

        Args :

        payload (bytes) : Information for the request (Not this layer concern)

        Return :

        True : Success

        """
        await self.handle_handshake()
        seq = self.seq_number
        req = self.req_number
        self.seq_number = seq + 1  # incrementa seq para próximas mensagens
        self.req_number = req + 1

        msg_header = MissionHeader(
            connection_ID = self.connection_ID,
            seq_number =seq,
            length = len(payload),
            type = MissionHeader.TYPE_REQ,
            req_number = req
        )
        message = msg_header.pack() + payload
        self.socket.sendto(message,(self.host,self.port))
        result = await self.wait_acks(MissionHeader.TYPE_ACK + seq, msg_header, payload)
        if result is None:
            raise RuntimeError(f"Message seq={seq} failed (timeout)")

        result =  await self.wait_data(MissionHeader.TYPE_DATA + req)
        if result is None:
            raise RuntimeError(f"Message seq={seq} failed (timeout)")
        ans_header, ans_payload = result
        ack_number = ans_header.seq_number

        ack_header = MissionHeader(
            connection_ID = self.connection_ID,
            type = MissionHeader.TYPE_ACK,
            ack_number = ack_number
        )
        self.socket.sendto(ack_header.pack() , (self.host,self.port))
        await self.end_interact()
        return ans_payload

    async def end_interact(self) :
        """
        End Client's interation with server

        """
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

    async def kill_client(self) :
        self.socket.close()
