import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import os

# --- Load CSVs ---
tickets = pd.read_csv("data/tickets.csv")
agents = pd.read_csv("data/agents.csv")
tickets["open_date"] = pd.to_datetime(tickets["open_date"])
tickets["resolution_date"] = pd.to_datetime(tickets["resolution_date"])

print(f"✅ Data loaded: {len(tickets):,} tickets, {len(agents):,} agents")

# --- Load into SQLite ---
conn = sqlite3.connect("data/operationsiq.db")
tickets.to_sql("tickets", conn, if_exists="replace", index=False)
agents.to_sql("agents", conn, if_exists="replace", index=False)
print("✅ Data loaded into SQLite database")

# --- SQL Queries ---

# 1. Support volume by department
volume_by_dept = pd.read_sql_query("""
    SELECT 
        department,
        COUNT(ticket_id) AS total_tickets,
        SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_tickets,
        ROUND(100.0 * SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) / COUNT(ticket_id), 2) AS resolution_rate_pct
    FROM tickets
    GROUP BY department
    ORDER BY total_tickets DESC
""", conn)

# 2. Resolution time by priority
resolution_by_priority = pd.read_sql_query("""
    SELECT 
        priority,
        COUNT(ticket_id) AS total_tickets,
        ROUND(AVG(resolution_days), 2) AS avg_resolution_days,
        sla_target_days
    FROM tickets
    WHERE resolution_days IS NOT NULL
    GROUP BY priority, sla_target_days
    ORDER BY sla_target_days ASC
""", conn)

# 3. SLA compliance by department
sla_by_dept = pd.read_sql_query("""
    SELECT 
        department,
        COUNT(ticket_id) AS total_tickets,
        SUM(sla_met) AS sla_met_count,
        ROUND(100.0 * SUM(sla_met) / COUNT(ticket_id), 2) AS sla_compliance_pct
    FROM tickets
    GROUP BY department
    ORDER BY sla_compliance_pct DESC
""", conn)

# 4. Ticket volume by category
volume_by_category = pd.read_sql_query("""
    SELECT 
        category,
        COUNT(ticket_id) AS total_tickets,
        ROUND(AVG(resolution_days), 2) AS avg_resolution_days,
        ROUND(AVG(satisfaction_score), 2) AS avg_satisfaction
    FROM tickets
    WHERE resolution_days IS NOT NULL
    GROUP BY category
    ORDER BY total_tickets DESC
""", conn)

# 5. Monthly ticket trend
monthly_trend = pd.read_sql_query("""
    SELECT 
        strftime('%Y-%m', open_date) AS month,
        COUNT(ticket_id) AS total_tickets,
        SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved,
        SUM(CASE WHEN status = 'Escalated' THEN 1 ELSE 0 END) AS escalated,
        ROUND(AVG(satisfaction_score), 2) AS avg_satisfaction
    FROM tickets
    GROUP BY month
    ORDER BY month ASC
""", conn)

# 6. Agent performance
agent_performance = pd.read_sql_query("""
    SELECT 
        a.agent_id,
        a.agent_name,
        a.seniority,
        COUNT(t.ticket_id) AS tickets_handled,
        ROUND(AVG(t.resolution_days), 2) AS avg_resolution_days,
        ROUND(AVG(t.satisfaction_score), 2) AS avg_satisfaction,
        SUM(t.sla_met) AS sla_met_count
    FROM agents a
    JOIN tickets t ON a.agent_id = t.agent_id
    GROUP BY a.agent_id, a.agent_name, a.seniority
    ORDER BY avg_satisfaction DESC
    LIMIT 10
""", conn)

# 7. Data quality report
data_quality = pd.read_sql_query("""
    SELECT 
        COUNT(*) AS total_tickets,
        SUM(CASE WHEN resolution_days IS NULL THEN 1 ELSE 0 END) AS missing_resolution_days,
        SUM(CASE WHEN satisfaction_score IS NULL THEN 1 ELSE 0 END) AS missing_satisfaction,
        SUM(CASE WHEN resolution_date IS NULL THEN 1 ELSE 0 END) AS missing_resolution_date
    FROM tickets
""", conn)

conn.close()
print("✅ SQL queries executed successfully")

# --- Data Validation ---
print("\n" + "="*50)
print("OperationsIQ: Automated Data Validation Report")
print("="*50)

# Check 1: Missing records
print("\n[1] Missing Records Check")
for col in ["resolution_days", "satisfaction_score", "resolution_date"]:
    missing = tickets[col].isnull().sum()
    pct = 100 * missing / len(tickets)
    print(f"    {col}: {missing:,} missing ({pct:.1f}%)")

# Check 2: Schema mismatch
print("\n[2] Schema Mismatch Check")
valid_statuses = ["Resolved", "Open", "Escalated"]
valid_priorities = ["Low", "Medium", "High", "Critical"]
invalid_status = tickets[~tickets["status"].isin(valid_statuses)]
invalid_priority = tickets[~tickets["priority"].isin(valid_priorities)]
print(f"    status: {len(invalid_status)} invalid values found")
print(f"    priority: {len(invalid_priority)} invalid values found")

