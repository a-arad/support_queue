import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import calendar
from data_processing import load_and_process
import os

df, dftm, dft_dash = load_and_process()

df_filtered = dft_dash[dft_dash['waiting_zone'].notnull()].copy()

def filter_by_company_size(df, size_category):
    if size_category == 'all':
        return df.copy()
    else:
        return df[df['company_size_category'] == size_category].copy()

app = Dash(__name__)

# to expose flask app to gunicorn
server = app.server  

df_filtered['month'] = df_filtered['created_at'].dt.strftime('%B')
months_in_order = list(calendar.month_name[1:])

app.layout = html.Div([
    html.H1("Customer Support Dashboard (start version)"),
    
    html.Label("Select Company Size"),
    dcc.Dropdown(
        id='company-size-filter',
        options=[
            {'label': 'All', 'value': 'all'},
            {'label': 'Small', 'value': 'small'},
            {'label': 'Large', 'value': 'large'}
        ],
        value='all',
        clearable=False,
        style={'width': '50%'}
    ),
    
    html.Label("Select Month"),
    dcc.Dropdown(
        id='month-filter',
        options=[{'label': month, 'value': month} for month in months_in_order if month in df_filtered['month'].unique()] + [{'label': 'All', 'value': 'all'}],
        value='all',
        clearable=False,
        style={'width': '50%'}
    ),
    
    dcc.Graph(id='time-series-plot'),
])

@app.callback(
    Output('time-series-plot', 'figure'),
    [Input('company-size-filter', 'value'),
     Input('month-filter', 'value')]
)
def update_time_series(company_size_category, selected_month):
    df_plot = filter_by_company_size(df_filtered, company_size_category)

    if selected_month != 'all':
        df_plot = df_plot[df_plot['month'] == selected_month]

    if 'created_at' in df_plot.columns:
        df_plot.set_index('created_at', inplace=True)

    df_plot.index = pd.to_datetime(df_plot.index)

    df_plot['green_zone'] = df_plot['waiting_zone'].apply(lambda x: 1 if x == 'green' else 0)
    df_plot['amber_zone'] = df_plot['waiting_zone'].apply(lambda x: 1 if x == 'amber' else 0)
    df_plot['red_zone'] = df_plot['waiting_zone'].apply(lambda x: 1 if x == 'red' else 0)

    time_grouped = df_plot.resample('D').agg({
        'wait_time_minutes': 'mean',
        'ticket_id': 'count',
        'green_zone': 'sum',
        'amber_zone': 'sum',
        'red_zone': 'sum'
    })

    trace_green = go.Scatter(
        x=time_grouped.index,
        y=time_grouped['green_zone'],
        mode='lines',
        name='Green Zone (0-29 min)',
        line=dict(color='green')
    )

    trace_amber = go.Scatter(
        x=time_grouped.index,
        y=time_grouped['amber_zone'],
        mode='lines',
        name='Amber Zone (30-59 min)',
        line=dict(color='orange')
    )

    trace_red = go.Scatter(
        x=time_grouped.index,
        y=time_grouped['red_zone'],
        mode='lines',
        name='Red Zone (60+ min)',
        line=dict(color='red')
    )

    trace_avg_wait_time = go.Scatter(
        x=time_grouped.index,
        y=time_grouped['wait_time_minutes'],
        mode='lines+markers',
        name='Average Wait Time (min)',
        line=dict(color='blue', dash='dot')
    )

    layout = go.Layout(
        title=f"Ticket Waiting Zones and Average Wait Time - {company_size_category.capitalize()} Companies",
        xaxis=dict(title='Date'),
        yaxis=dict(title='Number of Tickets / Avg Wait Time (min)'),
        hovermode='closest'
    )

    fig = go.Figure(data=[trace_green, trace_amber, trace_red, trace_avg_wait_time], layout=layout)

    return fig


if __name__ == '__main__':
    # Get the port from environment variable (Heroku), or default to 8050 (for local)
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=True, port=port)

    