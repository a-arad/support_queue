import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

def sql_ready_dates(tables):
    """why? to smooth things with postgres"""
    for table in tables:
        for col in tables[table].columns:
            if pd.api.types.is_datetime64_any_dtype(tables[table][col]):
                tables[table][col] = tables[table][col].astype(str)
            elif pd.api.types.is_numeric_dtype(tables[table][col]):
                tables[table][col] = tables[table][col].astype(int)
    return tables

params = {
    'NUM_COMPANIES' :  50,
    'NUM_USERS' : 1000,
    'NUM_SUPPORT_STAFF' : 50,
    'NUM_TICKETS' :5000, 
    'TICKET_CATEGORIES' :['Technical', 'Billing', 'Account', 'General Inquiry'],
    'mean' : 2 ,
    'sigma' :1,
    'user_probs_limit' : 100

    }
def support_queue_data_generator(params):

    company_sizes = np.random.lognormal(mean= params['mean'], sigma=params['sigma'], size=params['NUM_COMPANIES'])

    companies = pd.DataFrame({
        'company_id': range(1, params['NUM_COMPANIES'] + 1),
        'company_name': [f'Company_{i}' for i in range(1, params['NUM_COMPANIES'] + 1)],
        'company_size': company_sizes
    })

    # normalize company size to obtain a distribution
    company_size_probs = company_sizes / company_sizes.sum()

    # users
    user_company_distribution = np.random.choice(companies['company_id'], params['NUM_USERS'], p=company_size_probs)
    users = pd.DataFrame({
        'user_id': range(1,  params['NUM_USERS'] + 1),
        'user_name': [f'User_{i}' for i in range(1,  params['NUM_USERS'] + 1)],
        'company_id': user_company_distribution
    })

    # staff table
    support_staff = pd.DataFrame({
        'staff_id': range(1, params['NUM_SUPPORT_STAFF'] + 1),
        'staff_name': [f'Staff_{i}' for i in range(1, params['NUM_SUPPORT_STAFF'] + 1)],
        'experience_level': np.random.choice(['Junior', 'Mid', 'Senior'], params['NUM_SUPPORT_STAFF'], p=[0.4, 0.4, 0.2])
    })

    # tickets
    def random_date(start, end):
        return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

    start_date = datetime.now() - timedelta(days=180)
    end_date = datetime.now()

    ticket_ids = range(1, params['NUM_TICKETS'] + 1)
    user_probs = np.array([0.05 if i <= params['user_probs_limit'] else 0.95/(params['NUM_USERS']-params['user_probs_limit']) for i in range(1, params['NUM_USERS'] + 1)])
    user_probs = user_probs/user_probs.sum()

    ticket_data = []
    for ticket_id in ticket_ids:
        user_id = np.random.choice(users['user_id'], p=user_probs)
        company_id = users.loc[users['user_id'] == user_id, 'company_id'].values[0]
        issue_category = np.random.choice(params['TICKET_CATEGORIES'], p=[0.5, 0.2, 0.2, 0.1])
        created_at = random_date(start_date, end_date)
        ticket_data.append((ticket_id, user_id, company_id, issue_category, created_at))

    tickets = pd.DataFrame(ticket_data, columns=['ticket_id', 'user_id', 'company_id', 'issue_category', 'created_at'])

    # matches
    # probability distribution over matching times
    # how many minutes go by between created_at and matched_at
    matches = pd.DataFrame({
        'ticket_id': tickets['ticket_id'],
        'staff_id': np.random.choice(support_staff['staff_id'], params['NUM_TICKETS']),
        'matched_at': [random_date(pd.Timestamp(tickets.loc[tickets['ticket_id'] == ticket_id, 'created_at'].values[0]),
                                   pd.Timestamp(tickets.loc[tickets['ticket_id'] == ticket_id, 'created_at'].values[0]) + pd.Timedelta(seconds = 120 + round(np.random.lognormal(2,1,1)[0]*60))) for ticket_id in ticket_ids]
    })

    ##### ticket status
    ticket_status_data = []

    # first active status
    for ticket_id in ticket_ids:
        status = 'active'
        timestamp = pd.Timestamp(matches.loc[tickets['ticket_id'] == ticket_id, 'matched_at'].values[0])
        ticket_status_data.append((ticket_id, status, timestamp))

    # how long does it take to resolve
    # first inactive
    for ticket_id in ticket_ids:
        status = 'inactive'
        timestamp = pd.Timestamp(matches.loc[tickets['ticket_id'] == ticket_id, 'matched_at'].values[0]) + pd.Timedelta(seconds = round(np.random.lognormal(3,.3,1)[0]*60))
        ticket_status_data.append((ticket_id, status, timestamp))

    ticket_status = pd.DataFrame(ticket_status_data, columns=['ticket_id', 'status', 'timestamp'])

    return_dict = {"companies":companies,
                   "users":users,
                   "support_staff":support_staff,
                   "support_tickets":tickets,
                   "ticket_status":ticket_status,
                   "matches":matches}
    
    return_dict = sql_ready_dates(return_dict)

    return return_dict 


