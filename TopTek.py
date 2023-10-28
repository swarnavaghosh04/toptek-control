import time
from dataclasses import dataclass
from enum import IntEnum

import logging 
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

    def press(self, switch: ToptekSwitches, delay: float = 0.2):
        self.switch_on(switch)
        time.sleep(delay)
        self.switch_off(switch)

    def get_switch(self, switch: ToptekSwitches) -> bool:
        return bool(self.query(f"R{int(switch)}"))

    def read_state(self) -> ToptekState:
        da_state = self.query("RS")
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
        da_sw = self.query("R6")
        toptek_sw = int(self.query("RS"), 16)
        return ToptekSwitchState(
            bool(toptek_sw & 0b00010000),
            bool(toptek_sw & 0b00100000),
            bool(toptek_sw & 0b00000100),
            bool(toptek_sw & 0b00001000),
            bool(toptek_sw & 0b00000001),
            bool(da_sw),
        )

    def get_tx_power(self) -> int:
        self.press(ToptekSwitches.SET_PWR, delay=0.1)
        state = None
        for i in range(10):
            time.sleep(0.1)
            state = self.read_state()
            if state.get_power() != 0:
                break

        return state.get_power()

    def set_tx_power(self, power: int) -> None:
        if power not in [20, 40, 60, 80]:
            raise ValueError(f"Invalid set power (got {power}, needs to be 20, 40, 60, or 80)")

        set_power = self.get_tx_power()
        num_presses = int(abs(set_power - power) / 20)

        if num_presses > 0:
            self.press(ToptekSwitches.SET_PWR)

            for i in range(num_presses):
                time.sleep(0.5)
                self.press(ToptekSwitches.SET_PWR)

            # Verify
            actual_set = self.get_cur_power()
            if actual_set != power:
                raise RuntimeError(f"Power not set correctly (got {actual_set}, wanted {power})")

    def get_cur_power(self) -> int:
        state = self.read_state()
        if state.red_en:
            raise RuntimeError("Amplifier in error or in check SWR mode")
        return state.get_power()

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

        if sw_state.sw_show_swr:
            outstr += ", SHOW SWR mode is ENABLED (not implemented)"
            return outstr

        outstr += f", output power set at {self.get_tx_power()}W"

        if state.red_en:
            outstr += f", ERRORS: {state.get_errors()}"
            return outstr

        outstr += f", current power: {state.get_power()}"

        return outstr
