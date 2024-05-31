#authors Nathan & Perry
import matplotlib.pyplot as plt
import serial
import numpy as np
import time as theTime

from serial.tools import list_ports


import dash
from dash import Dash, dcc, html, Input, Output, callback
from plotly.subplots import make_subplots
import plotly.graph_objects as go


#some data up here

class ArduinoData:
    """
    Arduino data stores the voltage and relative time from the live data, this allows for easy processing of the data,
    """
    def __init__(self, voltage: np.int16, time: np.int32):
        self.voltage = voltage
        self.time = time


Livedata = np.empty(10000, dtype=object)
for i in range (len(Livedata)): Livedata[i] = ArduinoData(0,0) 

def ChoosePort():
    print("\n\n\n")
    print("Please select a port from the list below\n")
    port = list(list_ports.comports())
    for i, p in enumerate(port):
        print(f"{i+1}. {p.device}")
    
    choosenPort = int(input("\nPort: "))
    
    return port[choosenPort-1].device


def listPorts():
    port = list(list_ports.comports())
    portchoice = []
    for p in port:
        portchoice.append(p.device)
    return portchoice


class aquire_data:
    def __init__(self) -> None:
        self.prevTime = theTime.time_ns()/1000
        self.prevData = bytearray([255,0,0])
        self.Arduino = serial.Serial(listPorts()[0],2000000)

    def setPort(self, choice):
        self.Arduino = serial.Serial(choice,2000000)

    def FastSerial(self):
        #Fast Serial communications

        bytesToRead = self.Arduino.inWaiting()

        if bytesToRead > 0 :
            RawData = bytearray(self.Arduino.read(bytesToRead))
            ReadTime = theTime.time_ns()/1000    # To be done as close as possible to reading the data

            RawData = self.prevData + RawData # joins old data to the new
            if not(RawData[0]==255): # it must start with ff, if not shift to the next ff start
                try:
                    RawData = RawData[RawData.index(b'\xff'):]
                except ValueError: # when the data is corrupted return and don't process it. next buffer should work
                    return 
            #debug
            #print(RawData)

            for i in range(round(len(RawData)/3)):
                if RawData[(3*i)] == 255 and (RawData[(3*i)+1]>>4) == 0:
                    voltage = int.from_bytes(RawData[(3*i)+1:(3*i)+3], byteorder="big", signed=False)
                    time = self.prevTime +  i * (3 * (ReadTime - self.prevTime)/ (len(RawData)))

                    if (voltage < 4096 and voltage > 0 and (voltage - Livedata[1].voltage) < 2000):
                        #Shift Data in
                        Livedata[1:] = Livedata[:-1]
                        Livedata[0] = ArduinoData(voltage, time)

                    else:
                        #Data is corrupt ignore it. this will cause gaps
                        pass 
                        
                else: #shift data until we reach the next valid point
                    try:
                        RawData = RawData[RawData.index(b'\xff'):]
                    except ValueError: # when the data is corrupted return and don't process it. next buffer should work
                        pass
                    


            self.prevData = RawData[round(len(RawData)/3)*3:]

            self.prevTime = ReadTime

        return  
        
data_update = aquire_data()





external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
comPorts = listPorts()

app = Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    html.Div([
        html.H4('ArduinoScope Live Feed'),
        html.Div(id='live-update-text'),
        dcc.Dropdown(comPorts, comPorts[0], id='comPortSelection'),
        dcc.Slider(min=100, max=10000, marks=None, value=1000, id='my-slider'),
        dcc.Graph(id='live-update-graph', style={'height': '100%'}),
        dcc.Interval(
            id='interval-component',
            interval=50, # in milliseconds
            n_intervals=0
        )
    ], style={'height' : '100%'}), style={'height' : '80vh'}
)

"""
@callback(Output('live-update-text', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    lon, lat, alt = satellite.get_lonlatalt(datetime.datetime.now())
    style = {'padding': '5px', 'fontSize': '16px'}
    return [
        html.Span('Longitude: {0:.2f}'.format(lon), style=style),
        html.Span('Latitude: {0:.2f}'.format(lat), style=style),
        html.Span('Altitude: {0:0.2f}'.format(alt), style=style)
    ]
"""


@callback(Input('comPortSelection', 'value'))
def update_com_port(comPort):
    data_update.setPort(comPort)
    return



# Multiple components can update everytime interval gets fired.
@callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'),
              Input('my-slider', 'value'))
def update_graph_live(n, width):
    widthAdjust = 10000 - round(width)
    data_update.FastSerial()
    fig = make_subplots(rows=2, cols=1, row_heights=[2,2])
    fig.add_trace(
        go.Line(x = [Livedata[widthAdjust + i].time for i in range(len(Livedata)- widthAdjust)], y = [Livedata[widthAdjust + i].voltage for i in range(len(Livedata) - widthAdjust)]),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Line(x = [Livedata[i].time for i in range(len(Livedata))], y = [Livedata[i].voltage for i in range(len(Livedata))]),
        row=2, col=1
    )
    
    return fig


def plotData():
    plt.plot([Livedata[i].time for i in range(len(Livedata))], [Livedata[i].voltage for i in range(len(Livedata))], linewidth=2)
    plt.show()

if __name__ == '__main__':
    app.run(debug=True)







