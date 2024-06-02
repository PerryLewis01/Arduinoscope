#authors Nathan & Perry
import serial
import time
import threading
from collections import deque
from serial.tools import list_ports
import numpy as np

from dash import Dash, dcc, html, Input, Output, callback
from plotly.subplots import make_subplots
import plotly.graph_objects as go


"""
Calibration Data


time_constant = 28.20us

+5v = 917
+2V = 1402
GND = 1710
-2V = 2032
-5.383V = 2557

this is incredibly linier

input to voltage

voltage = -157.8630 * input + 1711.5077


----------------------
Colour's

#ffffff
#3a86ff
#8338ec
#ff006e
#fb5607
#ffbe0b
#8d99ae
#353535

"""
#28.20us
time_constant = 2.820e-05

voltage_adjustment = -6.33416107e-03
voltage_offset = 1.084096e01


class DataStorage:
    def __init__(self, max_size=10000):
        self.data = deque(maxlen=max_size)
        self.max_size = max_size
        
        #fill with innit data
        for i in range(max_size):
            self.data.append((0, i*time_constant))

    def add_data(self, packet, time_of_packet):
        self.data.append((packet, time_of_packet))

    def get_data(self):
        return list(self.data)


def read_from_serial(arduino, buffer, timestamps, lock, new_data_event):
    while True:
        try:
            bytes_to_read = arduino.in_waiting
            if bytes_to_read > 0:
                raw = arduino.read(bytes_to_read)
                current_time = time.time_ns() / 1000
                with lock:
                    buffer.extend(raw)
                    timestamps.extend([current_time] * bytes_to_read)
                new_data_event.set()


        except Exception as e:
            print(f"Serial read error: {e}")
            break

def process_data(buffer, timestamps, lock, new_data_event, storage_A, storage_B):
    while True:
        new_data_event.wait()  # Wait for new data to be read
        new_data_event.clear()
        
        with lock:
            while len(buffer) >= 3:
                start_index = buffer.find(b'\xff')
                if start_index == -1:
                    break

                if start_index <= len(buffer) - 3:
                    packet = buffer[start_index:start_index+3]
                    packet_timestamps = timestamps[start_index:start_index+3]
                    if len(packet) == 3:
                        arrival_time = packet_timestamps[0]
                        time_of_packet = packet_timestamps[0] + (arrival_time - packet_timestamps[0]) / len(packet)
                        voltage_input = int.from_bytes(packet[1:], byteorder='big', signed=False) & 0xfff
                        
                        voltage = (voltage_adjustment * voltage_input) + voltage_offset
                        if voltage_input > 0 and voltage_input < 4096:
                            if packet.hex()[2] == '0':
                                storage_A.add_data(voltage, time_of_packet)
                            elif packet.hex()[2] == 'f':
                                storage_B.add_data(voltage, time_of_packet)

                        del buffer[:start_index+3]
                        del timestamps[:start_index+3]
                        
                            
                else:
                    break




def listPorts():
    port = list(list_ports.comports())
    portchoice = []
    for p in port:
        portchoice.append(p.device)
    return portchoice




### Dash App

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
comPorts = listPorts()

arduino = serial.Serial(comPorts[2], 2000000)
storage_a = DataStorage()
storage_b = DataStorage()


app = Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    html.Div([
        html.H4('ArduinoScope Live Feed', style={'text-align': 'center'}),
        html.P(f'Port : {comPorts[2]}'),
        html.Div([

            html.Div([

                dcc.Slider(min=20, max=4990, marks={20:'fast', 50: '',100:'a', 200:'b', 400:'c', 600:'d', 800:'e', 1000:'f', 2000:'g', 4000:'h', 4990:'slow',}, value=1000, id='my-slider'),
                html.Div([
                    dcc.Graph(id='live-update-graph', style={'height': '100%'}),
                    dcc.Interval(
                        id='interval-component',
                        interval=1000/25, # in milliseconds
                        n_intervals=0
                    )
                ], style={'height' : '80vh', 'top':'-1vh', 'position': 'relative'}),
            ]),

            html.Div([
                html.Div([
                    html.Button('Start / Stop', id='start-button', n_clicks=0,style={'background-color': 'green', 'color': 'white', ':hover': {'background-color': '#fb5607', 'color': 'white'}}),
                    html.Div([
                        html.P('Trigger'),
                        dcc.Input(id='trigger-value', min=-10, max = 10, step = 0.1, placeholder=0, value=0, type='number')
                    ], style={'margin-top': '10px', 'margin-bottom': '10px'}),

                    html.Div([
                        html.Button('   Rise/Fall   ', id='rise-fall-button', n_clicks=0,style={'background-color': 'green', 'color': 'white', ':hover': {'background-color': '#fb5607', 'color': 'white'}})
                    ], style={'margin-top': '10px', 'margin-bottom': '10px'}),

                    html.Div([
                        html.Button('Channel 1', id='channel-1-button', n_clicks=0,style={'background-color': '#3a86ff', 'color': 'white', 'padding':'5px', 'margin':'10px', 'border-radius':'2px'})
                    ], style={'margin-top': '10px', 'margin-bottom': '10px'}),

                    html.Div([ 
                        html.Button('Channel 2', id='channel-2-button', n_clicks=0,style={'background-color': '#8d99ae', 'color': 'white', 'padding':'5px', 'margin':'10px', 'border-radius':'2px'})
                    ], style={'margin-top': '10px', 'margin-bottom': '10px'}),

                    html.Div([
                        html.Button('Toggle\nChannel', id='channel-toggle-button', n_clicks=0,style={'background-color': 'green', 'color': 'white', ':hover': {'background-color': '#fb5607', 'color': 'white'}})
                    ], style={'margin-top': '10px', 'margin-bottom': '10px'}),
                    

                ],style={'display':'flex', 'flex-direction':'column', 'justify-content':'baseline', 'align-items':'baseline', 'height':'15vh'} ,id='input-bar'),

            ])
        ], style={'display':'grid', 'grid-template-columns':"8fr 2fr", 'grid-gap':'1vw', 'height':'90vh'}),
        html.P(f'{(1/time_constant) //2} MHz max bandwidth')
    ], style={'height' : '100%'}), style={'height' : '90vh'}
)




def GUI():
    """Runs the Dash app"""
    app.run_server(debug=False, port=8050)

def main():
    """
    Main function
    
    Reads data from the Arduino and processes it in real-time.

    The function also plots the data in real-time using Plotly.
    
    """
    buffer = bytearray()
    timestamps = []
    lock = threading.Lock()
    new_data_event = threading.Event()
    

    try:

        # Create a new thread for the serial read and processing and GUI
        reader_thread = threading.Thread(target=read_from_serial, args=(arduino, buffer, timestamps, lock, new_data_event))
        processor_thread = threading.Thread(target=process_data, args=(buffer, timestamps, lock, new_data_event, storage_a, storage_b))
        GUI_thread = threading.Thread(target=GUI)

        reader_thread.start()
        processor_thread.start()
        GUI_thread.start()
        


        reader_thread.join()
        processor_thread.join()
        GUI_thread.join()

    except KeyboardInterrupt:
        # Clean up when the user presses Ctrl+C
        pass
    finally:
        arduino.close()

    # Optionally, do something with the stored data
    data_points = storage_a.get_data()
    print(data_points[:100])  # Print the first 10 data points as an example





@app.callback(
    Output('rise-fall-button', 'style'),
    Input('rise-fall-button', 'n_clicks')
)
def update_button1_color(n_clicks):
    if n_clicks % 2 == 0:
        return {'display':'inline','background-color': 'green', 'color': 'white', ':hover': {'background-color': '#fb5607', 'color': 'white'}}
    else:
        return {'display':'inline','background-color': 'red', 'color': 'white', ':hover': {'background-color': '#fb5607', 'color': 'white'}}

LiveData = np.empty((10000,2), dtype=object)


@app.callback(
    Output('start-button', 'style'),
    Input('start-button', 'n_clicks')
)
def update_button2_color(n_clicks):
    if n_clicks % 2 == 0:
        return {'display':'inline','background-color': 'green', 'color': 'white', ':hover': {'background-color': '#fb5607', 'color': 'white'}}
    else:
        return {'display':'inline','background-color': 'red', 'color': 'white', ':hover': {'background-color': '#fb5607', 'color': 'white'}}

@app.callback(
    Output('channel-1-button', 'style'),
    Output('channel-2-button', 'style'),
    Input('channel-toggle-button', 'n_clicks')
)
def update_button3_color(n_clicks, arduino = arduino):
    '''
    T | A B
    -------------
    0 | 1 0
    1 | 0 1
    2 | 1 1
    3 | 0 0
    '''
    arduino.write(b'\x42')
    if n_clicks % 4 == 0:
        return {'display':'inline','background-color': '#3a86ff', 'color': 'white'} , {'display':'inline','background-color': '#8d99ae', 'color': 'white'}
    elif n_clicks % 4 == 1:
        return {'display':'inline','background-color': '#8d99ae', 'color': 'white'} , {'display':'inline','background-color': '#ff006e', 'color': 'white'}
    elif n_clicks % 4 == 2:
        return {'display':'inline','background-color': '#8d99ae', 'color': 'white'} , {'display':'inline','background-color': '#8d99ae', 'color': 'white'}
    elif n_clicks % 4 == 3:
        return {'display':'inline','background-color': '#3a86ff', 'color': 'white'} , {'display':'inline','background-color': '#ff006e', 'color': 'white'}
    else:
        return {'display':'inline','background-color': '#ffbe0b', 'color': 'white'}, {'display':'inline','background-color': '#ffbe0b', 'color': 'white'}