# Check 3: Duplicate tickets
print("\n[3] Duplicate Records Check")
dupes = tickets.duplicated(subset=["ticket_id"]).sum()
print(f"    ticket_id duplicates: {dupes}")

# Check 4: Date integrity
print("\n[4] Date Integrity Check")
invalid_dates = tickets.dropna(subset=["resolution_date"])
invalid_dates = invalid_dates[invalid_dates["resolution_date"] < invalid_dates["open_date"]]
print(f"    resolution_date before open_date: {len(invalid_dates)} records")

# Check 5: SLA compliance summary
print("\n[5] SLA Compliance Summary")
for priority in ["Critical", "High", "Medium", "Low"]:
    subset = tickets[tickets["priority"] == priority]
    compliance = subset["sla_met"].mean() * 100
    print(f"    {priority}: {compliance:.1f}% SLA compliance")

print("\n" + "="*50)
print("Validation Complete")
print("="*50)

# --- Save outputs ---
os.makedirs("outputs", exist_ok=True)
volume_by_dept.to_csv("outputs/volume_by_dept.csv", index=False)
resolution_by_priority.to_csv("outputs/resolution_by_priority.csv", index=False)
sla_by_dept.to_csv("outputs/sla_by_dept.csv", index=False)
volume_by_category.to_csv("outputs/volume_by_category.csv", index=False)
monthly_trend.to_csv("outputs/monthly_trend.csv", index=False)
agent_performance.to_csv("outputs/agent_performance.csv", index=False)
data_quality.to_csv("outputs/data_quality_report.csv", index=False)
print("\n✅ Query results saved to outputs/")

# --- Charts ---
sns.set_theme(style="whitegrid")
os.makedirs("outputs/charts", exist_ok=True)

# Chart 1: Support volume by department
plt.figure(figsize=(10, 6))
sns.barplot(data=volume_by_dept, x="total_tickets", y="department", color="steelblue")
plt.title("Support Volume by Department", fontsize=14, fontweight="bold")
plt.xlabel("Total Tickets")
plt.ylabel("Department")
plt.tight_layout()
plt.savefig("outputs/charts/volume_by_dept.png")
plt.close()

# Chart 2: Resolution rate by department
plt.figure(figsize=(10, 6))
sns.barplot(data=volume_by_dept, x="resolution_rate_pct", y="department", color="green")
plt.title("Resolution Rate by Department (%)", fontsize=14, fontweight="bold")
plt.xlabel("Resolution Rate (%)")
plt.ylabel("Department")
plt.tight_layout()
plt.savefig("outputs/charts/resolution_rate.png")
plt.close()

# Chart 3: SLA compliance by department
plt.figure(figsize=(10, 6))
sns.barplot(data=sla_by_dept, x="sla_compliance_pct", y="department", color="orange")
plt.title("SLA Compliance by Department (%)", fontsize=14, fontweight="bold")
plt.xlabel("SLA Compliance (%)")
plt.ylabel("Department")
plt.tight_layout()
plt.savefig("outputs/charts/sla_compliance.png")
plt.close()

# Chart 4: Monthly ticket trend
plt.figure(figsize=(14, 5))
plt.plot(monthly_trend["month"], monthly_trend["total_tickets"],
         marker="o", color="steelblue", linewidth=2, label="Total Tickets")
plt.plot(monthly_trend["month"], monthly_trend["resolved"],
         marker="s", color="green", linewidth=2, label="Resolved")
plt.plot(monthly_trend["month"], monthly_trend["escalated"],
         marker="^", color="red", linewidth=2, label="Escalated")
plt.title("Monthly Ticket Trend", fontsize=14, fontweight="bold")
plt.xlabel("Month")
plt.ylabel("Number of Tickets")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig("outputs/charts/monthly_trend.png")
plt.close()

# Chart 5: Avg resolution days vs SLA target by priority
plt.figure(figsize=(10, 6))
x = range(len(resolution_by_priority))
width = 0.35
plt.bar([i - width/2 for i in x], resolution_by_priority["avg_resolution_days"],
        width, label="Avg Resolution Days", color="steelblue")
plt.bar([i + width/2 for i in x], resolution_by_priority["sla_target_days"],
        width, label="SLA Target Days", color="orange")
plt.xticks(list(x), resolution_by_priority["priority"])
plt.title("Avg Resolution Days vs SLA Target by Priority", fontsize=14, fontweight="bold")
plt.xlabel("Priority")
plt.ylabel("Days")
plt.legend()
plt.tight_layout()
plt.savefig("outputs/charts/resolution_vs_sla.png")
plt.close()

print("✅ All charts saved to outputs/charts/")
print("\n📊 Summary Insights:")
print(f"   Total Tickets:        {len(tickets):,}")
print(f"   Overall Resolution:   {(tickets['status'] == 'Resolved').mean():.1%}")
print(f"   Overall SLA Met:      {tickets['sla_met'].mean():.1%}")
print(f"   Avg Satisfaction:     {tickets['satisfaction_score'].mean():.2f}/5")
print(f"   Top Department:       {volume_by_dept.iloc[0]['department']} ({volume_by_dept.iloc[0]['total_tickets']} tickets)")