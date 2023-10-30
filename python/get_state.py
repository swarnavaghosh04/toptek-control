import logging
from argparse import ArgumentParser

from toptek import Toptek


def main():
    logging.basicConfig(level=logging.INFO)

    parser = ArgumentParser(
        prog="get_state.py",
        description="Returns current state of the system",
    )
    parser.add_argument(
        "port",
        help="Serial port connected to an Arduino (typically /dev/ttyUSB0)",
    )

    args = parser.parse_args()

    pa = Toptek(args.port)

    print(pa.info())


if __name__ == "__main__":
    main()
