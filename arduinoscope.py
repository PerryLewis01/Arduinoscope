#authors Nathan & Perry
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
import numpy as np
import datetime as dt

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


#some data up here

Livedata = np.zeros(100000)



def FFT():
    print("FFT")





def GUI():
    print("GUI")




def FastSerial():
    print("Serial Coms")


