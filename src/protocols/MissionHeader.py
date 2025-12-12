import struct

class MissionHeader:
    size = 16  #tamanho do header A DEFINIR
    # Definir typess como constantes
    TYPE_ACK    = 0b00000001
    TYPE_SYN    = 0b00000010
    TYPE_SYNACK = 0b00000100
    TYPE_REQ    = 0b00010000 #So do lado do servidor
    TYPE_DATA   = 0b00100000

    #Flag Retransmissao

    RETR = 0b00000001  # RETRANSMITIDO
    DEF  = 0b00000000  #DEFAULT

    def __init__(self, connection_ID = 0, seq_number = 0, ack_number = 0, type = TYPE_DATA,retr = DEF, req_number = 0):
        self.connection_ID  = connection_ID                   # 4 bytes
        self.seq_number     = seq_number                      # 4 bytes
        self.ack_number     = ack_number                      # 4 bytes
        self.type           = type                            # 1 byte
        self.retr           = retr                            # 1 byte
        self.req_number     = req_number                      # 2 bytes

    def pack(self):
        """
        Converte os campos do header em bytes prontos para enviar via socket.
        """
        return struct.pack('!IIIBBH',
                           self.connection_ID,
                           self.seq_number,
                           self.ack_number,
                           self.type,
                           self.retr,
                           self.req_number
                           )

    @staticmethod
    def unpack(data):
        """
        Recebe bytes e reconstrói o header original.
        """
        connection_ID,seq_number,ack_number,flags,retr, req_number = struct.unpack('!IIIBBH', data)
        return MissionHeader(connection_ID, seq_number, ack_number,  flags,retr, req_number)


