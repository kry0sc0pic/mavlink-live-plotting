# imports
from pymavlink import mavutil


# connection
connection = mavutil.mavlink_connection('COM9',baud=57600)  # Adjust connection string as needed

# Wait for a heartbeat
print("Waiting for heartbeat...")
connection.wait_heartbeat()
print(f"Heartbeat received from system {connection.target_system}, component {connection.target_component}")

frequency_hz = 10
interval_us = int(1e6 / frequency_hz)  # Convert Hz to microseconds



"""
Fields:
time_boot_ms	uint32_t	ms	    Timestamp (time since system boot).
xacc	        int16_t	    mG	    X acceleration
yacc	        int16_t	    mG	    Y acceleration
zacc	        int16_t	    mG	    Z acceleration
xgyro	        int16_t	    mrad/s	Angular speed around X axis
ygyro	        int16_t	    mrad/s	Angular speed around Y axis
zgyro	        int16_t	    mrad/s	Angular speed around Z axis
xmag	        int16_t	    mgauss	X Magnetic field
ymag	        int16_t	    mgauss	Y Magnetic field
zmag	        int16_t	    mgauss	Z Magnetic field
temperature ++	int16_t	    cdegC	Temperature, 0: IMU does not provide temperature values. If the IMU is at 0C it must send 1 (0.01C).
"""


# send scaled
connection.mav.command_long_send(
    connection.target_system,
    connection.target_component,
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # Command ID
    0,  # Confirmation
    mavutil.mavlink.MAVLINK_MSG_ID_SCALED_IMU ,  # Message ID for SCALED_IMU
    interval_us,  # Interval in microseconds
    0, 0, 0, 0, 0  # Unused parameters
)

connection.mav.command_long_send(
    connection.target_system,
    connection.target_component,
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # Command ID
    0,  # Confirmation
    mavutil.mavlink.MAVLINK_MSG_ID_SCALED_IMU2 ,  # Message ID for SCALED_IMU
    interval_us,  # Interval in microseconds
    0, 0, 0, 0, 0  # Unused parameters
)

connection.mav.command_long_send(
    connection.target_system,
    connection.target_component,
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # Command ID
    0,  # Confirmation
    mavutil.mavlink.MAVLINK_MSG_ID_SCALED_IMU3 ,  # Message ID for SCALED_IMU
    interval_us,  # Interval in microseconds
    0, 0, 0, 0, 0  # Unused parameters
)


try:
    while True:
        msg = connection.recv_match(blocking=True)
        if msg:
            print("Data:",msg.to_dict())
except KeyboardInterrupt:
    print("Stopped")