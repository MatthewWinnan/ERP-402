# Author: C.F. Wagner
# Data created: 2021/09/06
# Filename: ERP420-Interpreter.py

import matplotlib.pyplot as plt
import numpy as np
import serial

np.set_printoptions(precision=4, linewidth=170, edgeitems=10, floatmode='fixed', sign=' ')
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams.update({'font.size': 13})

REAL_TIME = False
ZOOMED_PLOT = True
COM_PORT = 'COM20'
NUM_SAMPLES = 3000  # 1 minute
BYTES_PER_PACKET = 7
BYTE_ORDER = 'little'  # or 'big'
SAMPLING_FREQ = 50  # Hz

if REAL_TIME:
    NUM_SAMPLES = 145  # 30 seconds
    SAMPLING_FREQ = 5

SCALE_M = 0.14 / 1000  # gauss/LSB
SCALE_G = 8.75 / 1000  # dps/LSB
SCALE_A = 0.061 / 1000 * 9.8066  # m/s/s/LSB

# Header values
HEADER_M = 'M'
HEADER_G = 'G'
HEADER_A = 'A'

Mag_arr = np.zeros((NUM_SAMPLES, 3), dtype=float)
Gyro_arr = np.zeros((NUM_SAMPLES, 3), dtype=float)
Acc_arr = np.zeros((NUM_SAMPLES, 3), dtype=float)
X_axis = np.linspace(0, (NUM_SAMPLES - 1) / SAMPLING_FREQ, NUM_SAMPLES)
global_counter = -1

# Library
SENSOR_LIST = ['Magnetometer', 'Gyroscope', 'Accelerometer']
AXIS_LIST = ['X', 'Y', 'Z']
DATATYPE_LIST = ['$gauss$', "$deg/s$", "$m/s^2$"]
ARR = [Mag_arr, Gyro_arr, Acc_arr]


def rxDataPoint():
    global global_counter
    global ser
    global_counter += 1

    rxData = ser.read(BYTES_PER_PACKET * 3)
    if global_counter == 0:
        print("Readings started.")
        print(rxData)
    # Split in 3 and extract the data
    if rxData[0] != ord(HEADER_M):
        print("Byte packet missed at:", global_counter, rxData)
        return

    Mag_arr[global_counter][0] = int.from_bytes(rxData[1:3], byteorder=BYTE_ORDER, signed=True) * SCALE_M
    Mag_arr[global_counter][1] = int.from_bytes(rxData[3:5], byteorder=BYTE_ORDER, signed=True) * SCALE_M
    Mag_arr[global_counter][2] = int.from_bytes(rxData[5:7], byteorder=BYTE_ORDER, signed=True) * SCALE_M

    Gyro_arr[global_counter][0] = int.from_bytes(rxData[8:10], byteorder=BYTE_ORDER, signed=True) * SCALE_G
    Gyro_arr[global_counter][1] = int.from_bytes(rxData[10:12], byteorder=BYTE_ORDER, signed=True) * SCALE_G
    Gyro_arr[global_counter][2] = int.from_bytes(rxData[12:14], byteorder=BYTE_ORDER, signed=True) * SCALE_G

    Acc_arr[global_counter][0] = int.from_bytes(rxData[15:17], byteorder=BYTE_ORDER, signed=True) * SCALE_A
    Acc_arr[global_counter][1] = int.from_bytes(rxData[17:19], byteorder=BYTE_ORDER, signed=True) * SCALE_A
    Acc_arr[global_counter][2] = int.from_bytes(rxData[19:21], byteorder=BYTE_ORDER, signed=True) * SCALE_A


