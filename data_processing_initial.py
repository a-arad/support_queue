import pandas as pd
from sqlalchemy import create_engine
import numpy as np
from dotenv import load_dotenv
import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning, message="pandas only supports SQLAlchemy connectable")

load_dotenv()

db_con_string = os.getenv('READONLY_DB')

def load_and_process():
    engine = create_engine(db_con_string)

    # to manage the raw connection 🙄 🤯
    connection = engine.raw_connection()
    
    try:
        # to pass this raw connection to pandas read_sql
        df_companies = pd.read_sql('select * from companies', connection)
        df_tickets = pd.read_sql('select * from support_tickets', connection)
        df_matches = pd.read_sql('select * from matches', connection)
        df_status = pd.read_sql('select * from ticket_status', connection)
        df_support_staff = pd.read_sql('select * from support_staff', connection)
    finally:       
        connection.close()

    
    df_tickets['created_at'] = pd.to_datetime(df_tickets['created_at'])
    df_matches['matched_at'] = pd.to_datetime(df_matches['matched_at'])
    df_status['timestamp'] = pd.to_datetime(df_status['timestamp'])

    ticket_match = pd.merge(df_tickets, df_matches, on="ticket_id", how="left")
    ticket_match['wait_time'] = ticket_match['matched_at'] - ticket_match['created_at']
    ticket_match_companies = pd.merge(ticket_match, df_companies, on="company_id", how="left")
    ticket_match_companies_status = pd.merge(ticket_match_companies, df_status, on='ticket_id', how='left')
    
    ticket_match_companies_status['wait_time_minutes'] = ticket_match_companies_status['wait_time'].dt.total_seconds() / 60
    ticket_match_companies_status['solve_time'] = ticket_match_companies_status['timestamp'] - ticket_match_companies_status['matched_at']
    ticket_match_companies_status['solve_time_minutes'] = ticket_match_companies_status['solve_time'].dt.total_seconds() / 60
    
    df_interim = pd.merge(ticket_match_companies_status, df_support_staff, on='staff_id', how='left')
    df_interim.drop(columns=['staff_name', 'company_name', 'status_id'], inplace=True)

    active_df = df_interim[df_interim['status'] == 'active'][['ticket_id', 'timestamp']].rename(columns={'timestamp': 'active_status'})
    inactive_df = df_interim[df_interim['status'] == 'inactive'][['ticket_id', 'timestamp']].rename(columns={'timestamp': 'inactive_status'})
    consolidated_df = pd.merge(active_df, inactive_df, on='ticket_id', how='inner')

    df = pd.merge(consolidated_df, df_interim, on='ticket_id')
    df = df[1::2].reset_index(drop=True)
    df.drop(columns=['match_id', 'status', 'timestamp'], inplace=True)

    median_company_size = np.percentile(df['company_size'], 50)
    df['company_size_category'] = np.where(df['company_size'] <= median_company_size, 'small', 'large')
    
    def assign_waiting_zone(minutes):
        if minutes > 60:
            return 'red'
        elif minutes > 30:
            return 'amber'
        else:
            return 'green'
    df['waiting_zone'] = df['wait_time_minutes'].apply(assign_waiting_zone)

    dftm = df.copy(deep=True)
    dftm.set_index('created_at', inplace=True)

    dft_dash = df.copy(deep=True)

    return df, dftm, dft_dash

if __name__ == '__main__':
    df, dftm, dft_dash = load_and_process()
    print(df.head(2))