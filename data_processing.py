import pandas as pd
from sqlalchemy import create_engine
import numpy as np

def load_and_process():
    engine = create_engine('postgresql://readonly.isypnmrsdydmdvvnyxce:n5ZLPLyEtq@aws-0-us-east-1.pooler.supabase.com:6543/postgres')
    
    # Creating initial dataframes by reading SQL tables
    df_companies = pd.read_sql('select * from companies', engine)
    df_tickets = pd.read_sql('select * from support_tickets', engine) 
    df_matches = pd.read_sql('select * from matches', engine)
    df_status = pd.read_sql('select * from ticket_status', engine)
    df_support_staff = pd.read_sql('select * from support_staff', engine)

    # Datetime columns to the correct format (if they weren't)
    df_tickets['created_at'] = pd.to_datetime(df_tickets['created_at'])
    df_matches['matched_at'] = pd.to_datetime(df_matches['matched_at'])
    df_status['timestamp'] = pd.to_datetime(df_status['timestamp'])

    # Combining initial dataframes into interim dataframe -> df_interim
    ticket_match = pd.merge(df_tickets, df_matches, on="ticket_id", how="left")
    ticket_match['wait_time'] = ticket_match['matched_at'] - ticket_match['created_at']
    ticket_match_companies = pd.merge(ticket_match, df_companies, on="company_id", how="left")
    ticket_match_companies_status = pd.merge(ticket_match_companies, df_status, on='ticket_id', how='left')
    
    # Adding new calculated columns
    ticket_match_companies_status['wait_time_minutes'] = ticket_match_companies_status['wait_time'].dt.total_seconds() / 60
    ticket_match_companies_status['solve_time'] = ticket_match_companies_status['timestamp'] - ticket_match_companies_status['matched_at']
    ticket_match_companies_status['solve_time_minutes'] = ticket_match_companies_status['solve_time'].dt.total_seconds() / 60
    
    # Merging ticket_match_companies_status with df_support_staff and dropping unnecessary columns
    df_interim = pd.merge(ticket_match_companies_status, df_support_staff, on='staff_id', how='left')
    df_interim.drop(columns=['staff_name', 'company_name', 'status_id'], inplace=True)

    # Reshaping df_interim by adding active and inactive separate columns(instead of being rows in timestamp column)
    active_df = df_interim[df_interim['status'] == 'active'][['ticket_id', 'timestamp']].rename(columns={'timestamp': 'active_status'})
    inactive_df = df_interim[df_interim['status'] == 'inactive'][['ticket_id', 'timestamp']].rename(columns={'timestamp': 'inactive_status'})
    consolidated_df = pd.merge(active_df, inactive_df, on='ticket_id', how='inner')

    # Creating working dataframe df
    df = pd.merge(consolidated_df, df_interim, on='ticket_id')
    df = df[1::2].reset_index(drop=True)
    df.drop(columns=['match_id', 'status', 'timestamp'], inplace=True)

    # Defining company sizes and tickets waiting time zones
    median_company_size = np.percentile(df['company_size'], 50)
    df['company_size_category'] = np.where(df['company_size'] <= median_company_size, 'small', 'large')
    
    # Assign waiting zone
    def assign_waiting_zone(minutes):
        if minutes > 60:
            return 'red'
        elif minutes > 30:
            return 'amber'
        else:
            return 'green'
    df['waiting_zone'] = df['wait_time_minutes'].apply(assign_waiting_zone)

    # Creating dftm dataframe for TSA with datetime index
    dftm = df.copy(deep=True)
    dftm.set_index('created_at', inplace=True)

    # Creating dft_dash dataframe specifically for dashboard
    dft_dash = df.copy(deep=True)
    
    return df, dftm, dft_dash
"""
if __name__ == '__main__':
    df, dftm, dft_dash = load_and_process()
    print(df.head(2))
"""    