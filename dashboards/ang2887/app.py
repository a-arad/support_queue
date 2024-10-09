
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
from plotly.subplots import make_subplots
from datetime import date
from data_processing_initial import load_and_process

_, _, dft_dash = load_and_process()

def filter_by_company_size(df, size_category):
    if size_category == 'all':
        return df.copy()
    else:
        return df[df['company_size_category'] == size_category].copy()

app = Dash(__name__)

min_date = dft_dash['created_at'].min().date()
max_date = dft_dash['created_at'].max().date()

app.layout = html.Div([
    html.H1('Customer Support Ticket Wait Time', style={'color': '#0E446E', 'font-family': 'Arial'}), 

    html.Div([
        html.Label('Select Company Size', style={'font-weight': 'bold','color': '#0E446E', 'font-family': 'Arial'}),  
        dcc.Dropdown(
            id='company-size-filter',
            options=[
                {'label': 'All', 'value': 'all'},
                {'label': 'Small - 1-12 employees', 'value': 'small'},
                {'label': 'Large - 13+ employees', 'value': 'large'}
            ],
            value='all',
            clearable=False,
            style={'width': '50%', 'font-family': 'Arial'}
        )
    ], style={'margin-bottom': '20px'}),  
    

    dcc.Graph(id='avg-wait-time-plot'),
    dcc.Graph(id='total-tickets-plot'),

    html.Div([
        html.Div(id='red-zone-tickets', style={'backgroundColor': 'red', 'color': 'white', 'padding': '10px', 'flex': '1', 'font-family': 'Arial'}),
        html.Div(id='amber-zone-tickets', style={'backgroundColor': 'orange', 'color': 'white', 'padding': '10px', 'flex': '1', 'font-family': 'Arial'}),
        html.Div(id='green-zone-tickets', style={'backgroundColor': 'green', 'color': 'white', 'padding': '10px', 'flex': '1', 'font-family': 'Arial'}),
    ], style={'display': 'flex', 'flexDirection': 'row', 'marginBottom': '20px'}),

    
    html.Label('Filter by Date Range', style={ 'font-weight': 'bold','color': '#0E446E', 'font-family': 'Arial'}),  
    dcc.RangeSlider(
        id='date-slider',
        min=min_date.toordinal(),
        max=max_date.toordinal(),
        step=1,
        value=[min_date.toordinal(), max_date.toordinal()],
        marks={date.toordinal(): date.strftime('%Y-%m-%d') for date in pd.date_range(min_date, max_date, freq='ME')},
        updatemode='mouseup'
    ),

    
    html.Div(id='date-display', style={'margin-top': '20px', 'font-weight': 'bold', 'color': '#0E446E', 'font-family': 'Arial'})  
])

