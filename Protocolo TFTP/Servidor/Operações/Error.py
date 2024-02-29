class Error():
    def __init__(self):
        """ Método construtor da classe Error
        """

        self.__op = 5
        


    def monta_cabecalho(self, errorCode):
        """ Monta o cabeçalho do ERROR

        Returns:
            bytearray: Cabeçalho da operação
        """
        
        """
            2 bytes |  2 bytes  | string | 1 byte   
            Opcode  | ErrorCode | ErrMsg |   0  
        
        """

        codigos_erro = {
            0 : 'Not defined, see error message (if any)',
            1 : 'File not found',
            2 : 'Access violation',
            3 : 'Disk full or allocation exceeded',
            4 : 'Illegal TFTP operation',
            5 : 'Unknown transfer ID',
            6 : 'File already exists',
            7 : 'No such user'
        }

        if errorCode in codigos_erro:
            self.__errorCode = errorCode
            self.__errMsg = codigos_erro[errorCode].encode('utf-8')
        else:
            raise Exception('Código de erro inválido')

        cabecalho = bytearray()

        cabecalho.append(0)
        cabecalho.append(self.__op)

        cabecalho.append(0)
        cabecalho.append(self.__errorCode)

        cabecalho += self.__errMsg

        cabecalho.append(0)
        
        return cabecalho
    

    
    def retorna_erro(self):
        """ retorna a msg de erro """
        return self.__errorCode, self.__errMsg
    


    def get_opcode(self):
        return self.__op