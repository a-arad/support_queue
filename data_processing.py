import pandas as pd
from sqlalchemy import create_engine, text
import os

def load_and_process():
    try:
        # Ensure you have the correct database URL
        db_url = os.getenv('DATABASE_URL', 'postgresql://readonly.isypnmrsdydmdvvnyxce:n5ZLPLyEtq@aws-0-us-east-1.pooler.supabase.com:6543/postgres')
        
        print("Connecting to the database...")
        engine = create_engine(db_url)

        # Querying using SQLAlchemy text() method
        query_companies = text("SELECT * FROM companies")
        query_tickets = text("SELECT * FROM support_tickets")
        query_matches = text("SELECT * FROM matches")
        query_status = text("SELECT * FROM ticket_status")
        query_support_staff = text("SELECT * FROM support_staff")

        # Executing the queries and loading them into pandas dataframes
        with engine.connect() as connection:
            df_companies = pd.read_sql(query_companies, con=connection)
            df_tickets = pd.read_sql(query_tickets, con=connection)
            df_matches = pd.read_sql(query_matches, con=connection)
            df_status = pd.read_sql(query_status, con=connection)
            df_support_staff = pd.read_sql(query_support_staff, con=connection)

        # Now that the dataframes are loaded, process them as usual
        # Datetime columns to the correct format
        df_tickets['created_at'] = pd.to_datetime(df_tickets['created_at'])
        df_matches['matched_at'] = pd.to_datetime(df_matches['matched_at'])
        df_status['timestamp'] = pd.to_datetime(df_status['timestamp'])

        # Combining initial dataframes into interim dataframe -> df_interim
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

        median_company_size = df['company_size'].median()
        df['company_size_category'] = df['company_size'].apply(lambda x: 'small' if x <= median_company_size else 'large')

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

    except Exception as e:
        print(f"Error connecting to the database or executing query: {e}")
        return None

# Running the function if the script is executed
if __name__ == '__main__':
    df, dftm, dft_dash = load_and_process()
    if df is not None:
        print(df.head(2))