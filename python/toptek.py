import logging
import os
import sys
import time
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

import serial


class ToptekSwitches(IntEnum):
    SSB_ON = 1
    TX_PA = 2
    SET_PWR = 3
    RX_LNA = 4
    SHOW_SWR = 5
    DA_EN = 6


@dataclass
class ToptekState:
    led_10: bool
    led_20: bool
    led_30: bool
    led_40: bool
    led_50: bool
    led_60: bool
    led_70: bool
    led_80: bool
    red_en: bool
    lna_on: bool
    tx_pa: bool
    ssb_on: bool
    da_swr: bool

    def get_power(self) -> int:
        if self.red_en:
            raise ValueError("Red LEDs are on, unable to get power")

        if self.led_80:
            return 80
        if self.led_70:
            return 70
        if self.led_60:
            return 60
        if self.led_50:
            return 50
        if self.led_40:
            return 40
        if self.led_30:
            return 30
        if self.led_20:
            return 20
        if self.led_10:
            return 10
        return 0

    def get_swr(self) -> float:
        if self.led_80:
            return 1.9
        if self.led_70:
            return 1.8
        if self.led_60:
            return 1.7
        if self.led_50:
            return 1.6
        if self.led_40:
            return 1.5
        if self.led_30:
            return 1.4
        if self.led_20:
            return 1.3
        if self.led_10:
            return 1.2
        return 1

    def get_errors(self) -> str:
        if not self.red_en:
            raise ValueError("No error apparent!")

        errors = []

        if self.led_10:
            errors.append("PA FAIL")
        if self.led_20:
            errors.append("HIGH TEMP")
        if self.led_30:
            errors.append("DC VOLTAGE")
        if self.led_40:
            errors.append("OVERDRIVE")
        if self.led_50:
            errors.append("HIGH SWR")

        return errors


@dataclass
class ToptekSwitchState:
    sw_ssb_on: bool
    sw_tx_pa: bool
    sw_set_pwr: bool
    sw_rx_lna: bool
    sw_show_swr: bool
    sw_da_on: bool