if __name__ == "__main__":
    if ZOOMED_PLOT:
        fig = plt.figure(figsize=(6.5 * 2, 7.2))
    else:
        fig = plt.figure(figsize=(6.5, 7.2))

    ax = fig.add_subplot(111)
    axs = [fig.add_subplot(311), fig.add_subplot(312), fig.add_subplot(313)]
    if ZOOMED_PLOT:
        axs[0].set_ylim([-0.25, 0.8])
        axs[1].set_ylim([-0x8000 * SCALE_G, 0x8000 * SCALE_G])
        axs[2].set_ylim([-0x8000 * SCALE_A, 0x8000 * SCALE_A])
    else:
        axs[0].set_ylim([-0x8000 * SCALE_M, 0x8000 * SCALE_M])
        axs[1].set_ylim([-0x8000 * SCALE_G, 0x8000 * SCALE_G])
        axs[2].set_ylim([-0x8000 * SCALE_A, 0x8000 * SCALE_A])

    axs[0].set_ylabel("Magnetometer\n" + DATATYPE_LIST[0] + "\n")
    axs[1].set_ylabel("Gyroscope\n" + DATATYPE_LIST[1])
    axs[2].set_ylabel("Accelerometer\n" + DATATYPE_LIST[2])

    ax.spines['right'].set_color('none')
    ax.spines['left'].set_color('none')
    ax.spines['bottom'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.tick_params(labelcolor='w', top=False, bottom=False, left=False, right=False)

    ax.set_xlabel("Time (s)")
    axs[0].tick_params(axis='x', colors='none')
    axs[1].tick_params(axis='x', colors='none')

    fig.subplots_adjust(top=0.979, bottom=0.071, left=0.152, right=0.979, wspace=0, hspace=0.055)
    # fig.tight_layout()

    for i in range(3):
        axs[i].set_xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
        axs[i].grid(True)

    try:
        # Setup the serial
        ser = serial.Serial(COM_PORT, 115200, timeout=None, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS)
        print("Connected to " + COM_PORT + ".")
    except:
        print("Could not connect to the device.")
        exit()

    lines = []
    for i in range(NUM_SAMPLES):
        rxDataPoint()
        if REAL_TIME:
            print("Mag:", Mag_arr[i], "Gyro:", Gyro_arr[i], "Acc:", Acc_arr[i])
            # remove old lines
            for line in lines:
                if len(line) > 0:
                    line.pop(0).remove()
            for j in range(3):
                # Select colour
                if j == 0:
                    label = 'X'
                    color = 'g'
                elif j == 1:
                    color = 'b'
                    label = 'Y'
                else:
                    color = 'r'
                    label = 'Z'
                lines.append(axs[0].plot(X_axis[:i], Mag_arr[:i, j], color, label=label, alpha=0.8))
                if i == 0 and j == 2:
                    axs[0].legend(loc='upper right')
                lines.append(axs[1].plot(X_axis[:i], Gyro_arr[:i, j], color, label=label, alpha=0.8))
                lines.append(axs[2].plot(X_axis[:i], Acc_arr[:i, j], color, label=label, alpha=0.8))

            plt.pause(0.00001)

    if REAL_TIME:
        plt.savefig("Live_XYZ_data.pdf")
        plt.show()

    if not REAL_TIME:
        # Get stats
        for i in range(3):
            # Select colour
            if i == 0:
                label = 'X'
                color = 'g'
            elif i == 1:
                color = 'b'
                label = 'Y'
            else:
                color = 'r'
                label = 'Z'
            axs[0].plot(X_axis, Mag_arr[:, i], color, label=label, alpha=0.8)
            axs[1].plot(X_axis, Gyro_arr[:, i], color, label=label, alpha=0.8)
            axs[2].plot(X_axis, Acc_arr[:, i], color, label=label, alpha=0.8)
        axs[0].legend(loc='upper right')
        plt.savefig("XYZ_data.pdf")
        plt.show()

        # Histograms

        for s in range(3):
            for a in range(3):
                # print(ARR[s][:, a])
                n, bins, patches = plt.hist(ARR[s][:, a], bins=25, color='c', rwidth=0.85)
                plt.xlabel(DATATYPE_LIST[s])
                plt.ylabel("Frequency")
                max_freq = n.max()
                plt.grid(axis='y', alpha=0.65)
                plt.ylim(ymax=np.ceil(max_freq * 1.1))

                plt.text(bins[-1] - (bins[-1] - bins[0]) * 0.26, np.ceil(max_freq * 1.1) * 0.86,
                         "$\mu=" + str(np.round(np.mean(ARR[s][:, a]), decimals=4)) + "$\n$\sigma = " + str(
                             np.round(np.std(ARR[s][:, a]), decimals=4)) + "$")
                plt.savefig("Hist_" + SENSOR_LIST[s] + "_" + AXIS_LIST[a] + ".pdf")
                plt.show()

    # Save np array
    for s in range(3):
        np.save("Measurement_" + SENSOR_LIST[s], ARR[s])