from pymavlink import mavutil
import numpy as np
import threading
from fastapi import FastAPI, WebSocket
import uvicorn
import asyncio
from collections import deque

ZERO_READING = {
    'AccX': 0.0,
    'AccY': 0.0,
    'AccZ': 0.0,
    'GyrX': 0.0,
    'GyrY': 0.0,
    'GyrZ': 0.0,
    'MagX': 0.0,
    'MagY': 0.0,
    'MagZ': 0.0,
    'TimeS': 0.0,
    'AccMagnitude': 0.0,
    'MagMagnitude': 0.0,
    'Pitch': 0.0,
    'Roll': 0.0
}
SCALED_IMU_0 = [ZERO_READING.copy(),]
SCALED_IMU_1 = [ZERO_READING.copy(),]
SCALED_IMU_2 = [ZERO_READING.copy(),]
LAST_LEN_0 = len(SCALED_IMU_0)
LAST_LEN_1 = len(SCALED_IMU_1)
LAST_LEN_2 = len(SCALED_IMU_2)
PORT = "COM10"

MAVLINK_STARTED = False
READINGS_ADDED = []

def mavlink_task():
    global SCALED_IMU_0
    global SCALED_IMU_1
    global SCALED_IMU_2
    global READINGS_ADDED
    # connection
    connection = mavutil.mavlink_connection(PORT,baud=57600)  # Adjust connection string as needed

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
        
            if msg and (msg_type:= msg.get_type()) in ["SCALED_IMU","SCALED_IMU2","SCALED_IMU3"]:
                data = msg.to_dict()
                converted = {}
                # Convert values and rename variables to match ardupilog / matlab
                converted['AccX'] = round(data['xacc'] * 9.80665 / 1000 ,2)# Convert to m/s^2
                converted['AccY'] = round(data['yacc'] * 9.80665 / 1000,2) # Convert to m/s^2
                converted['AccZ'] = round(data['zacc'] * 9.80665 / 1000,2) # Convert to m/s^2
                converted['GyrX'] = round(data['xgyro'] / 1000,2) # Convert to rad/s
                converted['GyrY'] = round(data['ygyro'] / 1000,2) # Convert to rad/s
                converted['GyrZ'] = round(data['zgyro'] / 1000,2) # Convert to rad/s
                converted['MagX'] = round(data['xmag'],2) # Keep in mgauss
                converted['MagY'] = round(data['ymag'],2) # Keep in mgauss
                converted['MagZ'] = round(data['zmag'],2) # Keep in mgauss
                converted['TimeS'] = round(data['time_boot_ms'] / 1000,2) # Convert to s
                converted['AccMagnitude'] = round(np.linalg.norm([converted['AccX'],converted['AccY'],converted['AccZ']]),2)
                converted['MagMagnitude'] = round(np.linalg.norm([converted['MagX'],converted['MagY'],converted['MagZ']]),2)
                converted['Pitch'] = round(np.rad2deg(np.arctan((-1 * converted['AccX'])/((div_result := (np.sqrt((np.square(converted['AccY']) + np.square(converted['AccZ']))))) if (np.sqrt((np.square(converted['AccY']) + np.square(converted['AccZ'])))) != 0 else 0.001))),2)
                converted['Roll'] = round(np.rad2deg(np.arctan(converted['AccY']/(converted['AccZ'] if converted['AccZ'] != 0 else 0.001))),2)

                if msg_type == "SCALED_IMU":
                    SCALED_IMU_0.append(converted)
                    if len(SCALED_IMU_0) == 1 and 0 in READINGS_ADDED:
                        SCALED_IMU_0.pop(0)
                        READINGS_ADDED.append(0)
                   
                elif msg_type == "SCALED_IMU2":
                    SCALED_IMU_1.append(converted)
                    if len(SCALED_IMU_1) == 1 and 1 in READINGS_ADDED:
                        SCALED_IMU_1.pop(0)
                        READINGS_ADDED.append(1)

                elif msg_type == "SCALED_IMU3":
                    SCALED_IMU_2.append(converted)
                    if len(SCALED_IMU_2) == 1 and 2 in READINGS_ADDED:
                        SCALED_IMU_2.pop(0)
                        READINGS_ADDED.append(2)

    except KeyboardInterrupt:
        print("Stopped")

def start_mavlink_task():
    global MAVLINK_STARTED
    if MAVLINK_STARTED:
        return
    t = threading.Thread(target=mavlink_task)
    # st.scriptrunner.add_script_ctx(t)
    t.start()
    MAVLINK_STARTED = True

def stop_mavlink_task():
    global MAVLINK_STARTED
    MAVLINK_STARTED = False

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global LAST_LEN_0
    global LAST_LEN_1
    global LAST_LEN_2
    await websocket.accept()
    while True:
        if len(SCALED_IMU_0) > LAST_LEN_0:
            LAST_LEN_0 = len(SCALED_IMU_0)
            await websocket.send_json({
                "channel": "IMU0",
                "data": SCALED_IMU_0[-1]
            })
        
        if len(SCALED_IMU_1) > LAST_LEN_1:
            LAST_LEN_1 = len(SCALED_IMU_1)
            await websocket.send_json({
                "channel": "IMU1",
                "data": SCALED_IMU_1[-1]
            })

        if len(SCALED_IMU_2) > LAST_LEN_2:
            LAST_LEN_2 = len(SCALED_IMU_2)
            await websocket.send_json({
                "channel": "IMU2",
                "data": SCALED_IMU_2[-1]
            })
        
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    start_mavlink_task()
    try:
        uvicorn.run(app=app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        stop_mavlink_task()
        print("Stopped")