#!/usr/bin/env python3

import sys
from controller import Controller


def application_start() -> None:
    controller = Controller(sys.argv)
    controller.start()


if __name__ == '__main__':
    application_start()