LiveData_a = np.empty((10000,2), dtype=object)
LiveData_a = np.empty((10000,2), dtype=object)

def trigger(input_data, width_output, trigger_value, trigger_rise = True):
    #Triggers on either rising or falling edge at point closes to the trigger value including some buffer so it can be displayed
    assert len(input_data) > width_output*2
    
    #https://stackoverflow.com/questions/50365310/python-rising-falling-edge-oscilloscope-like-trigger
    if trigger_rise:
        sign = input_data[width_output//2:-width_output//2] >= trigger_value
        pos = np.where(np.convolve(sign, [1,-1])==1)[0][0]
        return pos
    else:
        sign = input_data[width_output//2:-width_output//2] >= trigger_value
        pos = np.where(np.convolve(sign, [1,-1])==-1)[0][0]
        return pos
    



# Graph Update each frame
@callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'),
              Input('my-slider', 'value'),
              Input('start-button', 'n_clicks'),
              Input('trigger-value', 'value'),
              Input('rise-fall-button', 'n_clicks'),
              Input('channel-toggle-button', 'n_clicks'))
def update_graph_live(n, width, Start_Stop, trigger_value, Rise_Fall, Channel_Toggle):
    # if Start, update the data
    if Start_Stop % 2 == 0:
        LiveData_a = np.array(storage_a.get_data()[:], dtype=object)
        LiveData_b = np.array(storage_b.get_data()[:], dtype=object)

    # Triggering, get index of the startpoint from trigger
    Rise_Fall_bool = (Rise_Fall % 2 == 0)
    trigger_index = trigger(LiveData_a[:, 0], width, trigger_value, trigger_rise=Rise_Fall_bool)
    start_index = trigger_index

    # Update the graph
    fig = make_subplots(rows=2, cols=1, row_heights=[2,2])
    if Channel_Toggle % 4 == 0 or Channel_Toggle % 4 == 3:
        fig.add_trace(
            go.Scatter(mode="lines",x = np.arange(len(LiveData_a[start_index: start_index+width, 1]))* time_constant, y = list(LiveData_a[start_index:start_index+width, 0]), line = dict(color = '#3a86ff')),
            row=1, col=1
        )
    if Channel_Toggle % 2 == 1 or Channel_Toggle % 4 == 3:
        fig.add_trace(
            go.Scatter(mode="lines",x = np.arange(len(LiveData_b[start_index: start_index+width, 1]))* time_constant, y = list(LiveData_b[start_index:start_index+width, 0]), line = dict(color = '#ff006e')),
            row=1, col=1
        )
    #display trigger point
    fig.add_trace(
        go.Scatter(mode='markers', y = [trigger_value], x = [(width//2) * time_constant], marker = dict(size = 10, color = '#ffbe0b', opacity = 0.9)),
        row=1, col=1
    )
    
    #fft trace
    if Channel_Toggle % 4 == 0 or Channel_Toggle % 4 == 3:
        fig.add_trace(
            go.Scatter(mode='lines', x = np.abs( np.fft.fftfreq( len(LiveData_a[:, 1]), d=time_constant )),  y = np.abs( np.fft.fft(LiveData_a[:, 0])), line = dict(color = '#3a86ff')),
            row=2, col=1
        )
    if Channel_Toggle % 4 == 1 or Channel_Toggle % 4 == 3:
        fig.add_trace(
            go.Scatter(mode='lines', x = np.abs( np.fft.fftfreq( len(LiveData_b[:, 1]), d=time_constant )),  y = np.abs( np.fft.fft(LiveData_b[:, 0])), line = dict(color = '#ff006e')),
            row=2, col=1
        )

    fig.update_xaxes(title_text="Time", row=1, col=1)
    fig.update_yaxes(title_text="Voltage", row=1, col=1)
    fig.update_xaxes(title_text="Freq", type='log', row=2, col=1)
    fig.update_yaxes(title_text="Magnitude", type='log', range = [np.log(0.1), np.log(10000)], row=2, col=1)
    fig.update_traces(showlegend = False)
    return fig

if __name__ == "__main__":
    main()
