class Ack():
    def __init__(self, block=1):
        """ Método construtor da classe Ack

        Args:
            block (int): Identificador do cabeçalho

        Raises:
            Exception: BLOCK inválido
        """
        self.__op = 4
        
        if block >= 0:
            self.__block = block.to_bytes(2, 'big')
        else:
            raise Exception('Bloco inválido')
        
    def get_opcode(self):
        return self.__op

    def monta_cabecalho(self):
        """ Monta o cabeçalho do ACK

        Returns:
            bytearray: Cabeçalho da operação
        """

        """
            2 bytes | 2 bytes
             Opcode | Block #
        """

        cabecalho = bytearray()
        
        cabecalho.append(0)
        cabecalho.append(self.__op)

        cabecalho += self.__block

        return cabecalho
    
    def desmembra_cabecalho(self,cabecalho):
        self.__block = int.from_bytes(cabecalho[2:4], byteorder='big')

    def get_block(self):
        return self.__block
