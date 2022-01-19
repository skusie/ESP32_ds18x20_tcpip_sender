import network, socket, onewire, time, ds18x20
import ntptime
from machine import Pin, RTC

def read_pw_file(filename):
	filehandle = open(filename, 'r')
	data = filehandle.read().split(',')
	filehandle.close()
	ssid = data[0]
	pw   = data[1][0:-1]
	return ssid, pw

def connect_wlan():
	ssid, pw = read_pw_file('creds.txt')
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
	s.connect(('192.168.145.11', 5007))
	s.send(command.encode())
	print(s.recv(1))
	s.close()

def get_temperature_data():
	ow = onewire.OneWire(Pin(15))
	ds = ds18x20.DS18X20(ow)
	roms = ds.scan()
	ds.convert_temp()
	time.sleep_ms(1500)
	temp_data = ''
	try:
		for rom in roms:
			temp_data += zfill_special(str(ds.read_temp(rom)), 4) + ', '
	except:
		temp_data = get_temperature_data()

	return(temp_data)


def zfill_special(string, width):
	string  = string.split('.')
	string0 = string[0]
	string1 = string[1]
	
	if len(string0) < width:
		string0 = ("0" * (width - len(string0))) + string0 

	if len(string1) < width:
		string1 = string1 + "0" * (width - len(string1))

	return (string0 + '.' + string1)


connect_wlan()
rtc = RTC()
print(rtc.datetime())
ntptime.host='fritz.box'
ntptime.settime()
while True:
	temps = get_temperature_data()
	print(temps)
	message = str(rtc.datetime()) + ':' + temps
	message_length = len(message)
	header  = 'data:' + str((5 + len(message) + len(str(message_length))))	
	print(header+message)
	connect_server_and_send_data(header + message)
	time.sleep_ms(1000)
