
import serial
import pyubx2
from pyubx2 import UBXMessage
from serial import PARITY_NONE, EIGHTBITS, STOPBITS_ONE
import time

from serial_config import all_msgs



def eq():
    print("\n==============================================================\n"
          "==============================================================\n"
          "==============================================================\n")

def create_serStream(port='/dev/ttyUSB0', timeout=0):
    return(serial.Serial(port, baudrate=115200, parity=PARITY_NONE, bytesize=EIGHTBITS, stopbits=STOPBITS_ONE, timeout=timeout))

def test_identity():
    msg1 = yuh

def main(op="read"):
    port = "/dev/ttyUSB0"
    layers = 1  # RAM
    transaction = 0  # None
    bytearr = bytearray()
    if op == "read":
        cfgData = ["CFG_TP_LEN_LOCK_TP1"]
        msg = UBXMessage.config_poll(layer=0, position=0, keys=cfgData)
    else:
        cfgData = [("CFG_TP_LEN_LOCK_TP1", 100000), ('CFG_TP_LEN_TP1', 100000), ("CFG_TP_TP1_ENA", 1),
                   ("CFG_TP_PERIOD_TP1", 1000000)
                   ]
        msg = UBXMessage.config_set(layers, transaction, cfgData)
    try:
        serStream = create_serStream(timeout=1)
        serStream.write(msg.serialize())
        time.sleep(1)
        # if not (serStream.read(size=1) == bytes("\n", "utf-8")):
        #     exit(7)
        while serStream.inWaiting():
            bytearr.extend(serStream.read(size=1))

        # num = int.from_bytes(read_val, byteorder='little', signed=False)
        # print(str(num) + "\t\t" + str(read_val.hex()) + "\t\t" + str(read_val), end=" ")
        # if read_val != '':
        #     print("\t" + str(port))

        print(bytearr.decode("utf-8"))
        serStream.close()
    except serial.SerialException:
        print("Bruh")


if __name__ == '__main__':
    main("read")
    eq()
    main("write")
