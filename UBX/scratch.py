import signal
from optparse import OptionParser
from ubxstreamer import *

def signal_handler(g_var, ubp, signal, frame):
    # print("in sig handler - g_var=%s" % g_var)
    print(f"in sig handler - g_var={g_var}")
    ubp._e.set()
    print("resuming")


def main(config_bool, read_bool, time_bool, port, baud, timeout, ubxonly):

    ubp = UBXStreamer(port, baud, timeout, ubxonly)
    signal.signal(signal.SIGINT, partial(signal_handler, "hello", ubp))
    # signal.signal(signal.SIGINT, partial(UBXStreamer.signal_handler, ubp))  # handle the keyboard control

    print(f"Connecting to serial port {port} at {baud} baud...")
    if ubp.connect():
        if read_bool:
            print("Starting reader thread...")
            ubp.start_read_thread() # From here on, all ack or nak should be printed right?

    while ubp._live:
        print("\n\t\t\twaiting for feedback")

        keys = [("CFG_UART1_PARITY")]
        msg = UBXMessage.config_poll(2, 0, keys)
        # print(f"{msg}, bruh {msg.identity}, bruh {msg.msg_cls}, bruh {msg.length}")
        # thang = msg.msg_cls == b'\x06'
        # print(f"{thang}")

        ubp._single_send_pollmsg(msg)
        print('end')
        sleep(1)



if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--skip_config", action="store_false", dest="config_bool",
                      help="If flag, don't send config commands", default=True)
    parser.add_option("--skip_read", action="store_false", dest="read_bool",
                      help="If flag, don't open serial read daemon/ignore serial in", default=True)
    parser.add_option("--find_time", action="store_true", dest="time_bool", help="If flag, find time stamps",
                      default=False)
    parser.add_option("--port", type="string", dest="port", help="Linux port of serial dev",
                      default="/dev/ttyUSB0")  # This is typically true for LINUX systems
    parser.add_option("--baud", type="int", dest="baud", help="Baud rate of dev", default=115200)
    parser.add_option("--timeout", type="float", dest="timeout", help="Serial Timeout", default=0.1)
    parser.add_option("--ubxonly", action="store_true", dest="ubxonly",
                      help="If flag, raise exception when reading non-UBX data", default=False)
    (options, args) = parser.parse_args()

    main(
        config_bool=options.config_bool,
        read_bool=options.read_bool,
        time_bool=options.time_bool,
        port=options.port,
        baud=options.baud,
        timeout=options.timeout,
        ubxonly=options.ubxonly
    )