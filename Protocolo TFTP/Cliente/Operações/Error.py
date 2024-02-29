class Error():
    def __init__(self):
        """ Método construtor da classe Error
        """

        self.__codigos_erro = [0, 1, 2, 3, 4, 5, 6, 7]

        self.__op = 5
        


    def desmembra_cabecalho(self, cabecalho):
        """ Abre o cabeçalho da classe Error

        Args:
            cabecalho (bytearry): Cabeçalho do error

        Raises:
            Exception: Código de erro inválido
        """

        """
            2 bytes |  2 bytes  | string | 1 byte   
            Opcode  | ErrorCode | ErrMsg |   0  
        """

        errorCode = int.from_bytes(cabecalho[2:4], byteorder='big')

        if errorCode in self.__codigos_erro:
            self.__errorCode = errorCode
            self.__errMsg = cabecalho[4:-1].decode('utf-8')
        else:
            raise Exception('Código de erro inválido')
    

    
    def retorna_erro(self):
        """ retorna a msg de erro """
        return self.__errorCode, self.__errMsg
    


    def get_opcode(self):
        return self.__op