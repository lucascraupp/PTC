class RrqWrq():
    def __init__(self, op, file, mode):
        """ Método construtor da clase

        Args:
            op (int): OPCODE do RRQ (1) ou do WRQ (2)
            file (str): Nome do arquivo que será processado
            mode (str): Formato da codificação

        Raises:
            Exception: OPCODE inválido
            Exception: Formato da codificação inválido
        """

        if op == 1 or op == 2:
            self.__op = op
        else:
            raise Exception('OPCODE inválido')
        
        if mode.lower() == 'netascii' or mode.lower() == 'octet' or mode.lower() == 'mail':    
            self.__mode = mode.encode('utf-8')
        else:
            raise Exception('Modo informado não é uma opção válida')
        
        self.__file = file.encode('utf-8')
        
    def monta_cabecalho(self):
        """ Monta o cabeçalho do RRQ ou do WRQ

        Returns:
            bytearray: Cabeçalho da operação
        """

        """
            2 bytes | string   | 1 byte | string | 1 byte
            Opcode  | Filename |    0   |  Mode  |   0
        """

        cabecalho = bytearray()

        cabecalho.append(0) # O opcode precisa ter 2 bytes, então acrecenta-se o 0
        cabecalho.append(self.__op)

        cabecalho += self.__file

        cabecalho.append(0)

        cabecalho += self.__mode
        
        cabecalho.append(0)

        return cabecalho