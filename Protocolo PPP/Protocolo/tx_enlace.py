#!/usr/bin/env python3

import sys

from pypoller import poller
from serial import Serial
from src.crc import CRC16
import time

class TxEnlace(poller.Callback):
    def __init__(self, serial_port, message, timeout):
        self.__flag = 0x7E           # ~
        self.__esc = 0x7D            # }
        self.__control = 0b00000000  # Quadro tipo DATA e não sequência do anterior
        self.__reserved = 0b00000000
        self.__id_proto = 0b00000001
        self.__fcs_lsb = 0b00100000
        self.__fcs_msb = 0b00010000
        self.__byte_list = []
        self.__data_list = []
        self.__ack_list = []
        self.__state = self.__send_frame
        self.__byteAmount = 0
        self.__message_length = len(message)

        self.__ack_message = [
            self.__flag,
            self.__control ^ 0b10000000,
            self.__reserved,
            self.__fcs_lsb,
            self.__fcs_msb,
            self.__flag,
        ]

        self.__timeout = timeout
        self.__general_timeout = 1

        self.__message = message
        self.__message_index = 0

        self.__serial = Serial(serial_port, 9600)

        poller.Callback.__init__(self, self.__serial, self.__timeout)
        
        self.process_message()

    def __send_frame(self, byte_list):
        for byte in byte_list:
            sys.stdout.write(chr(byte))
            sys.stdout.flush()
            msg = bytes([byte])
            self.__serial.write(msg)
            # time.sleep(0.03) # Descomente para teste em hardware

        print("\n")
        self.__state = self.__wait_ack

    def __wait_ack(self, byte):
        self.__ack_list.append(byte)
        if len(self.__ack_list) == 6 and self.__ack_list == self.__ack_message:
            self.__state = self.__send_frame
            self.__ack_list = []

            if self.__control == 0b00000000:
                sys.exit(0)

            self.process_message()

    def process_message(self):
        self.__data_list = [] 
        self.__byte_list = []

        # Verificar se é o último trecho
        if self.__message_length - self.__message_index > 1024:
            self.__control = 0b00001000
        else:
            self.__control = 0b00000000

        self.__data_list.append(self.__control)
        self.__data_list.append(self.__reserved)
        self.__data_list.append(self.__id_proto)

        self.__byte_list.append(self.__flag)
        self.__byte_list.append(self.__control)
        self.__byte_list.append(self.__reserved)
        self.__byte_list.append(self.__id_proto)

        while self.__message_index < len(self.__message):
            byte = ord(self.__message[self.__message_index])

            if self.__byteAmount == 1024:
                self.__byteAmount = 0
                break
            else:
                if byte == self.__flag:
                    self.__byte_list.append(self.__esc)
                    self.__byte_list.append(byte ^ 0x20)
                    self.__byteAmount += 2
                elif byte == self.__esc:
                    self.__byte_list.append(self.__esc)
                    self.__byte_list.append(byte ^ 0x20)
                    self.__byteAmount += 2
                else:
                    self.__byte_list.append(byte)
                    self.__byteAmount += 1

                self.__message_index += 1
                self.__data_list.append(byte)

        fcs = CRC16(bytes(self.__data_list))
        msg_crc = fcs.gen_crc()
        self.__byte_list.append(msg_crc[-2])
        self.__byte_list.append(msg_crc[-1])
        self.__byte_list.append(self.__flag)

        self.__state(self.__byte_list)

    def handle(self):
        byte = self.__serial.read(1)

        self.__general_timeout = 1

        self.__state(byte[0])

    def handle_timeout(self):
        print("Timeout", self.__general_timeout)
        if self.__general_timeout == 3:
            print("Timeout máximo atingido. Saindo...")
            sys.exit(1)
        else:
            print("Reenviando quadro...")
            self.__general_timeout += 1
            self.reload_timeout()
            self.__send_frame(self.__byte_list)


serial_port = sys.argv[1]

message = input("Digite uma mensagem: ")

callback = TxEnlace(serial_port, message, 5)  # instancia um callback
sched = poller.Poller()                       # cria o poller (event loop)
sched.adiciona(callback)                      # registra o callback no poller
sched.despache()                              # entrega o controle pro loop de eventos