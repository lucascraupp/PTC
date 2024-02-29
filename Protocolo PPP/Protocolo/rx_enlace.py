#!/usr/bin/env python3

import sys

from pypoller import poller
from serial import Serial
from src.crc import CRC16


class RxEnlace(poller.Callback):
    def __init__(self, serial_port):
        self.__flag = 0x7E  # ~
        self.__esc = 0x7D  # }
        self.__control = 0b10000000  # Quadro tipo ACK e não sequência do anterior
        self.__reserved = 0b00000000
        self.__fcs_lsb = 0b00100000
        self.__fcs_msb = 0b00010000
        self.__data_list = []
        self.__frame = []
        self.__state = self.__idle

        self.__timeout = 10
        self.__general_timeout = 1

        self.__serial = Serial(serial_port, 9600)
        poller.Callback.__init__(self, self.__serial, self.__timeout)

        # Instancia Poller
        self.enable()
        self.enable_timeout()
        pol = poller.Poller()

        # Despache
        pol.adiciona(self)
        pol.despache()

    def __idle(self, byte):
        self.__frame = []
        if byte == self.__flag:
            self.__state = self.__prep

    def __prep(self, byte):
        if byte == self.__esc:
            self.__state = self.__escape
        elif not (byte == self.__flag or byte == self.__esc):
            self.__state = self.__rx
            self.__frame.append(byte)

    def __break_header(self):
        data = bytes(self.__frame)[:-2]

        payload = bytes(self.__frame)

        fcs = CRC16(data)
        fcs.gen_crc()

        fcs.clear()
        fcs.update(payload)

        if fcs.check_crc():
            data = bytes(self.__frame)[3:-2]
            control = bytes(self.__frame)[:1]
            control = int.from_bytes(control, byteorder="big")

            control = bin(control)

            self.__data_list.append(data)

            if control == bin(0):
                data = b"".join(self.__data_list)
                print(data)
                self.__data_list = []

            self.__serial.write(
                bytes(
                    [
                        self.__flag,
                        self.__control,
                        self.__reserved,
                        self.__fcs_lsb,
                        self.__fcs_msb,
                        self.__flag,
                    ]
                )
            )
        else:
            print("Erro no FCS")

    def __rx(self, byte):
        if not (byte == self.__flag or byte == self.__esc):
            self.__frame.append(byte)
        elif byte == self.__esc:
            self.__state = self.__escape
        elif byte == self.__flag:
            self.__break_header()
            self.__state = self.__idle

    def __escape(self, byte):
        if byte != self.__esc:
            self.__frame.append(byte ^ 0x20)
            self.__state = self.__rx

    def handle(self):
        byte = self.__serial.read(1)

        self.__general_timeout = 1

        self.__state(byte[0])

    def handle_timeout(self):
        if self.__general_timeout == 3:
            self.__data_list = []
            self.__state = self.__idle
        else:
            self.__general_timeout += 1
            self.reload_timeout()


serial_port = sys.argv[1]

teste = RxEnlace(serial_port)
