import numpy as np
import pandas as pd
import datetime as dt

from bokeh.plotting import figure, show, curdoc
from bokeh.models import ColumnDataSource, Button, DatetimeTickFormatter
from bokeh.layouts import column


def plot_dataframe(dataframe, columns):
	ds = ColumnDataSource(df)
	plots =[]
	
	for item in columns:
		p = figure(title=item, x_axis_type='datetime', width=1200, height=400, toolbar_location='above')
		p.xaxis.formatter=DatetimeTickFormatter(days="%m/%d %H:%M",
		months  ="%H:%M",
		hours   ="%H:%M",
		minutes ="%H:%M",
		minsec  ="%H:%M:%S")
		p.scatter(x='timestamps', y=item, size=1, source=ds)
#		p.line(x='timestamps', y=item, source=ds)
		plots.append(p)
	return plots



def show_plots(list_of_plots):
        show(column(list_of_plots))


filename = 'temperatures_' + dt.datetime.today().strftime('%Y%m%d') + '.csv'
df = pd.read_csv(filename, parse_dates=['timestamps'])
columns = df.columns
plots = plot_dataframe(df, columns)


i = 0


# create a callback that adds a number in a random location
def callback():
    global i

    # BEST PRACTICE --- update .data in one step with a new dict
    new_data = dict()
    new_data['text'] = ds.data['text'] + [str(i)]
    ds.data = new_data

    i = i + 1

# add a button widget and configure with the call back
button = Button(label="Update")
button.on_click(callback)

# put the button and plot in a layout and add to the document
curdoc().add_root(column(plots))
