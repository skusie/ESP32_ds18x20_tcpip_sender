import network, socket, onewire, time, ds18x20
import ntptime
from machine import Pin, RTC


CONFIGURATION = {'ds18x20_pin_number' :  15,
		 'server_ip_address'  : '192.168.145.11',	
		 'creds_file_name'    : 'creds.txt',
		 'ntphost'            : 'fritz.box'
	        }
		

def read_wlan_file(filename):
	filehandle = open(filename, 'r')
	data = filehandle.read().split(',')
	filehandle.close()
	ssid = data[0]
	pw   = data[1][0:-1]
	return ssid, pw

def connect_wlan():
	global CONFIGURATION
	ssid, pw = read_wlan_file(CONFIGURATION['creds_file_name'])
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
	global CONFIGURATION
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.connect((CONFIGURATION['server_ip_address'], 5007))
		s.send(command.encode())
	except OSError as exc:
		s.close()
		if exc.errno == errno.ECONNRESET:	
			print('Server not reachable')
	#print(s.recv(1))

def init_ds18x20_sensors():
	ow = onewire.OneWire(Pin(CONFIGURATION['ds18x20_pin_number']))
	ds = ds18x20.DS18X20(ow)
	roms = ds.scan()
	return ds, roms


def get_temperature_data(ds, roms):
	print('converting...')
	ds.convert_temp()
	print('sleeping...')
	time.sleep_ms(750)
	print('reading...')
	temp_data = ''
	first_iteration = True
	try:
		for rom in roms:
			if first_iteration:
				first_iteration = False
				temp_data += zfill_special(str(ds.read_temp(rom)), 4)
			else:
				temp_data += ',' + zfill_special(str(ds.read_temp(rom)), 4)
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

def main_loop():
	connect_wlan()
	rtc = RTC()
	print(rtc.datetime())
	ntptime.host=CONFIGURATION['ntphost']
	ntptime.settime()
	ds, roms = init_ds18x20_sensors()	
	while True:
		temps = get_temperature_data(ds, roms)
		message = str(rtc.datetime()) + ':' + temps
		message_length = len(message)
		header  = 'data:' + str((5 + len(message) + len(str(message_length))))	
		#todo hier kommentar mit Beispiel message
		connect_server_and_send_data(header + message)
		print(temps)
		print(header + message)
		#time.sleep_ms(1000)
