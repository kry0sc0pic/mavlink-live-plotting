import aiohttp
from collections import deque
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
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


# https://github.com/marksemple/pyEllipsoid_Fit
def ellipsoid_fit(point_data, mode=''):
    """ Fit an ellipsoid to a cloud of points using linear least squares
        Based on Yury Petrov MATLAB algorithm: "ellipsoid_fit.m"
    """

    X = point_data[:, 0]
    Y = point_data[:, 1]
    Z = point_data[:, 2]

    # AlGEBRAIC EQUATION FOR ELLIPSOID, from CARTESIAN DATA
    if mode == '':  # 9-DOF MODE
        D = np.array([X * X + Y * Y - 2 * Z * Z,
                      X * X + Z * Z - 2 * Y * Y,
                      2 * X * Y, 2 * X * Z, 2 * Y * Z,
                      2 * X, 2 * Y, 2 * Z,
                      1 + 0 * X]).T

    elif mode == 0:  # 6-DOF MODE (no rotation)
        D = np.array([X * X + Y * Y - 2 * Z * Z,
                      X * X + Z * Z - 2 * Y * Y,
                      2 * X, 2 * Y, 2 * Z,
                      1 + 0 * X]).T

    # THE RIGHT-HAND-SIDE OF THE LLSQ PROBLEM
    d2 = np.array([X * X + Y * Y + Z * Z]).T

    # SOLUTION TO NORMAL SYSTEM OF EQUATIONS
    u = np.linalg.solve(D.T.dot(D), D.T.dot(d2))
    # chi2 = (1 - (D.dot(u)) / d2) ^ 2

    # CONVERT BACK TO ALGEBRAIC FORM
    if mode == '':  # 9-DOF-MODE
        a = np.array([u[0] + 1 * u[1] - 1])
        b = np.array([u[0] - 2 * u[1] - 1])
        c = np.array([u[1] - 2 * u[0] - 1])
        v = np.concatenate([a, b, c, u[2:, :]], axis=0).flatten()

    elif mode == 0:  # 6-DOF-MODE
        a = u[0] + 1 * u[1] - 1
        b = u[0] - 2 * u[1] - 1
        c = u[1] - 2 * u[0] - 1
        zs = np.array([0, 0, 0])
        v = np.hstack((a, b, c, zs, u[2:, :].flatten()))

    else:
        pass

    # PUT IN ALGEBRAIC FORM FOR ELLIPSOID
    A = np.array([[v[0], v[3], v[4], v[6]],
                  [v[3], v[1], v[5], v[7]],
                  [v[4], v[5], v[2], v[8]],
                  [v[6], v[7], v[8], v[9]]])

    # FIND CENTRE OF ELLIPSOID
    centre = np.linalg.solve(-A[0:3, 0:3], v[6:9])

    # FORM THE CORRESPONDING TRANSLATION MATRIX
    T = np.eye(4)
    T[3, 0:3] = centre

    # TRANSLATE TO THE CENTRE, ROTATE
    R = T.dot(A).dot(T.T)

    # SOLVE THE EIGENPROBLEM
    evals, evecs = np.linalg.eig(R[0:3, 0:3] / -R[3, 3])

    # SORT EIGENVECTORS
    # i = np.argsort(evals)
    # evals = evals[i]
    # evecs = evecs[:, i]
    # evals = evals[::-1]
    # evecs = evecs[::-1]

    # CALCULATE SCALE FACTORS AND SIGNS
    radii = np.sqrt(1 / abs(evals))
    sgns = np.sign(evals)
    radii *= sgns

    return (centre, evecs, radii)

def plot_ellipsoid_and_points(points, centre, evecs, radii):
    # Generate a grid of points for the ellipsoid
    phi, theta = np.mgrid[0:np.pi:100j, 0:2 * np.pi:100j]
    x_ellipsoid = radii[0] * np.sin(phi) * np.cos(theta)
    y_ellipsoid = radii[1] * np.sin(phi) * np.sin(theta)
    z_ellipsoid = radii[2] * np.cos(phi)

    # Apply rotation and translation to align the ellipsoid
    ellipsoid_points = np.stack((x_ellipsoid.ravel(), y_ellipsoid.ravel(), z_ellipsoid.ravel()), axis=0)
    rotated_points = evecs @ ellipsoid_points
    x_fit, y_fit, z_fit = (
        rotated_points[0, :] + centre[0],
        rotated_points[1, :] + centre[1],
        rotated_points[2, :] + centre[2],
    )

    # Reshape for plotting
    x_fit = x_fit.reshape(x_ellipsoid.shape)
    y_fit = y_fit.reshape(y_ellipsoid.shape)
    z_fit = z_fit.reshape(z_ellipsoid.shape)

    # Plot the point cloud and the fitted ellipsoid
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(points[:, 0], points[:, 1], points[:, 2], color="blue", label="Point Cloud", alpha=0.5)
    ax.plot_surface(x_fit, y_fit, z_fit, color="red", alpha=0.3, edgecolor="none", label="Fitted Ellipsoid")

    # Format the plot
    ax.set_xlabel("MagX (mGauss)")
    ax.set_ylabel("Mag-Y (mGauss)")
    ax.set_zlabel("Mag-Z (mGauss)")
    ax.set_title("Ellipsoid Fit to Point Cloud")
    return fig

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
                        if len(IMU_MAG_X) > 10 and len(IMU_MAG_Y) > 10 and len(IMU_MAG_Z) > 10:
                            try:
                                c,e,r = ellipsoid_fit(np.column_stack([IMU_MAG_X,IMU_MAG_Y,IMU_MAG_Z]))
                                fig = plot_ellipsoid_and_points(np.column_stack([IMU_MAG_X,IMU_MAG_Y,IMU_MAG_Z]),c,e,r)
                                cols[1].pyplot(fig)
                            except Exception as e:
                                pass
