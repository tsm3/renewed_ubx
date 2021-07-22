"""
Test Script to alternate between SET and POLL msgs and ensure the RCB behaves as we expect.


"""

from optparse import OptionParser
from ubxstreamer import *


def main(port="/dev/ttyUSB0", baud=115200, timeout=0.1, ubxonly=False):
    with UBXStreamer(port, baud, timeout, ubxonly) as ubp:
        ubp: "UBXStreamer"  # Type Hinting, comment out if running Python lower than 3.6 or after file complete
        signal.signal(signal.SIGINT, partial(UBXStreamer.signal_handler, ubp))
        set_short_len = UBXMessage.config_set(layers=1, transaction=0, cfgData=[("CFG_TP_DUTY_TP1", 10)])
        set_long_len = UBXMessage.config_set(layers=1, transaction=0, cfgData=[("CFG_TP_DUTY_TP1", 50)])
        # poll_tp_type = UBXMessage.config_poll(layer=1, position=0, keys=["CFG_TP_PULSE_DEF"])
        poll_tp_data = UBXMessage(b'\x0d', b'\x01', POLL)
        poll_tp_type = UBXMessage(b'\x0d', b'\x01', 2)
        poll_navpvt = UBXMessage(b'\x01', b'\x07', POLL)

        print(poll_tp_data)
        print(poll_navpvt)
        if ubp.connect():
            ubp.start_read_thread()
            logging.info("Successfully Connected")
            while ubp._live:
                logging.info("Starting loop")
                # ubp._single_send_pollmsg(poll_tp_type)
                ubp._single_send_pollmsg(poll_navpvt)
                logging.info("sleep 1")
                sleep(1)
                ubp.send_setmsg(set_short_len)
                logging.info("sleep 2")
                sleep(2)
                ubp._single_send_pollmsg(poll_tp_type)
                logging.info("sleep 3")
                sleep(1)
                ubp.send_setmsg(set_long_len)
                logging.info("End of loop")
                print("\n==========\n==========")
                sleep(2)





if __name__ == '__main__':
    main()
    exit(0)
