from TopTek import Toptek, ToptekSwitches, ToptekState

pa = Toptek("/dev/tty.usbserial-1450")

pa.press(ToptekSwitches.RX_LNA)

print(pa.read_state())
