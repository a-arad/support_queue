import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go

load_dotenv()
db_con_string = os.getenv("READONLY_DB")
conn = psycopg2.connect(db_con_string)

query_1 = """ 

SELECT   
s.created_at, 
date (s.created_at) as Date_created,
extract (hour from s.created_at) as hour_created,
s.user_id, s.ticket_id, 
c.company_id, c.company_size, s.issue_category, 
m.matched_at ,
EXTRACT (EPOCH FROM AGE(matched_at, created_at)) /60 AS wait_time,
st.staff_id


FROM support_tickets s 
LEFT JOIN ticket_status t
ON s.ticket_id = t.ticket_id 
JOIN companies c
ON s.company_id = c.company_id
Join matches m
ON t.timestamp = m.matched_at
JOIN support_staff st
on m.staff_id = st.staff_id
WHERE t.status = 'active'

"""

active_support_tickets= pd.read_sql( query_1, conn)

# for better intuitive insights, company sizes can be categorised into groups : small, medium, large and very large groups

bins = [0, 10, 20, 30, 47]
labels = ['Small', 'Medium', 'Large', 'Very_Large']
active_support_tickets['size_category'] = pd.cut(active_support_tickets['company_size'], bins = bins, labels= labels)


app = dash.Dash()

app.layout = html.Div([
    html.H1("Wait Time Analysis Dashboard"),
    
  
    dcc.Dropdown(
        id='resample_type',
        options=[ {'label': 'Daily', 'value': 'daily'}, {'label': 'Weekly', 'value': 'weekly'}],
        value='daily', 
        style={'width': '50%'} ),

    dcc.Dropdown(
        id='company_size_filter',
        options=[
            {'label': 'All', 'value': 'All'},  
            {'label': 'Small', 'value': 'Small'},
            {'label': 'Medium', 'value': 'Medium'},
            {'label': 'Large', 'value': 'Large'},
            {'label': 'Very_Large', 'value': 'Very_Large'}
            
        ],
        value='All', 
        style={'width': '50%', 'margin-top': '20px'}
    ),
    
    dcc.Graph(id='wait_time_plot')
])

@app.callback(
    Output('wait_time_plot', 'figure'),
    [Input('resample_type', 'value'),Input('company_size_filter', 'value')]
)

def update_plot(selected_resampling, selected_size_category):
    
    if selected_size_category == 'All':
        filtered_data = active_support_tickets
    else:
        filtered_data = active_support_tickets[active_support_tickets['size_category'] == selected_size_category]

    if selected_resampling == 'daily':
        data_to_plot = filtered_data.set_index('created_at')['wait_time'].resample('D').mean()
        title = f"Daily Average Wait Time ({selected_size_category} companies)"
    else:
        data_to_plot = filtered_data.set_index('created_at')['wait_time'].resample('W').mean()
        title = f"Weekly Average Wait Time ({selected_size_category} companies)"
    
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=data_to_plot.index,y=data_to_plot.values))
    figure.update_layout( title = title, xaxis_title='Date',yaxis_title='Average Wait Time (Min)', template='plotly')
    
    return figure

app.run_server(host="0.0.0.0",port=8080)

