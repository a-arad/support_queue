import os
from supabase import create_client, Client
from data_generator import *
from dotenv import load_dotenv
load_dotenv()

supabase: Client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

tables = support_queue_data_generator()

for table in tables:
    try:
        dict_data = tables[table].to_dict(orient='records')
        response = supabase.table(table).insert(dict_data).execute()
    except:
        print(f"problem posting {table}\n{response}")