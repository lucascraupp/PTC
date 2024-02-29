class RrqWrq:
    def desmembra_cabecalho(self, cabecalho):
        """Abre o cabeçalho do RRQ ou do WRQ

        Args:
            cabecalho (bytearray): Cabeçalho da operação

        Raises:
            Exception: Opcode inválido
            Exception: Modo de arquivo inválido
        """

        """
            2 bytes | string   | 1 byte | string | 1 byte
            Opcode  | Filename |    0   |  Mode  |   0
        """

        op = int.from_bytes(cabecalho[:2], byteorder="big")

        if op == 1 or op == 2:
            self.__op = op
        else:
            self.__op = None

        file_pos = cabecalho.rindex(0, -len(cabecalho), -1)

        self.__filename = cabecalho[2:file_pos].decode("utf-8")

        mode = cabecalho[file_pos + 1 : -1].decode("utf-8")

        if (
            mode.lower() != "netascii"
            and mode.lower() != "octet"
            and mode.lower() != "mail"
        ):
            self.__op = None

    def get_opcode(self):
        return self.__op

    def get_filename(self):
        return self.__filename
