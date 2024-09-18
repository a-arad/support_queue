import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import calendar
from datetime import date
import os
from data_processing_initial import load_and_process

df, dftm, dft_dash = load_and_process()

df_filtered = dft_dash[dft_dash['waiting_zone'].notnull()].copy()

def filter_by_company_size(df, size_category):
    if size_category == 'all':
        return df.copy()
    else:
        return df[df['company_size_category'] == size_category].copy()

app = Dash(__name__)

server = app.server

df_filtered['month'] = df_filtered['created_at'].dt.strftime('%B')
months_in_order = list(calendar.month_name[1:])

min_date = df_filtered['created_at'].min().date()
max_date = df_filtered['created_at'].max().date()

app.layout = html.Div([
    html.H1("Customer Support Dashboard"),

    html.Div([
        
        html.Div([
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
                style={'width': '90%'}
            )
        ], style={'flex': '1', 'padding-right': '10px'}),  
        
        html.Div([
            html.Label("Select Month"),
            dcc.Dropdown(
                id='month-filter',
                value='all',
                options=[{'label': 'All', 'value': 'all'}] + [{'label': month, 'value': month} for month in months_in_order if month in df_filtered['month'].unique()],
                clearable=False,
                style={'width': '90%'}
            )
        ], style={'flex': '1', 'padding-left': '10px'}),  
    ], style={'display': 'flex', 'flex-wrap': 'wrap', 'width': '100%', 'margin-bottom': '20px'}),  

    dcc.Graph(id='avg-wait-time-plot'), 
    dcc.Graph(id='zone-tickets-plot'),

    html.Label("Filter by Date Range"),
    
    dcc.RangeSlider(
        id='date-slider',
        min=min_date.toordinal(),
        max=max_date.toordinal(),
        step=1,
        value=[min_date.toordinal(), max_date.toordinal()],
        marks={date.toordinal(): date.strftime('%Y-%m-%d') for date in pd.date_range(min_date, max_date, freq='ME')},                  
        updatemode='mouseup'
    ),

    html.Div(id='date-display', style={'margin-top': '20px', 'font-weight': 'bold'}),
    
])
@app.callback(
    Output('date-display', 'children'),
    Input('date-slider', 'value')
)
def update_date_display(date_range):
    start_date = date.fromordinal(date_range[0]).strftime('%Y-%m-%d')
    end_date = date.fromordinal(date_range[1]).strftime('%Y-%m-%d')
    return f"Selected Date Range: {start_date} to {end_date}"
    
@app.callback(
    [Output('avg-wait-time-plot', 'figure'),
     Output('zone-tickets-plot', 'figure')],
    [Input('company-size-filter', 'value'),
     Input('month-filter', 'value'),
     Input('date-slider', 'value')]
)
def update_plots(company_size_category, selected_month, date_range):
    df_plot = filter_by_company_size(df_filtered, company_size_category)

    if selected_month != 'all':
        df_plot = df_plot[df_plot['month'] == selected_month]

    start_date = date.fromordinal(date_range[0])
    end_date = date.fromordinal(date_range[1])

    df_plot = df_plot[(df_plot['created_at'].dt.date >= start_date) & (df_plot['created_at'].dt.date <= end_date)]

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

    trace_avg_wait_time = go.Scatter(
        x=time_grouped.index,
        y=time_grouped['wait_time_minutes'].round(1),
        mode='lines+markers',
        name='Average Wait Time (min)',
        line=dict(color='blue', dash='dot')
    )

    layout_avg_wait_time = go.Layout(
        title="Average Wait Time Over Time",
        xaxis=dict(title='Date'),
        yaxis=dict(title='Average Wait Time (min)'),
        hovermode='closest'
    )

    fig_avg_wait_time = go.Figure(data=[trace_avg_wait_time], layout=layout_avg_wait_time)

    trace_green = go.Scatter(
        x=time_grouped.index,
        y=time_grouped['green_zone'],
        mode='lines',
        name='Green Zone',
        line=dict(color='green')
    )

    trace_amber = go.Scatter(
        x=time_grouped.index,
        y=time_grouped['amber_zone'],
        mode='lines',
        name='Amber Zone',
        line=dict(color='orange')
    )

    trace_red = go.Scatter(
        x=time_grouped.index,
        y=time_grouped['red_zone'],
        mode='lines',
        name='Red Zone',
        line=dict(color='red')
    )

    layout_zone_tickets = go.Layout(
        title="Number of Tickets in Red, Green, and Amber Zones",
        xaxis=dict(title='Date'),
        yaxis=dict(title='Number of Tickets'),
        hovermode='closest'
    )

    fig_zone_tickets = go.Figure(data=[trace_green, trace_amber, trace_red], layout=layout_zone_tickets)

    return fig_avg_wait_time, fig_zone_tickets

if __name__ == '__main__':    
    port = int(os.environ.get("PORT", 8051))
    app.run_server(host="localhost",debug=True, port=port)