# API Reference

## MCP Tools

### `query_database`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | — | SQL query or natural language question |
| `query_type` | string | No | `"auto"` | `"sql"`, `"natural_language"`, or `"auto"` |
| `limit` | integer | No | `100` | Maximum rows to return |

**Response**:
```json
{
  "columns": ["product_name", "total_revenue"],
  "rows": [["Widget A", 50000.00]],
  "row_count": 1,
  "execution_time_ms": 12.5,
  "generated_sql": "SELECT ... (if NL input)",
  "original_question": "... (if NL input)"
}
```

### `analyze_data`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `table_name` | string | Yes | — | Table or view name |
| `columns` | string[] | No | all | Columns to analyze |
| `group_by` | string | No | — | Column to group by |

**Response**:
```json
{
  "table": "sales",
  "total_rows": 10000,
  "numeric_summary": { "revenue": { "mean": 1500.0, "std": 800.0, ... } },
  "categorical_summary": { "category": { "unique_values": 5, "top_values": {...} } },
  "data_quality": { "null_percentage": 2.3, "duplicate_rows": 50 },
  "top_correlations": [{ "col_a": "revenue", "col_b": "quantity", "correlation": 0.72 }],
  "trend": { "direction": "increasing", "overall_change_pct": 15.3 }
}
```

### `generate_insights`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `question` | string | Yes | — | Business question |
| `table_name` | string | No | `"sales"` | Table to analyze |
| `time_period` | string | No | — | Time filter |

**Response**:
```json
{
  "question": "...",
  "rows_analyzed": 10000,
  "ai_response": "...",
  "insights": {
    "summary": "...",
    "key_findings": ["..."],
    "recommendations": ["..."],
    "risk_factors": ["..."]
  },
  "tokens_used": { "input": 500, "output": 300 }
}
```

### `detect_anomalies`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `table_name` | string | No | `"sales"` | Table to scan |
| `metric_column` | string | No | `"revenue"` | Numeric column |
| `date_column` | string | No | `"transaction_date"` | Date column |
| `method` | string | No | `"zscore"` | `"zscore"` or `"iqr"` |
| `threshold` | float | No | `3.0` | Detection sensitivity |
| `explain` | boolean | No | `false` | Get AI explanation |

**Response**:
```json
{
  "anomalies_found": 15,
  "anomaly_rate_pct": 0.15,
  "baseline": { "mean": 1500.0, "std": 800.0, "median": 1200.0 },
  "severity_breakdown": { "critical": 2, "high": 5, "medium": 8 },
  "anomalies": [
    { "date": "2024-11-15", "value": 75000.0, "severity": "critical", "deviation": 8.5 }
  ],
  "ai_explanation": { "explanation": "...", "possible_causes": ["..."] }
}
```

## MCP Resources

### `bi-copilot://datasets`
Returns list of all tables and views with schema info.

### `bi-copilot://datasets/{name}`
Returns detailed info for a specific table: schema, row count, sample data.

### `bi-copilot://query-history`
Returns recent query history and performance statistics.

## Error Format

All errors follow this structure:
```json
{
  "error": "Human-readable error message",
  "type": "ExceptionClassName",
  "suggestion": "Actionable fix suggestion"
}
```
