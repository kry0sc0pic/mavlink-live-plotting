# Mavlink Live Plotting
Plots live data from ardupilot on a streamlit dashboard


- All data except magnetometer is displayed using a rolling 100-record window. i.e. only the 100 most recent records are stored.
- For the magnetometer, all the records are saved.

## Running
1. Connect your autopilot and find the COM port using Windows Device Manager.
2. Change the COM Port in `server.py`
3. In the first terminal, execute `python server.py`
4. In the second terminal, execute `streamlit run Home.py`

- If you want to reset/clear the data on the frontend. Kill the streamlit process (second terminal) using `Ctrl + C` and restart it.