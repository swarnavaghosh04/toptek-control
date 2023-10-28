from TopTek import Toptek, ToptekSwitches, ToptekState

pa = Toptek("/dev/tty.usbserial-1450")

pa.press(ToptekSwitches.RX_LNA)

#print(pa.get_tx_power())
