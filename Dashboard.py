import plotly.graph_objects as go
import streamlit as st
import numpy as np
import serial
import math


ser = serial.Serial('COM10', 115200, timeout=1)  # Adjust port and baudrate accordingly

st.set_page_config(layout="wide")# Set page config to wide

# Create a figure
fig_3d = go.Figure()
g_force_fig = go.Figure()
rssi_fig = go.Figure()
g_force_time_fig = go.Figure()
compass_fig  =go.Figure()
speed_fig = go.Figure()

col1, col2, col3 = st.columns(3)

# Define the coordinates of the box
gravity_acc = 9.80665
lat_list = []
lon_list = []
x = [0, 1, 1, 0, 0, 1, 1, 0]
y = [0, 0, 2, 2, 0, 0, 2, 2]
z = [0, 0, 0, 0, 0.5, 0.5, 0.5, 0.5]

# Add a trace for the box
fig_3d.add_trace(go.Mesh3d(
    x=x,
    y=y,
    z=z,
    color="lightgreen",
    opacity=0.5,
    alphahull=0
))
camera = dict(
    eye=dict(x=-0.1, y=1.5, z=0.1)
)

# Update layuot for the box
fig_3d.update_layout(
    margin ={'l':20,'t':25,'b':4,'r':20},
    scene_camera=camera,width = 450,
    height = 450,scene_xaxis_visible=False, 
    scene_yaxis_visible=False, scene_zaxis_visible=False,
    title = '3D Orientation')

# Add a trace for g force chart
g_force_fig.add_trace(go.Scatterpolar(
    r=[0],
    theta=[0],
    mode='markers',
    marker=dict(
        color='blue',
        size=20,
        line=dict(color='black', width=2)
    )
))

# Set layout options for polar plot
g_force_fig.update_layout(
    margin ={'l':20,'t':25,'b':4,'r':20},
    polar=dict(
        radialaxis=dict(range=[0, 3], showgrid=True, gridcolor='lightgrey', gridwidth=0.5),
        angularaxis=dict(showgrid=True, gridcolor='lightgrey', gridwidth=0.5),
    ),
    showlegend=False,
    width=450,
    height=450,
    title='G-Force Sensor Data'
)

# Add a trace for time series g force
g_force_time_fig.add_trace(go.Scatter(
    x=[],
    y=[],
    mode='lines',
    marker=dict(
        color='blue',
        size=10,
        line=dict(color='black', width=2)
    )
))

# Update layout for time series g force
g_force_time_fig.update_layout(
    margin ={'l':20,'t':25,'b':4,'r':20},
    xaxis=dict(title='Time'),
    yaxis=dict(title='G-Force'),
    showlegend=False,
    title='G-Force Magnitude',
    yaxis_range=[-0.2,3]
)

# Add trace for RSSI fig
rssi_fig.add_trace(go.Indicator(
    mode="gauge+number+delta",
    value=0,
    title={'text': 'Gauge'},
    delta={'reference': 0},
    gauge={
        'axis': {'range': [-120, 0], 'tickmode': 'array', 'tickvals': [-120, -70, -30, 0]},
        'shape': "bullet",
        'steps': [
            {'range': [-120, -70], 'color': 'rgb(255, 0, 0)'},
            {'range': [-70, -30], 'color': 'rgb(255, 255, 0)'},
            {'range': [-30, 0], 'color': 'rgb(0, 255, 0)'},
        ],
        'bar': {'color': 'black', 'thickness': 0.4},
    },
))

# Update layuot for RSSI
rssi_fig.update_layout(
    margin ={'l':20,'t':25,'b':4,'r':20},
    width=500,
    height=100,
    title='RSSI'
)

# Add a trace for compass
compass_fig.add_trace(go.Scatterpolar(
        r=[0, 0.5],
        theta=[90, 90],
        mode='lines+markers',
        marker=dict(size=0),
        line=dict(color='red', width=4),
        hoverinfo='none'
    ))
# Update compass layout
compass_fig.update_layout(
        margin ={'l':20,'t':25,'b':4,'r':20},
        polar=dict(
            radialaxis=dict(visible=False),
            angularaxis=dict(showline=False, tickmode='array', tickvals=[0, 45, 90, 135, 180, 225, 270, 315], ticktext=['E','NE','N','NW','W','SW','S','SE' ])
        ),
        showlegend=False,
        width=500,
        height=500,
        title='Compass heading'
    )

#Initial map
tracker_map = go.Figure(go.Scattermapbox(
    mode = "markers",
    lon = [100.5],
    lat = [13.75],
    marker = {'size': 10,'color':'blue'}))

tracker_map.update_layout(
    margin ={'l':20,'t':25,'b':4,'r':20},
    mapbox = {
        'center': {'lon': 100.5, 'lat': 13.75},
        'style': "open-street-map",
        'center': {'lon': 100.5, 'lat': 13.75},
        'zoom': 18},
    title='Tracking Map',
    width=450,
    height=450,
        )

