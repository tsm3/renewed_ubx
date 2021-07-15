"""
Modified implementation of a UBXStreamer class

Rahman said to make an API right?
@author: tsm3
"""


import signal
import threading
from io import BufferedReader
from threading import Thread
from time import sleep
from functools import partial

from pyubx2 import UBXMessage, POLL, UBX_MSGIDS
from pyubx2.ubxreader import UBXReader
from serial import Serial, SerialException, SerialTimeoutException

import pyubx2.exceptions as ube
import math
import logging

from serial_config import all_msgs, ack_msg


class UBXStreamer:
    """
    UBXStreamer class. -> Tristan
    Can start a serial connection, thread out a reader, and send serial (config) so far.
    """

    def __init__(self, port, baudrate, timeout=5, ubx_only=False):
        """
        Constructor.
        """

        self._serial_object = None
        self._serial_thread = None
        self._ubxreader = None
        self._connected = False
        self._reading = False
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._ubx_only = ubx_only

        self._live = True
        self._waiting_ack = False
        self._waiting_parse = False
        self._parsed_data: "UBXMessage" = None  # Try using this to pass parsed data from the reading thread to the main thread
        self._e = threading.Event()
        self._parsing_e = threading.Event()
        self._parsing_e.set()

        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s : %(levelname)s : %(message)s")

    def __del__(self):
        """
        Destructor.
        """

        self.stop_read_thread()
        self.disconnect()

    def connect(self):
        """
        Open serial connection.
        """

        self._connected = False
        try:
            self._serial_object = Serial(
                self._port, self._baudrate, timeout=self._timeout
            )
            self._ubxreader = UBXReader(BufferedReader(self._serial_object), ubxonly=self._ubx_only)
            self._connected = True
        except (SerialException, SerialTimeoutException) as err:
            print(f"Error connecting to serial port {err}")

        return self._connected

    def disconnect(self):
        """
        Close serial connection.
        """

        if self._connected and self._serial_object:
            try:
                self._serial_object.close()
            except (SerialException, SerialTimeoutException) as err:
                print(f"Error disconnecting from serial port {err}")
        self._connected = False

        return self._connected

    def start_read_thread(self):
        """
        Start the serial reader thread.
        """

        if self._connected:
            self._reading = True
            self._serial_thread = Thread(target=self._read_thread, daemon=True)
            self._serial_thread.start()

    def stop_read_thread(self):
        """
        Stop the serial reader thread.
        """

        if self._serial_thread is not None:
            self._reading = False

    def send(self, data):
        """
        Send data to serial connection.
        """

        self._serial_object.write(data)

    def flush(self):
        """
        Flush input buffer
        """

        self._serial_object.reset_input_buffer()

    def waiting(self):
        """
        Check if any messages remaining in the input buffer
        """

        return self._serial_object.in_waiting

    def _read_thread(self):
        """
        THREADED PROCESS
        Reads and parses UBX message data from stream

        """

        while self._reading and self._serial_object and self._live:  # HERE: Check if _live does same as _reading
            if self._serial_object.in_waiting:
                self._parsing_e.wait(timeout=None)  # If some data needs to get parsed, use this to do it
                try:
                    (raw_data, parsed_data) = self._ubxreader.read()
                    #                     if raw_data:
                    #                         print(raw_data)
                    if parsed_data:
                        self._parsed_data = parsed_data
                        if parsed_data.msg_cls == b'\x05':  # That is, class == ACK
                            if UBXStreamer.is_ack(parsed_data):
                                self._waiting_ack = False
                                print("Acknowledged")
                        else:
                            print("Not an ack:", end="\n\t\t\t")
                            # print(parsed_data, end="\n\t\t\t")
                            print(parsed_data, end="\n\t\t\t")
                            print(parsed_data.payload)
                        if self._waiting_parse:
                            self._parsing_e.clear()
                        self._e.set()  # Everytime there exists parsed data, after it prints, sets _e flag -> wake up main thread
                except (
                    ube.UBXStreamError,
                    ube.UBXMessageError,
                    ube.UBXTypeError,
                    ube.UBXParseError,
                ) as err:
                    print(f"Something went wrong {err}")
                    continue

    def send_setmsg(self, msg: 'UBXMessage'):
        """
        Easy way to send one SET message that's passed in.
        That is, a CFG-XXX SET message -> Expect a ACK-ACK in return
        """
        if msg.msgmode != 1:  # mode = 1 is SET
            raise ValueError(f"msg is of type {msg.msgmode} not 'SET'")
        self.send(msg.serialize())
        self._waiting_ack = True
        while self._waiting_ack:  # Wait for acknowledgement
            self._e.clear()
            self._e.wait(timeout=None)
        self._e.clear()

    def _single_send_pollmsg(self, msg: 'UBXMessage'):
        """
        Easy way to send one POLL message that's passed in.
        Will wait till the read thread returns the correct message, and interpret it
        """
        if msg.msgmode != 2:  # mode = 2 is POLL
            raise ValueError(f"msg is of type {msg.msgmode}, not POLL")

        # Only expect and ACK back if it's a CFG POLL
        if msg.msg_cls == b'\x06':  # That is, if it's a CFG message
            logging.info("This is a 'CFG' class message, expecting a ACK and CFG response")  # LOG
            self._waiting_ack = True
        self._waiting_parse = True
        self.send(msg.serialize())

        thing = [msg]
        if self._waiting_ack:
            thing.append(ack_msg)  # want this to be a ACK ACK msg
            # thing.append(UBXMessage('b\x05', b'\x01', 0))




        while thing:
            # HERE: make sure you wait long enough to get the first response from this, else you'll 'NONE' out
            self._e.wait(timeout=None)  # the _parsing_e flag will clear in read_thread since _waiting_parse
            self._e.clear()
            resp = self._parsed_data
            print(f"{resp}")
            if resp.msg_cls == b'\x05':
                logging.info(f"{resp.identity} received, clearing self._waiting_ack")  # LOG
                logging.info(f"{resp}")
                self._parsing_e.set()
                self._waiting_ack = False
                thing.remove(ack_msg)
            elif resp.identity == msg.identity:
                print("hi")
                self._parsing_e.set()
                self._waiting_parse = False
                thing.remove(msg)
            else:
                print(f"in while thing loop: thing {thing}, resp {resp}")




        # while self._waiting_ack:# or msg.identity != self._parsed_data.identity:  # Wait for acknowledgement
        #     self._e.clear()  # if we wake up and want to wait() again, we have to clear (if we wake up and it's not an ACK)
        #     self._e.wait(timeout=None)
        self._e.clear()  # Clear here from waking up for the ACK
        print("two two")
        print(f"\t\t{self._parsed_data}")
        # After ACK, have to make sure the response is the right type
        print("three")
        #  So now we've gotten an ACK and a "GET" msg, check if it's the right one
        response = self._parsed_data
        if msg.msg_cls == response.msg_cls and msg.msg_id == response.msg_id:
            print("Yuh we got the response to the poll :) \n\t\t", str(response))


    def send_pollmsg(self, msg: 'UBXMessage'):  # Not sure if I want to have them pass in a UBXMessage or have them pass in things to POLL
        """
        Can send a UBX POLL message of any length (by sending them all in series)
        """
        if msg.msgmode != 2:  # mode = 2 is POLL
            raise ValueError(f"msg is of type {msg.msgmode}, not POLL")
        if msg.length > 1:
            raise ValueError(f"This isn't implemented yet, please be nice and only send POLLs with length=1")
        self._single_send_pollmsg(msg)


    @staticmethod
    def set_configs(ubp: 'UBXStreamer'):
        """
        :rtype: None
        """
        # return None
        layers = 1  # Flash
        transaction = 0  # No Transaction
        BATCH = 0
        if (BATCH):
            # for i in range(math.ceil(len(all_msgs)/64)+1):  #HERE: This should be the right line, but the last one NAKs?? but not when do individually, maybe ordering?
            for i in range(math.ceil(len(all_msgs)/64)):
                print(i)
                msg = UBXMessage.config_set(layers, transaction, all_msgs[i*64: ((i+1)*64-1)])  # Allows us to set 64 at a time (max)
                ubp.send_setmsg(msg)
        else:
            for i in range(0, len(all_msgs)):
                print(i)
                print(all_msgs[i])
                msg = UBXMessage.config_set(layers, transaction, [all_msgs[i]])  # Set one at a time
                ubp.send(msg.serialize())
                ubp._waiting_ack = True
                print("Expecting an ACK response: \t\t\t", end="")
                while ubp._waiting_ack:
                    ubp._e.clear()  # This makes the main thread wait till next _e.set(), if it's set but _waiting_ack still False, we want to wait again
                    ubp._e.wait(timeout=None)  # sleep till next read
                ubp._e.clear()  # Clear from last read (should be from the ACK reading

    @staticmethod
    def is_ack(parsed_data: 'UBXMessage') -> bool:
        """
        Used in read thread, to check identity of data in.
        If the passed message is not 'ACK-ACK', raise Exception
        :param parsed_data: a message returned from _ubxreader.read()
        :type parsed_data: UBXMessage
        :rtype: bool
        """
        if parsed_data.identity == 'ACK-ACK':
            return True
        else:
            # signal.raise_signal(signal.SIGINT)
            raise Exception("NAK encountered")

    @staticmethod
    def signal_handler(ubp, signal, frame):
        print(f"{signal} received")
        ubp._live = False
        ubp.__del__()
        exit(0)
