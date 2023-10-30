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

    args = parser.parse_args()

    pa = Toptek(args.port)

    pa.lna_on()
    pa.pa_off()
    pa.da_off()

    print(pa.info())


if __name__ == "__main__":
    main()
