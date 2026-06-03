import pandas as pd
import numpy as np
from faker import Faker
import random
import os

fake = Faker()
np.random.seed(42)
random.seed(42)

print("Generating OperationsIQ data...")

# --- Support Tickets ---
n_tickets = 10000
ticket_ids = [f"TKT_{i:05d}" for i in range(1, n_tickets + 1)]

departments = ["IT", "HR", "Finance", "Operations", "Facilities"]
categories = ["Hardware", "Software", "Access", "Payroll", "Maintenance", "Network", "Onboarding"]
priorities = ["Low", "Medium", "High", "Critical"]
statuses = ["Resolved", "Resolved", "Resolved", "Open", "Escalated"]

open_date = [fake.date_between(start_date="-2y", end_date="-1d") for _ in range(n_tickets)]
resolution_days = [random.randint(1, 30) if random.random() > 0.2 else None for _ in range(n_tickets)]

tickets = pd.DataFrame({
    "ticket_id": ticket_ids,
    "department": [random.choice(departments) for _ in range(n_tickets)],
    "category": [random.choice(categories) for _ in range(n_tickets)],
    "priority": [random.choice(priorities) for _ in range(n_tickets)],
    "status": [random.choice(statuses) for _ in range(n_tickets)],
    "open_date": open_date,
    "resolution_days": resolution_days,
    "agent_id": [f"AGT_{random.randint(1, 50):03d}" for _ in range(n_tickets)],
    "satisfaction_score": [random.randint(1, 5) if random.random() > 0.3 else None for _ in range(n_tickets)],
})

tickets["open_date"] = pd.to_datetime(tickets["open_date"])
tickets["resolution_date"] = tickets.apply(
    lambda r: r["open_date"] + pd.Timedelta(days=int(r["resolution_days"]))
    if pd.notna(r["resolution_days"]) else None, axis=1
)

# --- Agents ---
agents = pd.DataFrame({
    "agent_id": [f"AGT_{i:03d}" for i in range(1, 51)],
    "agent_name": [fake.name() for _ in range(50)],
    "department": [random.choice(departments) for _ in range(50)],
    "hire_date": [fake.date_between(start_date="-5y", end_date="-6m") for _ in range(50)],
    "seniority": [random.choice(["Junior", "Mid", "Senior"]) for _ in range(50)],
})

# --- SLA Compliance ---
tickets["sla_target_days"] = tickets["priority"].map({
    "Critical": 1, "High": 3, "Medium": 7, "Low": 14
})
tickets["sla_met"] = tickets.apply(
    lambda r: 1 if r["resolution_days"] is not None and r["resolution_days"] <= r["sla_target_days"] else 0,
    axis=1
)

# --- Save ---
os.makedirs("data", exist_ok=True)
tickets.to_csv("data/tickets.csv", index=False)
agents.to_csv("data/agents.csv", index=False)

print("✅ Data generated successfully!")
print(f"   Tickets: {len(tickets):,} rows")
print(f"   Agents:  {len(agents):,} rows")
print(f"   Resolution Rate: {(tickets['status'] == 'Resolved').mean():.1%}")
print(f"   SLA Compliance:  {tickets['sla_met'].mean():.1%}")