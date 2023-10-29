import logging
from argparse import ArgumentParser

from toptek import Toptek


def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = ArgumentParser(
        prog="PA_on.py",
        description="Turns PA and LNA on to typical operating conditions",
    )
    parser.add_argument(
        "port",
        help="Serial port connected to an Arduino (typically /dev/ttyUSB0)",
    )

    logging.basicConfig(level=logging.DEBUG)

    args = parser.parse_args()

    pa = Toptek(args.port)

    pa.lna_on()
    pa.pa_on()
    pa.da_on()

    pa.set_tx_power(40)

    print(pa.info())


if __name__ == "__main__":
    main()
