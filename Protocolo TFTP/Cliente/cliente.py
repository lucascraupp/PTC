import os
import socket
import sys

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"


import tftp_protobuf_pb2 as proto
from Operações.Ack import Ack
from Operações.Data import Data
from Operações.Error import Error
from Operações.RrqWrq import RrqWrq
from pypoller import poller


class Cliente(poller.Callback):
    def __init__(self, ip, porta, operacao, nomeArq, novoNome):
        """Método construtor da classe Cliente

        Args:
            ip (str): Endereço IP do Servidor
            porta (int): Porta do Servidor
        """

        self.__ip = ip
        self.__timeoutGeral = 1

        try:
            self.__porta = int(porta)
        except Exception:
            raise Exception("Porta inválida!")

        self.__operacao = operacao
        self.__nomeArq = nomeArq
        self.__modo = "NetAscii"
        self.__novoNome = novoNome
        self.__timeout = 10
        self.__tratador = self.handle_PADRAO

        self.__socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM  # Internet
        )  # UDP

        poller.Callback.__init__(self, self.__socket, self.__timeout)

        self.__estado = self.handle_INICIO
        self.__estado()

    def rrq(self):
        """Inicia o fluxo de leitura do cliente"""

        mensagem = RrqWrq(op=1, file=self.__nomeArq, mode=self.__modo).monta_cabecalho()

        self.__n = 1

        # Envia a requisição para o sistema
        self.__socket.sendto(mensagem, (self.__ip, self.__porta))

        # Instancia Poller
        self.enable()
        self.enable_timeout()
        pol = poller.Poller()

        # Despache
        self.__estado = self.handle_LEITURA
        pol.adiciona(self)
        pol.despache()

    def wrq(self):
        """Inicia o fluxo de escrita do cliente"""

        # self.__n = 0

        # Envia a requisição para o sistema
        # self.__socket.sendto(mensagem, (self.__ip, self.__porta))

        mensagem = RrqWrq(op=2, file=self.__nomeArq, mode=self.__modo).monta_cabecalho()
        self.__socket.sendto(mensagem, (self.__ip, self.__porta))
        self.__n = 0

        # Instancia Poller
        self.enable()
        self.enable_timeout()
        pol = poller.Poller()

        # Despache
        self.__estado = self.handle_ESCRITA
        pol.adiciona(self)
        pol.despache()

    def handle_LEITURA(self, data=None):
        if data is None:
            mensagem = RrqWrq(
                op=1, file=self.__nomeArq, mode=self.__modo
            ).monta_cabecalho()
            self.__socket.sendto(mensagem, (self.__ip, self.__porta))
        else:
            # Cria o arquivo para escrita de bytes
            self.__arq = open(self.__nomeArq, "wb")

            self.__estado = self.handle_RECEBENDO

            self.__estado(data)

    def handle_RECEBENDO(self, data=None):
        if data is None:
            ack = Ack(block=(self.__n - 1))
        else:
            ack = Ack(block=self.__n)

            self.__arq.write(data.get_data())

            # Ainda há bytes a receber
            if len(data.get_data()) == 512:
                self.__n += 1

            # Se não houver mais mensagens, encerra a conexão
            else:
                self.__estado = self.handle_FIM
                self.__estado(ack)

        cabecalho = ack.monta_cabecalho()

        self.__socket.sendto(cabecalho, (self.__ip, self.__porta))

    def handle_ESCRITA(self, ack=None):
        # Se não receber o ACK (Timeout), reenvia o Wrq
        if ack is None:
            mensagem = RrqWrq(
                op=2, file=self.__nomeArq, mode=self.__modo
            ).monta_cabecalho()
            self.__socket.sendto(mensagem, (self.__ip, self.__porta))
        else:
            try:
                self.__arq = open(self.__nomeArq, "rb")
            except Exception:
                raise Exception("Arquivo inexistente")

            self.__estado = self.handle_TRANSMITINDO
            self.__estado(ack)

    def handle_TRANSMITINDO(self, ack=None):
        bloco = ack.get_block()
        tamanho = 512
        leitura = self.__arq.read(tamanho)
        data = Data(self.__n + 1, leitura)
        dados = data.monta_cabecalho()

        # Verifica se recebeu o Ack correto, se sim envia Data
        if bloco == self.__n:
            self.__n += 1
            self.__socket.sendto(dados, (self.__ip, self.__porta))
            self.__ultimo_dado = dados
            if len(data.get_data()) < 512:
                self.__estado = self.handle_ULTIMO_TX
        # Se receber o Ack do penúltimo Data ou der Timeout, reenvia ultimo Data
        elif bloco == self.__n - 1 | ack is None:
            self.socket.sendto(self.__ultimo_dado, (self.__ip, self.__porta))

    def handle_ULTIMO_TX(self, mensagem=None):
        if mensagem is None:
            self.__socket.sendto(self.__ultimo_dado, (self.__ip, self.__porta))
        elif mensagem.get_opcode() == 4 or mensagem.get_opcode() == 5:
            self.__estado = self.handle_FIM
            self.__estado(None)

    def handle_FIM(self, mensagem=None):
        if mensagem is not None:
            # Se for um fluxo de recepção, envia um ACK final e encerra
            if mensagem.get_opcode() == 4:
                self.__socket.sendto(
                    mensagem.monta_cabecalho(), (self.__ip, self.__porta)
                )
                self.__arq.close()

            # Se receber uma mensagem de erro, printa ela e encerra
            elif mensagem.get_opcode() == 5:
                errorCode, errMsg = mensagem.retorna_erro()

                print(f"Erro {errorCode} - {errMsg}")

        sys.exit(0)

    def list(self):
        mensagem = proto.Mensagem()
        mensagem.list.path = self.__nomeArq

        # Envia a requisição para o sistema
        self.__socket.sendto(mensagem.SerializeToString(), (self.__ip, self.__porta))

        if self.__timeoutGeral == 1:
            # Instancia Poller
            self.enable()
            self.enable_timeout()
            pol = poller.Poller()

            # Despache
            pol.adiciona(self)
            pol.despache()

    def mkdir(self):
        mensagem = proto.Mensagem()
        mensagem.mkdir.path = self.__nomeArq

        # Envia a requisição para o sistema
        self.__socket.sendto(mensagem.SerializeToString(), (self.__ip, self.__porta))

        if self.__timeoutGeral == 1:
            # Instancia Poller
            self.enable()
            self.enable_timeout()
            pol = poller.Poller()

            # Despache
            pol.adiciona(self)
            pol.despache()

    def move(self):
        mensagem = proto.Mensagem()
        mensagem.move.nome_orig = self.__nomeArq

        if self.__novoNome is not None:
            mensagem.move.nome_novo = self.__novoNome

        # Envia a requisição para o sistema
        self.__socket.sendto(mensagem.SerializeToString(), (self.__ip, self.__porta))

        if self.__timeoutGeral == 1:
            # Instancia Poller
            self.enable()
            self.enable_timeout()
            pol = poller.Poller()

            # Despache
            pol.adiciona(self)
            pol.despache()

    def handle_NOVO(self, mensagem):
        msgRecebida = proto.Mensagem()
        msgRecebida.ParseFromString(mensagem)

        if msgRecebida.HasField("list_resp"):
            print(msgRecebida)
        elif msgRecebida.HasField("ack"):
            print("Operação realizada com sucesso!")
        elif msgRecebida.HasField("error"):
            print(msgRecebida.error)

        self.__estado = self.handle_FIM
        self.__estado(None)

    def handle_PADRAO(self, mensagem):
        match mensagem[1]:
            # Opcode do Data
            case 3:
                msg = Data()
                msg.desmembra_cabecalho(mensagem)

            # Opcode do ACK
            case 4:
                msg = Ack()
                msg.desmembra_cabecalho(mensagem)

            # Opcode do Error
            case 5:
                msg = Error()
                msg.desmembra_cabecalho(mensagem)
                self.__estado = self.handle_FIM

        self.__estado(msg)

    def handle_INICIO(self):
        match self.__operacao:
            case "rrq":
                self.rrq()

            case "wrq":
                self.wrq()

            case "list":
                self.__tratador = self.handle_NOVO
                self.list()

            case "mkdir":
                self.__tratador = self.handle_NOVO
                self.mkdir()

            case "move":
                self.__tratador = self.handle_NOVO
                self.move()

            case _:
                print("Comando inválido")
                sys.exit(1)  # Código se encerra com erro

    def handle(self):
        mensagem, (_, self.__porta) = self.__socket.recvfrom(
            516
        )  # 512 data bytes + 2 opcode bytes + 2 block bytes

        self.__timeoutGeral = 1

        self.__tratador(mensagem)

    def handle_timeout(self):
        if self.__timeoutGeral == 3:
            print("Programa encerrado devido a múltimos Timeouts")
            self.__estado = self.handle_FIM
        else:
            print("Timeout")
            self.__timeoutGeral += 1
            self.reload_timeout()

        self.__estado()


if len(sys.argv) == 5:
    ip = sys.argv[1]
    porta = sys.argv[2]
    operacao = sys.argv[3]
    arquivo = sys.argv[4]
    novo_nome = None
elif len(sys.argv) == 6:
    ip = sys.argv[1]
    porta = sys.argv[2]
    operacao = sys.argv[3]
    arquivo = sys.argv[4]
    novo_nome = sys.argv[5]
else:
    raise Exception("Número de argumentos inválido!")

cliente = Cliente(ip, porta, operacao, arquivo, novo_nome)
