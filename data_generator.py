import random
import string
from datetime import datetime, timedelta

def random_string(length):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

# generate companies
companies = [(i, "Company " + random_string(5)) for i in range(1, 11)]

# generate users
users = [(i, "User " + random_string(5), random.randint(1, 10)) for i in range(1, 51)]

# generate support staff
support_staff = [(i, "Staff " + random_string(5)) for i in range(1, 11)]

# generate support tickets
now = datetime.now()
support_tickets = [(i, random.randint(1, 50), "Issue " + random_string(10), (now - timedelta(minutes=random.randint(1, 1000))).strftime('%Y-%m-%d %H:%M:%S')) for i in range(1, 101)]

# generate matches
matches = [(i, random.randint(1, 100), random.randint(1, 10), (now - timedelta(minutes=random.randint(1, 1000))).strftime('%Y-%m-%d %H:%M:%S')) for i in range(1, 51)]

with open('data_generation.sql', 'w') as f:
    f.write("CREATE TABLE companies (\n")
    f.write("    company_id SERIAL PRIMARY KEY,\n")
    f.write("    company_name TEXT NOT NULL\n")
    f.write(");\n\n")
    
    f.write("CREATE TABLE users (\n")
    f.write("    user_id SERIAL PRIMARY KEY,\n")
    f.write("    name TEXT NOT NULL,\n")
    f.write("    company_id INTEGER REFERENCES companies(company_id)\n")
    f.write(");\n\n")
    
    f.write("CREATE TABLE support_staff (\n")
    f.write("    staff_id SERIAL PRIMARY KEY,\n")
    f.write("    name TEXT NOT NULL\n")
    f.write(");\n\n")
    
    f.write("CREATE TABLE support_tickets (\n")
    f.write("    ticket_id SERIAL PRIMARY KEY,\n")
    f.write("    user_id INTEGER REFERENCES users(user_id),\n")
    f.write("    issue_description TEXT NOT NULL,\n")
    f.write("    timestamp TIMESTAMP NOT NULL\n")
    f.write(");\n\n")
    
    f.write("CREATE TABLE matches (\n")
    f.write("    match_id SERIAL PRIMARY KEY,\n")
    f.write("    ticket_id INTEGER REFERENCES support_tickets(ticket_id),\n")
    f.write("    staff_id INTEGER REFERENCES support_staff(staff_id),\n")
    f.write("    match_timestamp TIMESTAMP NOT NULL\n")
    f.write(");\n\n")
    
    f.write("-- Insert companies\n")
    for company in companies:
        f.write(f"INSERT INTO companies (company_id, company_name) VALUES ({company[0]}, '{company[1]}');\n")
    
    f.write("\n-- Insert users\n")
    for user in users:
        f.write(f"INSERT INTO users (user_id, name, company_id) VALUES ({user[0]}, '{user[1]}', {user[2]});\n")
    
    f.write("\n-- Insert support staff\n")
    for staff in support_staff:
        f.write(f"INSERT INTO support_staff (staff_id, name) VALUES ({staff[0]}, '{staff[1]}');\n")
    
    f.write("\n-- Insert support tickets\n")
    for ticket in support_tickets:
        f.write(f"INSERT INTO support_tickets (ticket_id, user_id, issue_description, timestamp) VALUES ({ticket[0]}, {ticket[1]}, '{ticket[2]}', '{ticket[3]}');\n")
    
    f.write("\n-- Insert matches\n")
    for match in matches:
        f.write(f"INSERT INTO matches (match_id, ticket_id, staff_id, match_timestamp) VALUES ({match[0]}, {match[1]}, {match[2]}, '{match[3]}');\n")

print("SQL data generation script created as 'data_generation.sql'.")