# Add a trace for speed fig
speed_fig.add_trace(go.Indicator(
    mode="gauge+number+delta",
    value=0,
    title={'text': 'Gauge'},
    delta={'reference': 0},
    gauge={
        'axis': {'range': [0, 80], 'tickmode': 'array', 'tickvals': [0, 50, 70, 80]},
        'steps': [
            {'range': [0, 50], 'color': 'rgb(0, 255, 0)'},
            {'range': [50, 70], 'color': 'rgb(255, 255, 0)'},
            {'range': [70, 80], 'color': 'rgb(255, 0, 0)'},
        ],
        'bar': {'color': 'black', 'thickness': 0.4},
    },
))
# Update speed fig layout
speed_fig.update_layout(
    margin ={'l':20,'t':25,'b':4,'r':20},
    width=450,
    height=450,
    title='Speed'
)

# Insert charts to streamlit UI
chart_g_force = col1.plotly_chart(g_force_fig, use_container_width=True)
chart_g_force_time = col1.plotly_chart(g_force_time_fig, use_container_width=True)
chart_tracker_map = col2.plotly_chart(tracker_map, use_container_width=True)
chart_speed = col2.plotly_chart(speed_fig, use_container_width=True)
chart_rssi = st.sidebar.plotly_chart(rssi_fig, use_container_width=True)
debug_text = st.sidebar.empty()

chart_tracker_map_xy = col3.plotly_chart(fig_3d, use_container_width=True)
chart_compass = col3.plotly_chart(compass_fig, use_container_width=True)

# Calculate center of the box
center_x = sum(x) / len(x)
center_y = sum(y) / len(y)
center_z = sum(z) / len(z)

rssi_window_size = 3
rssi_last_values = [0] * rssi_window_size

speed_window_size = 3
speed_last_values = [0] * speed_window_size

g_force_window_size = 50
g_force_last_values  = [0] * g_force_window_size

g_force_x_window_size = 5
g_force_X_last_values  = [0] * g_force_x_window_size

g_force_y_window_size = 5
g_force_y_last_values  = [0] * g_force_y_window_size

def rotate_3d(x, y, z, yaw, pitch, roll):
    
    new_x = []
    new_y = []
    new_z = []
    
    for x_val, y_val, z_val in zip(x, y, z):
        # Apply 3D rotation
        new_x_val = (x_val - center_x) * (np.cos(yaw) * np.cos(pitch)) + \
                    (y_val - center_y) * (np.cos(yaw) * np.sin(pitch) * np.sin(roll) - np.sin(yaw) * np.cos(roll)) + \
                    (z_val - center_z) * (np.cos(yaw) * np.sin(pitch) * np.cos(roll) + np.sin(yaw) * np.sin(roll)) + center_x
        
        new_y_val = (x_val - center_x) * (np.sin(yaw) * np.cos(pitch)) + \
                    (y_val - center_y) * (np.sin(yaw) * np.sin(pitch) * np.sin(roll) + np.cos(yaw) * np.cos(roll)) + \
                    (z_val - center_z) * (np.sin(yaw) * np.sin(pitch) * np.cos(roll) - np.cos(yaw) * np.sin(roll)) + center_y
        
        new_z_val = -(x_val - center_x) * np.sin(pitch) + \
                     (y_val - center_y) * np.cos(pitch) * np.sin(roll) + \
                     (z_val - center_z) * np.cos(pitch) * np.cos(roll) + center_z
        
        new_x.append(new_x_val)
        new_y.append(new_y_val)
        new_z.append(new_z_val)
    
    return new_x, new_y, new_z

