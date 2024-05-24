#authors Nathan & Perry
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
import numpy as np
import time as theTime

"""
from serial.tools import list_ports
port = list(list_ports.comports())
for p in port:
    print(p.device)


# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = []
ys = []
arduinoSerialData = serial.Serial('/dev/cu.usbmodem1401',2000000)
# This function is called periodically from FuncAnimation
def animate(i, xs, ys):
    mydata = int.from_bytes(arduinoSerialData.read(2),byteorder="big", signed=False)
    print(mydata)
    # Add x and y to lists
    xs.append(dt.datetime.now().strftime('%H:%M:%S.%f'))
    ys.append(mydata)
    # Limit x and y lists to 20 items
    xs = xs[-1000:]
    ys = ys[-1000:]

    # Draw x and y lists
    ax.clear()
    ax.plot(xs, ys)
    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('Data over Time')
    plt.ylabel('Data samples')
# Set up plot to call animate() function periodically
anim = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=0)
plt.show()

'''
Serial = serial.Serial('/dev/cu.usbmodem1401', 2000000)

data = Serial.read(2)
print(data.hex())

'''
"""

#some data up here

class ArduinoData:
    """
    Arduino data stores the voltage and relative time from the live data, this allows for easy processing of the data,
    """
    def __init__(self, voltage: np.int16, time: np.int32):
        self.voltage = voltage
        self.time = time


Livedata = np.zeros(1000, dtype=object)



def FFT():
    print("FFT")



def GUI():

    time= list()
    livetime = 0  

    while time < 10000:
        vals = Livedata
        plt.plot(time, vals)
        plt.show() 
        time.append(livetime)
    print("GUI")
    



from serial.tools import list_ports

def ChoosePort():
    print("\n\n\n")
    print("Please select a port from the list below\n")
    port = list(list_ports.comports())
    for i, p in enumerate(port):
        print(f"{i+1}. {p.device}")
    
    choosenPort = int(input("\nPort: "))
    
    return port[choosenPort-1].device


def FastSerial(Arduino):
    #Fast Serial communications
    RawData = Arduino.read(1)
    if RawData.hex() == "ff":
        #leading byte
        Correctdata = Arduino.read(2)   
        voltage = int.from_bytes(Correctdata, byteorder="big", signed=False) #read two bits convert to int
        time = theTime.time_ns()
        Livedata[1:] = Livedata[:-1]
        Livedata[0] = ArduinoData(voltage, time)
    


def plotData():
    plt.plot(np.arange(1000), [Livedata[i].voltage for i in range(len(Livedata))], linewidth=2)
    plt.show()


class Method():
    def __init__(self) -> None:
        self.myport = ChoosePort()
        self.serialData = serial.Serial(self.myport,2000000)

        #begin GUI???

    def loop(self):
        FastSerial(self.serialData)
        #print(Livedata[0].voltage)
        #update GUI


myProgram = Method()
try:
    while(1):
        myProgram.loop()
except KeyboardInterrupt:
    plotData()
    pass



