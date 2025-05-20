import can
import matplotlib.pyplot as plt
from collections import deque
from dataclasses import dataclass
import time
import numpy as np


@dataclass
class CellData:
    invalid: bool
    value: int


def to_bit_string(message):
    return "".join(f"{byte:08b}" for byte in message)


def extract_bits(bit_string, start, amount):
    return bit_string[start : start + amount]


def parse_message_cell_info(payload_bit_string, cell_count, mux_offset, valid_bit_offset, data_bit_offset, data_bit_length, data_class):
    mux = int(extract_bits(payload_bit_string, 0, 8), 2)
    cells = []
    cell_offset = mux * mux_offset

    for i in range(cell_count):
        valid_bit_pos = valid_bit_offset + i
        data_bit_pos = data_bit_offset + i * data_bit_length
        invalid = bool(int(extract_bits(payload_bit_string, valid_bit_pos, 1)))
        value = int(extract_bits(payload_bit_string, data_bit_pos, data_bit_length), 2)
        cell_number = cell_offset + i
        cells.append((cell_number, data_class(invalid, value)))

    return mux, cells


# Parameters for moving average
ma_window_size = 10  # Adjust as needed for smoothing

# Constant variables
num_cells = 14
num_temp_sensors = 8

# Constants for message parsing
TEMPERATURE_CELL_COUNT = 6
TEMPERATURE_MUX_OFFSET = 6
TEMPERATURE_VALID_BIT_OFFSET = 10
TEMPERATURE_DATA_BIT_OFFSET = 16
TEMPERATURE_DATA_BIT_LENGTH = 8

VOLTAGE_CELL_COUNT = 4
VOLTAGE_MUX_OFFSET = 4
VOLTAGE_VALID_BIT_OFFSET = 8
VOLTAGE_DATA_BIT_OFFSET = 12
VOLTAGE_DATA_BIT_LENGTH = 13

# Initialize figure and subplots
fig, (ax_temp, ax_volt, ax_curr) = plt.subplots(3, 1, sharex=False)

# Temperature bar graph
temp_sensor_positions = np.arange(num_temp_sensors)
cell_temperatures = np.zeros(num_temp_sensors)
temp_bars = ax_temp.bar(temp_sensor_positions, cell_temperatures, color="#00bf63")
ax_temp.set_title("Real-time Temperatures", fontsize=24, fontweight="bold")
ax_temp.set_xlabel("Temp Sensor", fontsize=20)
ax_temp.set_ylabel("Temperature (°C)", fontsize=20)
ax_temp.set_ylim(0, 130)
ax_temp.set_xticks(temp_sensor_positions)
ax_temp.tick_params(axis="both", which="minor", labelsize=20)
ax_temp.grid(False)

# Voltage bar graph
cell_positions = np.arange(num_cells)
cell_voltages = np.zeros(num_cells)
volt_bars = ax_volt.bar(cell_positions, cell_voltages, color="#00bf63")
ax_volt.set_title("Real-time Cell Voltages", fontsize=24, fontweight="bold")
ax_volt.set_xlabel("Cell Number", fontsize=20)
ax_volt.set_ylabel("Voltage (mV)", fontsize=20)
ax_volt.set_ylim(0, 1200)
ax_volt.set_xticks(cell_positions)
ax_volt.tick_params(axis="both", which="minor", labelsize=20)
ax_volt.grid(False)

# Current line graph
time_window = 100  # Number of data points to show in the graph
current_data = deque([0] * time_window, maxlen=time_window)  # Raw current readings
time_stamps = deque(range(-time_window, 0), maxlen=time_window)  # Relative time stamps
(current_line,) = ax_curr.plot(time_stamps, current_data, color="#00bf63", linewidth=4)
ax_curr.set_title("Real-time Current", fontsize=24, fontweight="bold")
ax_curr.set_xlabel("Sample", fontsize=20)
ax_curr.set_ylabel("Current (mA)", fontsize=20)
ax_curr.set_ylim(0, 5000)  # Adjust based on expected current range
ax_curr.grid(True)

# Adjust layout
plt.tight_layout()
plt.show()

bus = can.Bus(interface="ixxat", channel=0, bitrate=500000)

update_interval = 0.1  # Time in seconds between plot updates
last_update_time = 0

try:
    while True:
        message = bus.recv(timeout=1)
        if message and message.arbitration_id == 608:
            payload_bit_string = to_bit_string(message.data)
            mux, cells = parse_message_cell_info(
                payload_bit_string,
                cell_count=TEMPERATURE_CELL_COUNT,
                mux_offset=TEMPERATURE_MUX_OFFSET,
                valid_bit_offset=TEMPERATURE_VALID_BIT_OFFSET,
                data_bit_offset=TEMPERATURE_DATA_BIT_OFFSET,
                data_bit_length=TEMPERATURE_DATA_BIT_LENGTH,
                data_class=CellData,
            )

            for cell_number, cell in cells:
                if cell_number < num_temp_sensors:
                    cell_temperatures[cell_number] = cell.value
                    print(f"Cell {cell_number} temperature (*C): {cell.value}")

        if message and message.arbitration_id == 592:  # Cell voltages
            payload_bit_string = to_bit_string(message.data)

            mux, cells = parse_message_cell_info(
                payload_bit_string,
                cell_count=VOLTAGE_CELL_COUNT,
                mux_offset=VOLTAGE_MUX_OFFSET,
                valid_bit_offset=VOLTAGE_VALID_BIT_OFFSET,
                data_bit_offset=VOLTAGE_DATA_BIT_OFFSET,
                data_bit_length=VOLTAGE_DATA_BIT_LENGTH,
                data_class=CellData,
            )

            for cell_number, cell in cells:
                if cell_number < num_cells:
                    cell_voltages[cell_number] = cell.value
                    print(f"Cell {cell_number} voltage (mV): {cell.value}")

        if message and message.arbitration_id == 1313:  # Current sensor
            payload_bit_string = to_bit_string(message.data)
            current = int(extract_bits(payload_bit_string, 16, 32), 2)
            if current > 300000:
                current = 0
            print(f"Current (mA): {current}")
            current_data.append(current)
            time_stamps.append(time_stamps[-1] + 1)  # Increment time step

        # Update plots only if sufficient time has passed
        if time.time() - last_update_time > update_interval:
            # Update temperature bar chart
            for bar, new_temperature in zip(temp_bars, cell_temperatures):
                bar.set_height(new_temperature)

            # Update voltage bar chart
            for bar, new_voltage in zip(volt_bars, cell_voltages):
                bar.set_height(new_voltage)

            # Update current line chart
            current_line.set_ydata(current_data)
            current_line.set_xdata(time_stamps)
            ax_curr.relim()
            ax_curr.autoscale_view()

            plt.pause(0.05)
            last_update_time = time.time()

except KeyboardInterrupt:
    print("Stopped listening.")
finally:
    plt.ioff()
    plt.show()
    bus.shutdown()
