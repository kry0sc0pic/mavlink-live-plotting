import aiohttp
from collections import deque, defaultdict
import pandas as pd
from functools import partial
WS_CONN = "ws://localhost:8000/ws"

# SCALED_IMU = deque([{},]*100, maxlen=100)
IMU_ACC_X = deque([0,]*100, maxlen=100)
IMU_ACC_Y = deque([0,]*100, maxlen=100)
IMU_ACC_Z = deque([0,]*100, maxlen=100)
IMU_ACC_MAG = deque([0,]*100, maxlen=100)
IMU_GYR_X = deque([0,]*100, maxlen=100)
IMU_GYR_Y = deque([0,]*100, maxlen=100)
IMU_GYR_Z = deque([0,]*100, maxlen=100)
IMU_MAG_X = deque([0,]*100)
IMU_MAG_Y = deque([0,]*100)
IMU_MAG_Z = deque([0,]*100)
IMU_MAG_MAG = deque([0,]*100)
IMU_ROLL = deque([0,]*100, maxlen=100)
IMU_PITCH = deque([0,]*100, maxlen=100)



async def consumer(ctr, status, subplot=[]):

    async with aiohttp.ClientSession(trust_env = True) as session:
        status.subheader(f"Connecting to {WS_CONN}")
        async with session.ws_connect(WS_CONN) as websocket:
            status.subheader(f"Connected to: {WS_CONN}")
            async for message in websocket:
                data = message.json()
                if data["channel"] == "IMU1":
                    data = data["data"]
                    # adding data
                    IMU_ACC_X.append(data["AccX"])
                    IMU_ACC_Y.append(data["AccY"])
                    IMU_ACC_Z.append(data["AccZ"])
                    IMU_ACC_MAG.append(data["AccMagnitude"])
                    IMU_GYR_X.append(data["GyrX"])
                    IMU_GYR_Y.append(data["GyrY"])
                    IMU_GYR_Z.append(data["GyrZ"])
                    IMU_MAG_X.append(data["MagX"])
                    IMU_MAG_Y.append(data["MagY"])
                    IMU_MAG_Z.append(data["MagZ"])
                    IMU_MAG_MAG.append(data["MagMagnitude"])
                    IMU_ROLL.append(data["Roll"])
                    IMU_PITCH.append(data["Pitch"])
                    # updating dataframe
                    


                    # plotting
                    ctr.header("Live Data")
                    cols = ctr.columns(4)
                    if 0 in subplot:
                        cols[0].metric("AccX", f"{IMU_ACC_X[-1]} m/s²")
                        cols[0].line_chart(list(IMU_ACC_X), height=200, width=200)
                        cols[1].metric("AccY", f"{IMU_ACC_Y[-1]} m/s²")
                        cols[1].line_chart(list(IMU_ACC_Y), height=200, width=200)
                        cols[2].metric("AccZ", f"{IMU_ACC_Z[-1]} m/s²")
                        cols[2].line_chart(list(IMU_ACC_Z), height=200, width=200)
                        cols[3].metric("Magnitude", f"{IMU_ACC_MAG[-1]} m/s²")
                        cols[3].line_chart(list(IMU_ACC_MAG), height=200, width=200)

                    if 1 in subplot:
                        cols[0].metric("p (GyrX)", f"{IMU_GYR_X[-1]} rad/s")
                        cols[0].line_chart(list(IMU_GYR_X), height=200, width=200)
                        cols[1].metric("q (GyrY)", f"{IMU_GYR_Y[-1]} rad/s")
                        cols[1].line_chart(list(IMU_GYR_Y), height=200, width=200)
                        cols[2].metric("r (GyrZ)", f"{IMU_GYR_Z[-1]} rad/s")
                        cols[2].line_chart(list(IMU_GYR_Z), height=200, width=200)
                        cols[3].metric("-", f"-")

                    if 2 in subplot:
                        cols[0].metric("Roll", f"{IMU_ROLL[-1]}°")
                        cols[0].line_chart(list(IMU_ROLL), height=200, width=200)
                        cols[1].metric("Pitch", f"{IMU_PITCH[-1]}°")
                        cols[1].line_chart(list(IMU_PITCH), height=200, width=200)
                        cols[2].metric("-", f"-")
                        cols[3].metric("-", f"-")

                    if 3 in subplot:
                        cols[0].metric("MagX", f"{IMU_MAG_X[-1]} mG")
                        cols[0].line_chart(list(IMU_MAG_X)[-100:], height=200, width=200)
                        cols[1].metric("MagY", f"{IMU_MAG_Y[-1]} mG")
                        cols[1].line_chart(list(IMU_MAG_Y)[-100:], height=200, width=200)
                        cols[2].metric("MagZ", f"{IMU_MAG_Z[-1]} mG")
                        cols[2].line_chart(list(IMU_MAG_Z)[-100:], height=200, width=200)
                        cols[3].metric("Magnitude", f"{IMU_MAG_MAG[-1]} mG")
                        cols[3].line_chart(list(IMU_MAG_MAG)[-100:], height=200, width=200)
                        df = pd.DataFrame(
                            columns=['MagX','MagY'],
                            data=zip(IMU_MAG_X,IMU_MAG_Y),
                        )
                        df.set_index("MagX",inplace=True)
                        cols[0].scatter_chart(df)
                        # cols[0].area_chart(MAG_DATAFRAME,x="MagX",y="MagY", height=200, width=200)
