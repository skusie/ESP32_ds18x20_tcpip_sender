import multiprocessing
import socket
import time
import ujson
import os
import queue as qu
import numpy as np
import pandas as pd
import datetime as dt


TCP_PORT = 5007

SENSOR_NAME_MAPPING =  {'0x287af7ffa003f' : 'sensorname1', # maps serial number to a custom name
			'0x287af7ffa003f' : 'sensorname1',
			'0x287af7ffa003f' : 'sensorname1'}

"""
data:77
(2022, 1, 18, 1, 22, 30, 58, 931369):0021.6250, 0021.6250, 0021.6250, 
<socket.socket fd=4, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=0, laddr=('192.168.145.11', 5007), raddr=('192.168.145.163', 51762)>
('192.168.145.163', 51762)
"""

def save_to_file_dataframe(df):
	filepath = './'
	filename = 'temperatures_' + dt.datetime.today().strftime('%Y%m%d') + '.csv'  # every day has its own file
	df.to_csv(filepath + filename, mode='a', header=not os.path.exists(filename)) # header = ... makes this function to append data without writing the header

def create_data_frame(numpy_array, column_names, index_names):
	if len(numpy_array.shape) > 1: # array has to have two dimensions, or the following line won't work
		df = pd.DataFrame(numpy_array[1:], columns=column_names, index=index_names) # ugly, have to "delete" first row of numpy array because of woerlks
		df.index.name = 'timestamps'
		return df

def plot_dataframe(dataframe, columns):
	ds = ColumnDataSource(df)
	Tools = []
	plots =[]
	
	for item in columns:
		p = figure(x_axis_type='datetime', width=1000, height=200, tools=Tools)
		p.scatter(x='index', y=item, source=ds)
		p.line(x='index', y=item, source=ds)
		plots.append(p)
	return plots


def show_plots(list_of_plots):
	show(column(list_of_plots))


def create_plots():
	df = pd.read_csv('temperatures_20220128.csv')
	columns = df.columns
	plots = plot_dataframe(df, columns)
	show_plots(plots)

def timer(cmd_queue, data_handler_queue):
	ten_minutes = 10
	save_time      = dt.datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
	last_timestamp = dt.datetime.now()
	while(True):

		now = dt.datetime.today()
		if (save_time - now).days == -1:
			data_handler_queue.put('save')
		if (now.minute - last_timestamp.minute) == 10:
			data_handler_queue.put('save')
		while(True):
			try:
				cmd = cmd_queue.get_nowait()
				if   cmd == 'exit':
					print('timer out!')
					break
				elif cmd == '10min_timer':
					pass
			except Exception: # ugly, but queue class somehow seems to not raise the empty exception clean
				break
#		print('running')
#		print((save_time - now).days)
#		print(now.minute - last_timestamp.minute)

		time.sleep(1)


def data_handler(cmd_queue):
	print('data handler started')
	cmd = ''
	timestamps = []
	temperature_array = np.zeros(3)
	while (True):
		cmd = cmd_queue.get()
		if   cmd == 'exit':
			print('data handler out!')
			break

		elif cmd == 'data':
			data = cmd_queue.get()
			tempsdict = ujson.loads(data.split(';')[1])
			temperature_array = np.vstack((temperature_array, np.array(list(tempsdict.values()))))
			column_names = list(tempsdict.keys())
			datestring = data.split(';')[0]
			timestamp = dt.datetime.strptime(datestring, '(%Y, %m, %d, %w, %H, %M, %S, %f)')
			timestamps.append(timestamp)
			print(data)
			
		elif cmd == 'save':
			save_to_file_dataframe(create_data_frame(temperature_array, column_names, timestamps))
			print('yes, I saved something')
			timestamps = []
			temperature_array = np.zeros(3)
		else:
			print('errorouneeous message: ' + cmd)


def temperature_data_server(cmd_queue, datahandler_queue):
	listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	listen_socket.bind(('', TCP_PORT))
	listen_socket.listen(1)
	
	print('Serving on port ' + str(TCP_PORT))
	while(True):
		cmd = cmd_queue.get()
		if   cmd == 'exit':
			datahandler_queue.put('save')
			datahandler_queue.put('exit')
			print('temperature server out!')
			break

		elif cmd == 'connect':
			client_connection, client_address = listen_socket.accept()
			request = client_connection.recv(8).decode()
			number_of_databytes = int(str(request.split(':')[1]))
			request2 = client_connection.recv(number_of_databytes).decode()
			datahandler_queue.put('data')
			# what if anyone queue.puts right here?
			datahandler_queue.put(request2)
			if not request:
				continue
			client_connection.close()
			cmd_queue.put('connect')

		else:
			print('errorouneeous message: ' + cmd)


datahandler_q  = multiprocessing.Queue()
tempserver_q   = multiprocessing.Queue()
timer_q        = multiprocessing.Queue()

tempserver_q.put('connect')

p1 = multiprocessing.Process(target=data_handler, args=(datahandler_q, ))
p2 = multiprocessing.Process(target=temperature_data_server, args=(tempserver_q, datahandler_q))
p3 = multiprocessing.Process(target=timer, args=(timer_q, datahandler_q))

p1.start()
p2.start()
p3.start()

while(True):
	try:
		keyinput = input()
		if keyinput == 'q':
			tempserver_q.put('exit')	
			print('exit sent tow tempserver')
			break
	except KeyboardInterrupt:
		print('\nYou killed the server, bye\n')
		tempserver_q.put('exit')
		break


p1.join()
p2.join()
p3.join()