accX, accY, accZ, yaw, pitch, roll, heading, lat, lon, gps_speed, rssi, isDraw = [0]*12
last_bool = 1
# Function to update the box rotation based on sensor data
def main_loop():
    global last_bool
    try: # Read and all data
        global accX, accY, accZ, yaw, pitch, roll, heading, lat, lon, gps_speed, rssi, isDraw

        data = ser.readline().decode('utf-8').strip().split(',')
        ser.flush()
        ser.flushInput()
        accX, accY, accZ, yaw, pitch, roll, heading, lat, lon, gps_speed, rssi, isDraw = map(float,data)
    except:
        pass

    if isDraw == 1 and last_bool == 0:#check edge of button
        draw_line()
    elif isDraw == 1 and last_bool == 1:
        pass
    else:
        delete_line()

    last_bool = isDraw
    add_marker(lat, lon) # add new position

    heading += 90 #adjust heading offset

    #convert acceleration to G-Force
    g_force_x = accX/gravity_acc
    g_force_y = accY/gravity_acc

    # Calculate average of last 5 data
    g_force_X_last_values.pop(0)
    g_force_X_last_values.append(g_force_x)

    g_force_y_last_values.pop(0)
    g_force_y_last_values.append(g_force_y)

    avg_g_force_x = np.average(g_force_X_last_values)
    avg_g_force_y = np.average(g_force_y_last_values)
    
    # Convert to polar form
    resultant_magnitude = math.sqrt(avg_g_force_x**2 + avg_g_force_y**2)
    theta = math.degrees(math.atan2(avg_g_force_y, avg_g_force_x))
    
    # Pop the first of array and add new value to array
    g_force_last_values.pop(0)
    g_force_last_values.append(resultant_magnitude)

    # Redraw G-Force chart
    g_force_time_fig.update_traces(x=list(range(g_force_window_size)), y=g_force_last_values)
    chart_g_force_time.plotly_chart(g_force_time_fig, use_container_width=True)

    g_force_fig.update_traces(r=[resultant_magnitude], theta=[theta])
    chart_g_force.plotly_chart(g_force_fig, use_container_width=True)
    
    # Calculate new position of edge of the box
    new_x, new_y, new_z = rotate_3d(x, y, z, yaw, pitch, roll)

    # Update the box trace with new coordinates
    fig_3d.data[0].x = new_x
    fig_3d.data[0].y = new_y
    fig_3d.data[0].z = new_z

    # Redraw the box
    fig_3d.update_layout(scene=dict(
        xaxis=dict(nticks=4, range=[-0.5, 1.8]),
        yaxis=dict(nticks=4, range=[-0.5, 2]),
        zaxis=dict(nticks=4, range=[-0.8, 1.5]),
        aspectmode='cube'
    ))
    chart_tracker_map_xy.plotly_chart(fig_3d, use_container_width=True)
    
    # Redraw the compass chart
    compass_fig.update_traces(r=[0,0.5], theta=[0,(360-heading)+90])
    chart_compass.plotly_chart(compass_fig, use_container_width=True)

    # Calculate the average of last 3 RSSI value to reference value
    rssi_last_values.pop(0)
    rssi_last_values.append(int(rssi))
    reference_value = sum(rssi_last_values) / rssi_window_size

    # Redraw RSSI chart
    rssi_fig.update_traces(value=int(rssi), delta={'reference': reference_value})
    chart_rssi.plotly_chart(rssi_fig, use_container_width=True)

    # Calculate the average of last 3 speed value to reference value
    speed_last_values.pop(0)
    speed_last_values.append(gps_speed)
    reference_value = sum(speed_last_values) / speed_window_size

    # Redraw speed chart
    speed_fig.update_traces(value=gps_speed, delta={'reference': reference_value})
    chart_speed.plotly_chart(speed_fig, use_container_width=True)

#Translate into valid coordinate
def translate_to_valid_coord(latitude, longitude):
    if latitude == 0 and longitude == 0:
        if len(lat_list) != 0:
            return lat_list[-1], lon_list[-1]
    return latitude, longitude

#Add new coordinate to the record
def add_pos(latitude, longitude):
    lon_list.append(longitude)
    lat_list.append(latitude)

#Erase all coordinates except the latest
def erase_trail():
    global lon_list
    global lat_list

    if len(lat_list) != 0:
        lat_list = [lat_list[-1]]
        lon_list = [lon_list[-1]]
    else:
        lat_list = []
        lon_list = []

#Reset coordinate record
def reset_coord_record():
    global lon_list
    global lat_list

    lat_list = []
    lon_list = []

#Add new marker in the map
def add_marker(latitude, longitude):
    global chart_tracker_map
    global tracker_map

    latitude, longitude = translate_to_valid_coord(latitude, longitude)

    #Add new marker
    add_pos(latitude, longitude)
    debug_text.write(tracker_map.data[0].mode)

    if tracker_map.data[0].mode == "markers":
        tracker_map.data[0].lon = (longitude, )
        tracker_map.data[0].lat = (latitude, )
    else:
        tracker_map.data[0].lon = lon_list
        tracker_map.data[0].lat = lat_list

    tracker_map.update_layout(
        mapbox = {
            'center': {'lon': longitude, 'lat': latitude},
            'style': "open-street-map",
                'center': {'lon': longitude, 'lat': latitude},
                'zoom': 18})
    
    #Update UI
    chart_tracker_map.plotly_chart(tracker_map, use_container_width=True)

#Draw line using marker
def draw_line():
    global chart_tracker_map
    global tracker_map

    #Draw the line
    tracker_map.data[0].mode = "markers+lines"
    erase_trail()
    tracker_map.data[0].lon = [lon_list[0]]
    tracker_map.data[0].lat = [lat_list[0]]

    #Update UI
    chart_tracker_map.plotly_chart(tracker_map, use_container_width=True)

#Delete the line and keep only latest marker
def delete_line():
    global chart_tracker_map
    global tracker_map

    #Remove old marker from list
    erase_trail()

    tracker_map.data[0].mode = "markers"
    
    tracker_map.data[0].lon = []
    tracker_map.data[0].lat = []

    #Update UI
    chart_tracker_map.plotly_chart(tracker_map, use_container_width=True)

#Testing stuff
if __name__ == "__main__":
    while True:
        main_loop()