class Toptek:
    def __init__(self, port: str) -> None:
        # Ensure we have r/w
        self.port = Path(port)
        if not self.port.exists():
            raise FileNotFoundError(self.port)

        if not os.access(self.port, os.R_OK | os.W_OK):
            logging.critical(
                f"Unable to acquire read/write permissions on {self.port}.\n"
                + "Please change permissions, or run this script as superuser."
            )
            sys.exit(1)

        self.ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(1)
        if self.readline() != "Toptek Switch Interface":
            raise RuntimeError("Invalid welcome message")

    def write(self, cmd: str) -> None:
        logging.debug(f"TX: {cmd}")
        self.ser.write(cmd.encode("ascii"))
        time.sleep(0.05)
        ret = self.readline()
        if ret != f"{cmd}":
            raise RuntimeError(f"Invalid response from Toptek: {ret}")

    def readline(self) -> str:
        line = self.ser.readline()
        line_decoded = line.decode("utf-8").strip()
        logging.debug(f"RX: {line_decoded}")
        return line_decoded

    def query(self, cmd: str) -> str:
        self.write(cmd)
        return self.readline()

    def switch_on(self, switch: ToptekSwitches) -> None:
        self.write(f"S{int(switch)}")

    def switch_off(self, switch: ToptekSwitches) -> None:
        self.write(f"U{int(switch)}")

    def press_manual(self, switch: ToptekSwitches, delay: float = 0.2):
        self.switch_on(switch)
        time.sleep(delay)
        self.switch_off(switch)

    def press(self, switch: ToptekSwitches):
        self.write(f"P{int(switch)}")
        # So that the PA can figure out what hit it
        time.sleep(0.1)

    def get_switch(self, switch: ToptekSwitches) -> bool:
        return bool(self.query(f"R{int(switch)}"))

    def enable(self) -> None:
        ret = self.query("EN")
        if ret != "Remote keys enabled":
            raise RuntimeError("Failed to enable remote keys")
        logging.info("Enabled remote control of PA")

    def disable(self) -> None:
        ret = self.query("DS")
        if ret != "Remote keys disabled":
            raise RuntimeError("Failed to disable remote keys")
        logging.info("Disabled remote control of PA")

    def read_state(self) -> ToptekState:
        da_state = int(self.query("RS"))
        toptek_state = int(self.query("RA"), 16)

        return ToptekState(
            bool(toptek_state & 0b0000000000000001),
            bool(toptek_state & 0b0000000000000010),
            bool(toptek_state & 0b0000000000000100),
            bool(toptek_state & 0b0000000000001000),
            bool(toptek_state & 0b0000000000010000),
            bool(toptek_state & 0b0000000000100000),
            bool(toptek_state & 0b0000000001000000),
            bool(toptek_state & 0b0000000010000000),
            bool(toptek_state & 0b0000000100000000),
            bool(toptek_state & 0b0000001000000000),
            bool(toptek_state & 0b0000010000000000),
            bool(toptek_state & 0b0000100000000000),
            bool(da_state),
        )

    def read_switch_state(self) -> ToptekSwitchState:
        da_sw = int(self.query("R6"))
        toptek_sw = int(self.query("RS"), 16)
        return ToptekSwitchState(
            bool(toptek_sw & 0b00010000),
            bool(toptek_sw & 0b00100000),
            bool(toptek_sw & 0b00000100),
            bool(toptek_sw & 0b00001000),
            bool(toptek_sw & 0b00000001),
            bool(da_sw),
        )

    def info(self) -> str:
        state = self.read_state()
        sw_state = self.read_switch_state()
        outstr = "Toptek State: "

        if state.tx_pa:
            outstr += "PA is ENABLED"
        else:
            outstr += "PA is DISABLED"

        if state.lna_on:
            outstr += ", LNA is ENABLED"
        else:
            outstr += ", LNA is DISABLED"

        if state.ssb_on:
            outstr += ", SSB is ENABLED"
        else:
            outstr += ", SSB is DISABLED"

        if sw_state.sw_da_on:
            outstr += ", DA is ON"
        else:
            outstr += ", DA is OFF"

        if state.da_swr:
            outstr += ", DA is showing HIGH SWR"

        if sw_state.sw_show_swr:
            outstr += ", SHOW SWR mode is ENABLED (not implemented)"
            return outstr

        outstr += f", output power set at {self.get_tx_power()}W"

        if state.red_en:
            outstr += f", ERRORS: {state.get_errors()}"
            return outstr

        outstr += f", current power: {state.get_power()}"

        return outstr

    def get_flashy_bargraph(self) -> ToptekState:
        state = None
        POLL_DELAY = 0.05  # Time between checking state
        TOTAL_DELAY = 2  # Time until PA's bargraph mode turns off
        for i in range(int(TOTAL_DELAY / POLL_DELAY)):
            time.sleep(POLL_DELAY)
            state = self.read_state()
            if state.get_power() != 0:
                time.sleep(TOTAL_DELAY-i*POLL_DELAY)
                break

        return state

    #  ╭──────────────────────────────────────────────────────────╮
    #  │                      POWER HELPERS                       │
    #  ╰──────────────────────────────────────────────────────────╯

    def get_tx_power(self) -> int:
        self.press(ToptekSwitches.SET_PWR)
        return self.get_flashy_bargraph().get_power()

    def set_tx_power(self, power: int) -> None:
        if power not in [20, 40, 60, 80]:
            raise ValueError(
                f"Invalid set power (got {power}, needs to be 20, 40, 60, or 80)"
            )

        set_power = self.get_tx_power()
        if set_power < power:
            num_presses = int(abs(set_power - power) / 20)
        else:
            num_presses = int((80 - set_power) / 20) + int(power / 20)

        if num_presses == 0:
            return

        self.press(ToptekSwitches.SET_PWR)
        time.sleep(0.1)

        for i in range(num_presses):
            time.sleep(0.2)
            self.press(ToptekSwitches.SET_PWR)

        # Timeout so we don't accidentally increment the power
        time.sleep(2)
        actual_set = self.get_tx_power()
        if actual_set != power:
            raise RuntimeError(
                f"Power not set correctly (got {actual_set}, wanted {power})"
            )

    def get_cur_power(self) -> int:
        state = self.read_state()
        if state.red_en:
            raise RuntimeError("Amplifier in error or in check SWR mode")
        logging.info(f"Current power is {state.get_power()}W")
        return state.get_power()

    #  ╭──────────────────────────────────────────────────────────╮
    #  │                      SWITCH HELPERS                      │
    #  ╰──────────────────────────────────────────────────────────╯

    def pa_on(self) -> None:
        state = self.read_state()
        if not state.tx_pa:
            logging.info("Turning PA on")
            self.press(ToptekSwitches.TX_PA)
            # sometimes the PA needs some extra time
            time.sleep(0.3)

            state = self.read_state()
            if not state.tx_pa:
                raise RuntimeError("PA not turned on")
        else:
            logging.info("PA already on")

    def pa_off(self) -> None:
        state = self.read_state()
        if state.tx_pa:
            logging.info("Turning PA off")
            self.press(ToptekSwitches.TX_PA)

            state = self.read_state()
            if state.tx_pa:
                raise RuntimeError("PA not turned off")
        else:
            logging.info("PA already off")

    def lna_on(self) -> None:
        state = self.read_state()
        if not state.lna_on:
            logging.info("Turning LNA on")
            self.press(ToptekSwitches.RX_LNA)
            # sometimes the LNA needs some extra time
            time.sleep(0.3)

            state = self.read_state()
            if not state.lna_on:
                raise RuntimeError("LNA not turned on")
        else:
            logging.info("LNA already on")

    def lna_off(self) -> None:
        state = self.read_state()
        if state.lna_on:
            logging.info("Turning LNA off")
            self.press(ToptekSwitches.RX_LNA)

            state = self.read_state()
            if state.lna_on:
                raise RuntimeError("LNA not turned off")
        else:
            logging.info("LNA already off")

    def ssb_on(self) -> None:
        state = self.read_state()
        if not state.tx_pa:
            logging.warning("Cannot turn on SSB when PA not on")
            return

        if not state.ssb_on:
            logging.info("Turning SSB on")
            self.press(ToptekSwitches.SSB_ON)
            # sometimes the SSB needs some extra time
            time.sleep(0.5)

            state = self.read_state()
            if not state.ssb_on:
                raise RuntimeError("SSB not turned on")

        else:
            logging.info("SSB already on")

    def ssb_off(self) -> None:
        state = self.read_state()
        if not state.tx_pa:
            logging.warning("Cannot turn off SSB when PA not on")
            return

        if state.ssb_on:
            logging.info("Turning SSB off")
            self.press(ToptekSwitches.SSB_ON)

            state = self.read_state()
            if state.ssb_on:
                raise RuntimeError("SSB not turned off")
        else:
            logging.info("SSB already off")

    def da_on(self) -> None:
        state = self.read_switch_state()
        print(state.sw_da_on)
        if not state.sw_da_on:
            logging.info("Turning DA on")
            self.switch_on(ToptekSwitches.DA_EN)

            state = self.read_switch_state()
            if not state.sw_da_on:
                raise RuntimeError("DA not turned on")
        else:
            logging.info("DA already on")

    def da_off(self) -> None:
        state = self.read_switch_state()
        if state.sw_da_on:
            logging.info("Turning DA off")
            self.switch_off(ToptekSwitches.DA_EN)

            state = self.read_switch_state()
            if state.sw_da_on:
                raise RuntimeError("DA not turned off")
        else:
            logging.info("DA already off")