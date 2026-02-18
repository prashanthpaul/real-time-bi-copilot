"""
Claude AI Client Utility
==========================
Handles Anthropic API integration with prompt templates,
response parsing, error handling, and token tracking.
"""

import json
import logging
import time
from typing import Any

from anthropic import Anthropic, APIError, RateLimitError

logger = logging.getLogger(__name__)


class AIClient:
    """Client for Claude API interactions."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0
        logger.info(f"AIClient initialized with model: {model}")

    def analyze(
        self, prompt: str, system: str = "", max_tokens: int = 4096, _retries: int = 0
    ) -> dict[str, Any]:
        """
        Send an analysis request to Claude and return structured results.

        Returns:
            {
                "response": str,
                "input_tokens": int,
                "output_tokens": int,
                "latency_ms": float
            }
        """
        MAX_RETRIES = 3
        start = time.time()
        try:
            messages = [{"role": "user", "content": prompt}]
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system

            response = self.client.messages.create(**kwargs)

            elapsed = round((time.time() - start) * 1000, 2)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.request_count += 1

            text = response.content[0].text
            logger.info(
                f"AI response received in {elapsed}ms "
                f"(tokens: {input_tokens} in / {output_tokens} out)"
            )

            return {
                "response": text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": elapsed,
            }

        except RateLimitError as e:
            elapsed = round((time.time() - start) * 1000, 2)
            if _retries >= MAX_RETRIES:
                logger.error(f"Rate limited {MAX_RETRIES} times, giving up.")
                return {
                    "error": f"Rate limited after {MAX_RETRIES} retries: {e}",
                    "type": "RateLimitError",
                    "latency_ms": elapsed,
                }
            wait = 30 * (2 ** _retries)  # 30s, 60s, 120s backoff
            logger.warning(f"Rate limited (attempt {_retries + 1}/{MAX_RETRIES}). Retrying in {wait}s...")
            time.sleep(wait)
            return self.analyze(prompt, system, max_tokens, _retries=_retries + 1)

        except APIError as e:
            elapsed = round((time.time() - start) * 1000, 2)
            logger.error(f"API error after {elapsed}ms: {e}")
            return {
                "error": str(e),
                "type": "APIError",
                "latency_ms": elapsed,
            }

    def generate_sql(self, natural_language: str, schema_info: str) -> dict[str, Any]:
        """Convert natural language to SQL using Claude."""
        system = (
            "You are a SQL expert. Convert the user's natural language question into a "
            "DuckDB-compatible SQL query. Return ONLY the SQL query, no explanation. "
            "Use the schema information provided to write accurate queries."
        )
        prompt = f"Schema:\n{schema_info}\n\nQuestion: {natural_language}"
        result = self.analyze(prompt, system=system, max_tokens=1024)

        if "error" not in result:
            sql = result["response"].strip()
            # Strip markdown code fences if present
            if sql.startswith("```"):
                lines = sql.split("\n")
                sql = "\n".join(lines[1:-1])
            result["sql"] = sql

        return result

    def generate_insights(self, data_summary: str, question: str = "") -> dict[str, Any]:
        """Generate business insights from data."""
        system = (
            "You are a senior business analyst. Analyze the data provided and generate "
            "actionable business insights. Structure your response as JSON with keys: "
            '"summary", "key_findings" (list), "recommendations" (list), "risk_factors" (list).'
        )
        prompt = f"Data Summary:\n{data_summary}"
        if question:
            prompt += f"\n\nSpecific Question: {question}"

        result = self.analyze(prompt, system=system)

        if "error" not in result:
            result["insights"] = _parse_json_response(result["response"])

        return result

    def explain_anomaly(self, anomaly_data: str, context: str = "") -> dict[str, Any]:
        """Get AI explanation for detected anomalies."""
        system = (
            "You are a data analyst specializing in anomaly detection. "
            "Explain the anomaly in business terms and suggest possible causes. "
            'Return JSON with keys: "explanation", "possible_causes" (list), '
            '"severity" (low/medium/high/critical), "recommended_actions" (list).'
        )
        prompt = f"Anomaly Data:\n{anomaly_data}"
        if context:
            prompt += f"\n\nBusiness Context:\n{context}"

        result = self.analyze(prompt, system=system)

        if "error" not in result:
            result["analysis"] = _parse_json_response(result["response"])

        return result

    def get_usage_stats(self) -> dict:
        """Return cumulative API usage statistics."""
        return {
            "total_requests": self.request_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }


def _parse_json_response(text: str) -> dict | None:
    """Extract JSON from a Claude response that may contain markdown."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        if "```" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
        logger.warning("Could not parse JSON from AI response")
        return None
