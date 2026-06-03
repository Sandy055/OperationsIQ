-- =============================================
-- OperationsIQ: Data Quality & Reporting
-- =============================================

-- 1. Support volume by department
SELECT 
    department,
    COUNT(ticket_id) AS total_tickets,
    SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_tickets,
    ROUND(100.0 * SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) / COUNT(ticket_id), 2) AS resolution_rate_pct
FROM tickets
GROUP BY department
ORDER BY total_tickets DESC;

-- 2. Average resolution time by priority
SELECT 
    priority,
    COUNT(ticket_id) AS total_tickets,
    ROUND(AVG(resolution_days), 2) AS avg_resolution_days,
    MIN(resolution_days) AS min_days,
    MAX(resolution_days) AS max_days,
    sla_target_days
FROM tickets
WHERE resolution_days IS NOT NULL
GROUP BY priority, sla_target_days
ORDER BY sla_target_days ASC;

-- 3. SLA compliance by department
SELECT 
    department,
    COUNT(ticket_id) AS total_tickets,
    SUM(sla_met) AS sla_met_count,
    ROUND(100.0 * SUM(sla_met) / COUNT(ticket_id), 2) AS sla_compliance_pct
FROM tickets
GROUP BY department
ORDER BY sla_compliance_pct DESC;

-- 4. Ticket volume by category
SELECT 
    category,
    COUNT(ticket_id) AS total_tickets,
    ROUND(AVG(resolution_days), 2) AS avg_resolution_days,
    ROUND(AVG(satisfaction_score), 2) AS avg_satisfaction
FROM tickets
WHERE resolution_days IS NOT NULL
GROUP BY category
ORDER BY total_tickets DESC;

-- 5. Monthly ticket trend
SELECT 
    strftime('%Y-%m', open_date) AS month,
    COUNT(ticket_id) AS total_tickets,
    SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved,
    SUM(CASE WHEN status = 'Escalated' THEN 1 ELSE 0 END) AS escalated,
    ROUND(AVG(satisfaction_score), 2) AS avg_satisfaction
FROM tickets
GROUP BY month
ORDER BY month ASC;

-- 6. Agent performance
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
LIMIT 10;

-- 7. Data quality check — missing records
SELECT 
    COUNT(*) AS total_tickets,
    SUM(CASE WHEN resolution_days IS NULL THEN 1 ELSE 0 END) AS missing_resolution_days,
    SUM(CASE WHEN satisfaction_score IS NULL THEN 1 ELSE 0 END) AS missing_satisfaction,
    SUM(CASE WHEN resolution_date IS NULL THEN 1 ELSE 0 END) AS missing_resolution_date
FROM tickets;

-- 8. Schema mismatch check — invalid status values
SELECT 
    status,
    COUNT(*) AS count
FROM tickets
GROUP BY status
ORDER BY count DESC;