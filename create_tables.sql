-- Create tables
CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    company_size INTEGER NOT NULL
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    company_id INTEGER REFERENCES companies(company_id)
);

CREATE TABLE support_staff (
    staff_id SERIAL PRIMARY KEY,
    staff_name TEXT NOT NULL,
    experience_level TEXT NOT NULL
);

CREATE TABLE support_tickets (
    ticket_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    company_id INTEGER REFERENCES companies(company_id),
    issue_category TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE ticket_status (
    status_id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES support_tickets(ticket_id),
    status TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

CREATE TABLE matches (
    match_id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES support_tickets(ticket_id),
    staff_id INTEGER REFERENCES support_staff(staff_id),
    matched_at TIMESTAMP NOT NULL
);
