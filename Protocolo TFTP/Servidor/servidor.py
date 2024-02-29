import os.path
import socket
import sys

from Operações.Ack import Ack
from Operações.Data import Data
from Operações.Error import Error
from Operações.RrqWrq import RrqWrq
from pypoller import poller

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import tftp_protobuf_pb2 as proto


class Servidor(poller.Callback):
    def __init__(self, diretorio, porta):
        self.__diretorio = diretorio
        self.__ip = "127.0.0.1"

        if isinstance(porta, int):
            self.__porta = porta
        else:
            raise Exception("A porta precisa ser um inteiro!")

        self.__n = 1
        self.__timeout = 10
        self.__timeoutGeral = 1

        self.__socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM  # Internet
        )  # UDP

        self.__socket.bind((self.__ip, self.__porta))

        poller.Callback.__init__(self, self.__socket, self.__timeout)

        # Instancia Poller
        self.enable()
        self.enable_timeout()
        pol = poller.Poller()

        # Despache
        self.__estado = self.handle_ESPERA
        pol.adiciona(self)
        pol.despache()

    def handle_ULTIMO_TX(self, mensagem=None):
        if mensagem is None:
            # Reenvia o bloco anterior
            self.__arquivo.seek((self.__n - 1) * 512)
            dados = Data(self.__n - 1, self.__arquivo.read(512))
            msg = dados.monta_cabecalho()
            self.__socket.sendto(msg, (self.__ip_clinte, self.__porta_cliente))
        else:
            if mensagem.get_opcode() == 3:
                msg = mensagem.monta_cabecalho()
                self.__socket.sendto(msg, (self.__ip_clinte, self.__porta_cliente))
                self.__estado = self.handle_ESPERA
            else:
                self.__n = 1
                self.__estado = self.handle_ESPERA

    def handle_TRANSMITINDO(self, mensagem=None):
        if mensagem is None:
            # Reenvia o bloco anterior
            self.__arquivo.seek((self.__n - 2) * 512)
            data = Data(self.__n - 1, self.__arquivo.read(512))
            msg = data.monta_cabecalho()
            self.__socket.sendto(msg, (self.__ip_clinte, self.__porta_cliente))
        else:
            # Lê o bloco de dados, de acordo com o valor de n
            self.__arquivo.seek((self.__n - 1) * 512)
            data = Data(self.__n, self.__arquivo.read(512))
            msg = data.monta_cabecalho()

            if len(data.get_data()) < 512:
                self.__estado = self.handle_ULTIMO_TX
                self.__estado(data)
            else:
                self.__socket.sendto(msg, (self.__ip_clinte, self.__porta_cliente))
                self.__n += 1

    def handle_RECEBENDO(self, mensagem=None):
        if mensagem is None:
            ack = Ack(self.__n)
            self.__socket.sendto(
                ack.monta_cabecalho(), (self.__ip_clinte, self.__porta_cliente)
            )
            return
        else:
            if mensagem[1] == 3:
                dados = Data()
                dados.desmembra_cabecalho(mensagem)
                if dados.get_block() == self.__n:
                    self.__arquivo.write(dados.get_data())
                    ack = Ack(self.__n)
                    self.__socket.sendto(
                        ack.monta_cabecalho(), (self.__ip_clinte, self.__porta_cliente)
                    )
                    self.__n += 1
                    if len(dados.get_data()) < 512:
                        self.__arquivo.close()
                        self.estado = self.handle_ESPERA
                else:
                    ack = Ack(self.__n - 1)
                    self.__socket.sendto(
                        ack.monta_cabecalho(), (self.__ip_clinte, self.__porta_cliente)
                    )
        return

    def handle_ESPERA(self, mensagem=None):
        if not mensagem is None:
            self.__n = 1
            self.__timeoutGeral = 1
            self.__porta = 6969

            match mensagem[1]:
                # Se for um RRQ
                case 1:
                    rrq = RrqWrq()
                    rrq.desmembra_cabecalho(mensagem)

                    if rrq.get_opcode() is None:
                        erro = Error()
                        self.__socket.sendto(
                            erro.monta_cabecalho(4),
                            (self.__ip_clinte, self.__porta_cliente),
                        )
                    else:
                        # Verifica se o arquivo existe
                        try:
                            self.__arquivo = open(
                                self.__diretorio + rrq.get_filename(), "rb"
                            )

                            self.__estado = self.handle_TRANSMITINDO
                            self.__estado(rrq)
                        except FileNotFoundError:
                            erro = Error()
                            self.__socket.sendto(
                                erro.monta_cabecalho(1),
                                (self.__ip_clinte, self.__porta_cliente),
                            )
                # Se for um WRQ
                case 2:
                    wrq = RrqWrq()
                    wrq.desmembra_cabecalho(mensagem)
                    arq_nome = self.__diretorio + wrq.get_filename()

                    # Se o arquivo existir, retorna um erro
                    if os.path.isfile(arq_nome):
                        erro = Error()
                        self.__socket.sendto(
                            erro.monta_cabecalho(6),
                            (self.__ip_clinte, self.__porta_cliente),
                        )
                    else:
                        # Envia Ack[0]
                        ack = Ack(0)
                        self.__socket.sendto(
                            ack.monta_cabecalho(),
                            (self.__ip_clinte, self.__porta_cliente),
                        )
                        # Abre arquivo para escrita
                        self.__arquivo = open(
                            self.__diretorio + wrq.get_filename(), "wb"
                        )
                        self.__estado = self.handle_RECEBENDO

                case _:
                    erro = Error()
                    self.__socket.sendto(
                        erro.monta_cabecalho(4),
                        (self.__ip_clinte, self.__porta_cliente),
                    )

    def handle_LIST(self):
        diretorio = self.__nova_mensagem

        if "../" in diretorio:
            msgCompleta = proto.Mensagem()

            msgCompleta.error.errorcode = 2
        elif os.path.isdir(diretorio):
            arquivos_e_pastas = os.listdir(diretorio)

            msgCompleta = proto.Mensagem()

            for item in arquivos_e_pastas:
                lista = proto.ListItem()
                caminho_completo = os.path.join(diretorio, item)

                if os.path.isfile(caminho_completo):
                    # É um arquivo
                    lista.file.nome = item
                    lista.file.tamanho = os.path.getsize(caminho_completo)

                elif os.path.isdir(caminho_completo):
                    lista.dir.path = item

                msgCompleta.list_resp.items.append(lista)
        else:
            msgCompleta = proto.Mensagem()

            msgCompleta.error.errorcode = 2

        self.__socket.sendto(
            msgCompleta.SerializeToString(),
            (self.__ip_clinte, self.__porta_cliente),
        )

    def handle_MKDIR(self):
        pasta = self.__nova_mensagem

        if os.path.exists(pasta):
            msg = proto.Mensagem()
            msg.error.errorcode = 6
        else:
            os.mkdir(pasta)

            msg = proto.Mensagem()
            msg.ack.block_n = 0

        self.__socket.sendto(
            msg.SerializeToString(),
            (self.__ip_clinte, self.__porta_cliente),
        )

    def handle_MOVE(self):
        nome_orig = self.__nova_mensagem.nome_orig

        if self.__nova_mensagem.HasField("nome_novo"):
            nome_novo = self.__nova_mensagem.nome_novo
        else:
            nome_novo = None

        msg = proto.Mensagem()

        if os.path.exists(nome_orig):
            if nome_novo is None:
                os.remove(nome_orig)
                msg.ack.block_n = 0
            elif os.path.exists(nome_novo):
                msg.error.errorcode = 6
            else:
                os.rename(nome_orig, nome_novo)

                msg.ack.block_n = 0
        else:
            msg.error.errorcode = 1

        self.__socket.sendto(
            msg.SerializeToString(),
            (self.__ip_clinte, self.__porta_cliente),
        )

    def handle(self):
        mensagem, (self.__ip_clinte, self.__porta_cliente) = self.__socket.recvfrom(
            516
        )  # 512 data bytes + 2 opcode bytes + 2 block bytes

        self.__timeoutGeral = 1

        try:
            msg = proto.Mensagem()
            msg.ParseFromString(mensagem)

            if msg.HasField("list"):
                self.__nova_mensagem = msg.list.path
                self.handle_LIST()
            elif msg.HasField("mkdir"):
                self.__nova_mensagem = msg.mkdir.path
                self.handle_MKDIR()
            elif msg.HasField("move"):
                self.__nova_mensagem = msg.move
                self.handle_MOVE()

        except:
            self.__estado(mensagem)

    def handle_timeout(self):
        if self.__timeoutGeral == 3:
            self.__estado = self.handle_ESPERA
        else:
            self.__timeoutGeral += 1
            self.reload_timeout()

        self.__estado()


try:
    caminho = sys.argv[1]
    porta = int(sys.argv[2])
except Exception:
    raise Exception("A porta precisa ser um inteiro!")

servidor = Servidor(caminho, porta)
