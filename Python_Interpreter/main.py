import matplotlib.pyplot as plt
import numpy as np
import serial
from scipy.stats import norm
import seaborn as sns
from IPython.display import clear_output

#Setting Print Options For The Terminal
np.set_printoptions(precision=4, linewidth=170, edgeitems=10, floatmode='fixed', sign=' ')
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams.update({'font.size': 13})

#Setting COM options
COM_PORT = 'COM19'
BAUD_RATE = 9600
NUM_SAMPLES = 120  # 1 minute
BYTES_PER_PACKET = 6
BYTE_ORDER = 'little'  # or 'big'
SAMPLING_FREQ = 1  # Hz

RNG_array = np.zeros((NUM_SAMPLES, 3), dtype=float)
X_axis = np.linspace(0, (NUM_SAMPLES - 1) / SAMPLING_FREQ, NUM_SAMPLES)
global_counter = -1

# Library
SENSOR_LIST = ['RNG']
AXIS_LIST = ['R']
DATATYPE_LIST = ['Mag']
ARR = [RNG_array]
measurement = []
read_flag = False
def rxDataPoint():
    global global_counter
    global ser
    global measurement
    global read_flag
    global_counter += 1
    #Read the first ine
    rxData = ser.read(1)
    int_val = int.from_bytes(rxData, "big")
    #Denotes the start of measurements
    if int_val==ord('S'):
        print("Yes")
        read_flag = True
        measurement = []
    #Denotes the end of measurements
    elif int_val==ord('0'):
        print(measurement)
        read_flag = False
        measurement = []
    else:
        measurement.append(int_val)
    print(int_val)
    # RNG_array[global_counter][0] = rxData[0]
    # RNG_array[global_counter][1] = rxData[1]
    # RNG_array[global_counter][2] = rxData[2]


if __name__ == "__main__":
    plt.figure(figsize=(6.5, 7.2))
    plt.ylabel("Magnetometer\n" + DATATYPE_LIST[0] + "\n")
    plt.tick_params(labelcolor='w', top=False, bottom=False, left=False, right=False)

    plt.xlabel("Time (s)")
    # fig.tight_layout()
    plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
    plt.grid(True)
    try:
        # Setup the serial
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=None, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS)
        print("Connected to " + COM_PORT + ".")
    except:
        print("Could not connect to the device.")
        exit()

    lines = []
    for i in range(NUM_SAMPLES):
        rxDataPoint()
        # remove old lines
        # for line in lines:
        #     if len(line) > 0:
        #         line.pop(0).remove()
        # for j in range(3):
        #     # Select colour
        #     if j == 0:
        #         label = 'X'
        #         color = 'g'
        #     elif j == 1:
        #         color = 'b'
        #         label = 'Y'
        #     else:
        #         color = 'r'
        #         label = 'Z'
        #     lines.append(plt.plot(X_axis[:i], RNG_array[:i, j], color, label=label, alpha=0.8))
        #     if j == 2:
        #         plt.legend(loc='upper right')
        # plt.grid(True)
        plt.pause(0.33)

    print(RNG_array)
    plt.close()
    data_normal = []
    for i in range(0,len(RNG_array)):
        for j in range(0,len(RNG_array[i])):
            data_normal.append(RNG_array[i][j])
    data_normal = np.array(data_normal)
    ax = sns.distplot(data_normal,
                      bins=256,
                      kde=True,
                      color='black',
                      hist_kws={"linewidth": 15, 'alpha': 1, 'color':'skyblue'})
    ax.set(xlabel='Normal Distribution', ylabel='Frequency')
    plt.savefig("PDF_data.pdf")
    plt.show()