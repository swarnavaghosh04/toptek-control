from TopTek import Toptek, ToptekSwitches, ToptekState
import logging

logging.basicConfig(level=logging.DEBUG)

pa = Toptek("/dev/tty.usbserial-1450")
state = pa.read_state()

pa.press(ToptekSwitches.RX_LNA)
if not state.lna_on:
    pa.press(ToptekSwitches.RX_LNA)

if not state.tx_pa:
    pa.press(ToptekSwitches.TX_PA)

pa.switch_on(ToptekSwitches.DA_EN)

pa.set_tx_power(40)

print(pa.read_state())
print(pa.info())
