import dash
from dash import dcc, html, Output, Input, dash_table
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import sqlite3

# tabelke z anomaliami
# wartosci srednie (dwa wykresy )
# powinno byc git

def normalised_column_value(df):
    return df['value'] / max(df['value']) * 100


def plot_single_figure_six_traces_separately_for_all_foots(df_measurements):
    title = str(df_measurements['firstname'].unique() + ' ' + df_measurements['lastname'].unique())

    fig = make_subplots(rows=2, cols=3, start_cell="bottom-left", shared_xaxes=True, shared_yaxes=True,
                        subplot_titles=df_measurements['name'].unique(), x_title='time', y_title='value')

    for i in range(6):
        fig.add_trace(go.Scatter(y=df_measurements[df_measurements['id_sensor'] == i]['value'], showlegend=False),
                      row=int(i / 3) + 1, col=(i % 3) + 1)

    fig.update_layout(
        title={
            'text': title[2:-2],
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'})

    return fig


def get_prepared_measurements():
    con = sqlite3.connect("proj.db")

    tmp_last_name = "Grzegorczyk"

    df_all_measurement = pd.read_sql_query("SELECT * from measurements", con)  # this moment it is one person

    df_all_measurement['value'] = normalised_column_value(df_all_measurement)

    df_all_measurement['time'] = (df_all_measurement['time'] - min(df_all_measurement['time'])) / (
            max(df_all_measurement['time']) - min(df_all_measurement['time']))

    df_all_measurement = df_all_measurement.drop('index', axis=1)

    person_measurements = df_all_measurement[df_all_measurement['lastname'] == tmp_last_name]
    return person_measurements


person_measurements = get_prepared_measurements()
anomaly = person_measurements[person_measurements['anomaly'] == 1]
min_time = min(person_measurements['time'])
max_time = max(person_measurements['time'])
step = 0.001
slider_left = min_time
slider_middle = (max_time - min_time) / 2
slider_right = max_time
n_intervals = 0

img = Image.open('stopki.png')

fig_foot = go.Figure(data=[go.Scatter(
    x=[3.5, 1, 3, 6.5, 9, 7],
    y=[7, 6, 1.5, 7, 6, 1.5],
    mode='markers',
    marker_size=person_measurements.iloc[-6:, -1]
)],
)

fig_foot.add_layout_image(
    dict(
        source=img,
        xref="x",
        yref="y",
        x=0,
        y=10,
        sizex=10,
        sizey=10,
        sizing="stretch",
        opacity=0.5,
        layer="below"),

)

fig_foot.update_layout(
    template="plotly_white",
)
# tmp = {'sentor_'+str(i): person_measurements[person_measurements['name'] == i]['value'].values for i in person_measurements['name'].unique()}
# box  = pd.DataFrame({'sentor_'+str(i): person_measurements[person_measurements['name'] == i]['value'].values for i in person_measurements['name'].unique()})

fig_quartiles = px.box({'sensor_'+str(i): person_measurements[person_measurements['name'] == i]['value'].values for i in person_measurements['name'].unique()})
fig_quartiles.update_layout(
    title="Quartiles")
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Wizualizcja stopek', style={'textAlign': 'center'}),

    html.Div(children='Andrzej Czechowki, Karol Kociołek', style={'textAlign': 'center'}),

    html.H1(children='Patterns:'),
    html.H1(children='Person'),

    dcc.Dropdown(
        id='dropdown',
        # options=[{'label': i, 'value': i} for i in df['category'].unique()],
        options=[{'label': "Grzegorczyk", 'value': "Grzegorczyk"}],

        value='Grzegorczyk'
    ),
    # html.H1(children='co to wgl znaczy wzor chodzenia, nwm jakas prenetacja stopek tu pewnie bedzie'),

    dcc.Graph(
        id='scanner_history_foot',
        figure=plot_single_figure_six_traces_separately_for_all_foots(person_measurements),

    ),
    html.Div([
        dcc.Graph(
            id='graph_foot',
            figure=fig_foot,
            style={'width': '90vh', 'height': '70vh'}
        ),
        'mean value',
        dcc.Graph(
            id='graph_foot_mean',
            figure=fig_foot,
            style={'width': '90vh', 'height': '70vh'}
        ),

    ],
        style={'width': '48%', 'float': 'left', 'display': 'inline-block'}

    ),
    html.Div([
        dcc.RadioItems(
            id='start-stop',
            options=[
                {'label': 'start', 'value': 'start'},
                {'label': 'stop', 'value': 'stop'},
            ],
            value='stop',
            labelStyle={'display': 'inline-block'}
        ),
        'Speed simulations',
        dcc.Dropdown(
            id='speed',
            # options=[{'label': i, 'value': i} for i in df['category'].unique()],
            options=[{'label': str(i/10), 'value': str(i/10)} for i in range(11)],

            value='0.0'
        ),

        html.P("Time:"),
        dcc.RangeSlider(
            id='range-slider',
            min=min_time, max=max_time, step=step,
            marks={min_time: str(min_time), max_time: str(max_time)},
            value=[slider_left, slider_middle, slider_right],
            allowCross=False,
            tooltip={"placement": "bottom", "always_visible": True},

            pushable=0.01
        ),
"Anomaly table",
        dash_table.DataTable(
            id='datatable-paging-page-count',
            columns=[
                {"name": i, "id": i} for i in person_measurements.columns
            ],
            page_current=0,
            page_size=6,
            page_action='custom',
            page_count=int(len(anomaly) / 6),
            style_table={'width': '90vh', 'height': '40vh'}
        ),
        dcc.Graph(
            id='quartiles',
            figure=fig_quartiles,
            style={'width': '90vh', 'height': '60vh'}
        ),

    ],
        style={'width': '48%', 'float': 'right', 'display': 'inline-block'}
    ),
    #


    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # in milliseconds
        n_intervals=0,
        disabled=True
    ),
])


