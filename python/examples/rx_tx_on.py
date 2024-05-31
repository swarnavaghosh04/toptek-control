import logging
from argparse import ArgumentParser

from toptek import Toptek


def main():
    logging.basicConfig(level=logging.INFO)

    parser = ArgumentParser(
        prog="PA_on.py",
        description="Turns PA and LNA on to typical operating conditions",
    )
    parser.add_argument(
        "port",
        help="Serial port connected to an Arduino (typically /dev/ttyUSB0)",
    )

    parser.add_argument(
        "power",
        help="Power level to set (20 | [40] | 60 | 80)",
        nargs="?",
        default="40",
    )

    args = parser.parse_args()

    pa = Toptek(args.port)

    pa.lna_on()
    pa.pa_on()
    pa.da_on()

    pa.set_tx_power(int(args.power))

    print(pa.info())


if __name__ == "__main__":
    main()