@app.callback(
    [Output('avg-wait-time-plot', 'figure'),
     Output('total-tickets-plot', 'figure'),
     Output('red-zone-tickets', 'children'),
     Output('amber-zone-tickets', 'children'),
     Output('green-zone-tickets', 'children'),
     Output('date-display', 'children')],
    [Input('company-size-filter', 'value'),
     Input('date-slider', 'value'),
     Input('avg-wait-time-plot', 'relayoutData'),
     Input('total-tickets-plot', 'relayoutData')],
    State('date-slider', 'value')  
)
def update_dashboard(company_size_category, date_range, avg_plot_relayout, total_plot_relayout, slider_value):
    df_plot = filter_by_company_size(dft_dash, company_size_category)
    
    
    if avg_plot_relayout and 'xaxis.range[0]' in avg_plot_relayout and 'xaxis.range[1]' in avg_plot_relayout:
        start_date = pd.to_datetime(avg_plot_relayout['xaxis.range[0]']).date()
        end_date = pd.to_datetime(avg_plot_relayout['xaxis.range[1]']).date()
    elif total_plot_relayout and 'xaxis.range[0]' in total_plot_relayout and 'xaxis.range[1]' in total_plot_relayout:
        start_date = pd.to_datetime(total_plot_relayout['xaxis.range[0]']).date()
        end_date = pd.to_datetime(total_plot_relayout['xaxis.range[1]']).date()
    else:
        start_date = date.fromordinal(slider_value[0])
        end_date = date.fromordinal(slider_value[1])

    df_plot = df_plot[(df_plot['created_at'].dt.date >= start_date) & (df_plot['created_at'].dt.date <= end_date)]
   
    if 'created_at' in df_plot.columns:
        df_plot.set_index('created_at', inplace=True)

    df_plot.index = pd.to_datetime(df_plot.index)

    df_plot['green_zone'] = df_plot['waiting_zone'].apply(lambda x: 1 if x == 'green' else 0)
    df_plot['amber_zone'] = df_plot['waiting_zone'].apply(lambda x: 1 if x == 'amber' else 0)
    df_plot['red_zone'] = df_plot['waiting_zone'].apply(lambda x: 1 if x == 'red' else 0)

    time_grouped = df_plot.resample('D').agg({
        'wait_time_minutes': ['mean', 'max'], 
        'ticket_id': 'count',  
        'green_zone': 'sum',
        'amber_zone': 'sum',
        'red_zone': 'sum'
    }).asfreq('D', fill_value=0)

    # to flatten multiindex columns 
    time_grouped.columns = ['_'.join(col).strip() for col in time_grouped.columns]

    # to check if the column names are properly flattened
    #print(time_grouped.columns)  

   
    fig_avg_max_wait_time = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                      subplot_titles=('Average Wait Time', 'Max Wait Time'))

    
    fig_avg_max_wait_time.add_trace(go.Scatter(
        x=time_grouped.index,
        y=time_grouped['wait_time_minutes_mean'].round(1),
        mode='lines+markers',
        name='Average Wait Time (min)',
        line=dict(color='blue', dash='dot')
    ), row=1, col=1)
    
    fig_avg_max_wait_time.add_trace(go.Scatter(
        x=time_grouped.index,
        y=time_grouped['wait_time_minutes_max'].round(1),
        mode='markers',
        name='Max Wait Time (min)',
        marker=dict(color='purple', size=6, opacity=0.6)
    ), row=2, col=1)

    fig_avg_max_wait_time.update_layout(
        height=600, 
        title={'text': 'Customer Wait Time: Daily Averages and Maximums', 'font': {'color': '#0E446E', 'family': 'Arial', 'size': 18}},
        hovermode='closest'
    )

    fig_avg_max_wait_time.update_yaxes(title_text='Avg Wait Time (min)', type='linear', row=1, col=1)
    fig_avg_max_wait_time.update_yaxes(title_text='Max Wait Time (min)', type='linear', row=2, col=1)
    

    trace_total_tickets = go.Bar(
        x=time_grouped.index,
        y=time_grouped['ticket_id_count'],  
        marker_color='blue'
    )

    fig_total_tickets = go.Figure(data=[trace_total_tickets])
    fig_total_tickets.update_layout(
        title={'text': 'Total Tickets per Day', 'font': {'color': '#0E446E', 'family': 'Arial','size': 18}},
        yaxis=dict(title='Number of Tickets'),
        hovermode='closest'
    )

    red_zone_tickets = f"Red Zone (wait time > 60 min): {time_grouped['red_zone_sum'].sum()} Tickets"
    amber_zone_tickets = f"Amber Zone (wait time > 30 min): {time_grouped['amber_zone_sum'].sum()} Tickets"
    green_zone_tickets = f"Green Zone (wait time ≤ 30 min): {time_grouped['green_zone_sum'].sum()} Tickets"

    date_display = f"Selected Date Range: {start_date} to {end_date}"

    return fig_avg_max_wait_time, fig_total_tickets, red_zone_tickets, amber_zone_tickets, green_zone_tickets, date_display
        
if __name__ == '__main__':    
    app.run_server(host='localhost', debug=True)