@app.callback(
    Output('datatable-paging-page-count', 'data'),
    Input('datatable-paging-page-count', "page_current"),
    Input('datatable-paging-page-count', "page_size"))
def update_table(page_current, page_size):
    return anomaly.iloc[
           page_current * page_size:(page_current + 1) * page_size
           ].to_dict('records')

@app.callback(
    Output('interval-component', 'disabled'),
    Input('start-stop', 'value')
)
def update_output(value):
    if value == 'start':
        return False
    else:
        return True


@app.callback(
    Output("scanner_history_foot", "figure"),
    [Input("range-slider", "value")])
def update_bar_chart(slider_range):
    low, current, high = slider_range

    global slider_left, slider_middle, slider_right

    slider_left, slider_middle, slider_right = slider_range

    delta = 0.01

    mask = person_measurements[(person_measurements['time'] > low) & (person_measurements['time'] < high)]

    title = str(person_measurements['firstname'].unique() + ' ' + person_measurements['lastname'].unique())

    fig = make_subplots(rows=2, cols=3, start_cell="bottom-left", shared_xaxes=True, shared_yaxes=True,
                        subplot_titles=person_measurements['name'].unique(), x_title='time', y_title='value')

    for i in range(6):
        point = \
            mask[((mask['time'] > (current - delta)) & (mask['time'] < (current + delta))) & (
                        mask['id_sensor'] == i)].iloc[
                -1]

        fig.add_trace(go.Scatter(x=mask[mask['id_sensor'] == i]['time'], y=mask[mask['id_sensor'] == i]['value'],
                                 showlegend=False, mode='lines'),
                      row=int(i / 3) + 1, col=(i % 3) + 1)

        fig.add_trace(go.Scatter(x=[point['time']], y=[point['value']],
                                 showlegend=False, mode='markers'),
                      row=int(i / 3) + 1, col=(i % 3) + 1)

    fig.update_layout(
        title={
            'text': title[2:-2],
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'})

    return fig


@app.callback(
    [
        Output('graph_foot', 'figure'),
        Output('range-slider', 'value'),
    ],
    [
        Input('scanner_history_foot', 'hoverData'),
        Input('interval-component', 'n_intervals')
    ])
def update_foot_image(hoverData, current_intervals):
    global slider_middle
    global n_intervals

    print(current_intervals)
    print(n_intervals)

    if current_intervals != n_intervals:
        slider_middle += 0.1
        n_intervals = current_intervals
        if slider_middle > slider_right:
            slider_middle -= 0.1
    else:
        try:
            slider_middle = hoverData['points'][0]['x']
        except:
            pass

    time = slider_middle

    fig_foot = go.Figure(data=[go.Scatter(
        x=[3.5, 1, 3, 6.5, 9, 7],
        y=[7, 6, 1.5, 7, 6, 1.5],
        mode='markers',
        marker_size=person_measurements[person_measurements['time'] == time].iloc[:, -1]
    )],
    )

    fig_foot.add_layout_image(
        dict(
            source=img,
            xref="x",
            yref="y",
            x=0,
            y=10,
            sizex=10,
            sizey=10,
            sizing="stretch",
            opacity=0.5,
            layer="below"),

    )
    fig_foot.update_layout(
        template="plotly_white",
    )

    return fig_foot, [slider_left, time, slider_right]


if __name__ == '__main__':
    app.run_server(debug=True)
