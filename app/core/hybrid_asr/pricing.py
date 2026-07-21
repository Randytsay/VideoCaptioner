"""Versioned, local estimates for model usage.

The provider reports token counts, while Cloud Billing is the source of truth
for charged and credit-offset amounts. Keeping the rates in a data object lets
the caller update them when Google changes a SKU without changing provider code.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import UsageMetrics


@dataclass(frozen=True, slots=True)
class TokenPricing:
    """USD prices per one million tokens for a specific model and request type."""

    input_usd_per_million: float
    output_usd_per_million: float
    cached_input_usd_per_million: float | None = None
    pricing_version: str = "user-configured"

    def __post_init__(self) -> None:
        for name in (
            "input_usd_per_million",
            "output_usd_per_million",
            "cached_input_usd_per_million",
        ):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True, slots=True)
class UsageCostEstimate:
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    estimated_cost_usd: float
    pricing_version: str


def estimate_token_cost(usage: UsageMetrics, pricing: TokenPricing) -> UsageCostEstimate:
    """Estimate a request cost from provider-reported tokens.

    Audio-only transcription uses the configured input rate. If the request
    includes a substantial text prompt or a cache, the exact invoice can differ;
    this deliberately remains an estimate.
    """

    input_tokens = usage.input_tokens or 0
    output_tokens = (usage.output_tokens or 0) + (usage.reasoning_tokens or 0)
    cached_input_tokens = usage.cached_input_tokens or 0
    uncached_input_tokens = max(0, input_tokens - cached_input_tokens)
    cached_rate = pricing.cached_input_usd_per_million
    if cached_rate is None:
        cached_rate = pricing.input_usd_per_million
    cost = (
        uncached_input_tokens * pricing.input_usd_per_million
        + cached_input_tokens * cached_rate
        + output_tokens * pricing.output_usd_per_million
    ) / 1_000_000
    return UsageCostEstimate(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached_input_tokens,
        estimated_cost_usd=cost,
        pricing_version=pricing.pricing_version,
    )
