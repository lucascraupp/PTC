class Data:
    def __init__(self, block=1, data=bytearray):
        """Método Construtor da classe Data

        Args:
            block (int): Identificador do cabeçalho
            data (bytes): Informação transmitida

        Raises:
            Exception: Block com valor inválido
        """

        self.__op = 3

        if block >= 1:
            self.__block = block.to_bytes(2, "big")
        else:
            raise Exception("O bloco deve começar com o valor 1")

        self.__data = data

    def get_block(self):
        return self.__block

    def get_opcode(self):
        return self.__op

    def get_data(self):
        return self.__data

    def desmembra_cabecalho(self, cabecalho):
        """Obtém o número do bloco e os dados dele

        Args:
            cabecalho (bytearray): Cabeçalho da operação
        """

        self.__block = int.from_bytes(cabecalho[2:4], byteorder="big")

        self.__data = cabecalho[4:]

    def monta_cabecalho(self):
        """Monta o cabeçalho do DATA

        Returns:
            bytearray: Cabeçalho da operação
        """

        """
            2 bytes | 2 bytes | n bytes
            Opcode  | Block # |  Data
        """

        cabecalho = bytearray()

        cabecalho.append(0)  # O opcode precisa ter 2 bytes, então acrecenta-se o 0
        cabecalho.append(self.__op)

        cabecalho += self.__block

        cabecalho += self.__data

        return cabecalho
