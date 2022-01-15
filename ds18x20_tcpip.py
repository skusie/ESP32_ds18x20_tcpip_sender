import network, socket, onewire, time, ds18x20
from ntptime
from machine import Pin, RTC

def read_pw_file(filename):
	filehandle = open(filename, 'r')
	ssid = filehandle.readline()
	pw   = filehandle.readline()
	filehandle.close()
	return ssid, pw

def connect_wlan():
	ssid, pw = read_pw_file('wlan_credentials.txt')
	wlan = network.WLAN(network.STA_IF)
	wlan.active(True)
	if not wlan.isconnected():
		print('connecting to network...')
	wlan.connect(ssid, pw) # connect to an AP
	while not wlan.isconnected(): 
		print('.', end='')
		time.sleep(1)
	print('network config:', wlan.ifconfig())

def connect_server_and_send_data(command):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('192.168.145.34', 5006))
	s.send(command.encode())
	print(s.recv(1))
	s.close()

def get_temperature_data():
	ow = onewire.OneWire(Pin(27))
	ds = ds18x20.DS18X20(ow)
	roms = ds.scan()
	ds.convert_temp()
	time.sleep_ms(1500)
	temp_data = ''
	try:
		for rom in roms:
			temp_data += str(ds.read_temp(rom)) + ', '
	except:
		temp_data = get_temperature_data()
	return(temp_data)

connect_wlan()
rtc = RTC()
ntptime.host='fritz.box'
ntptime.settime()
print(rtc.datetime())
while True:
	temps = get_temperature_data()
	print(temps)
	message = str(rtc.datetime()) + ':' + temps
	message_length = len(message)
	header  = 'data:' + str((5 + len(message) + len(str(message_length))))	
	connect_server_and_send_data(header + message)
	time.sleep_ms(1000)
