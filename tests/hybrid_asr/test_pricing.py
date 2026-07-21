from app.core.hybrid_asr.models import UsageMetrics
from app.core.hybrid_asr.pricing import TokenPricing, estimate_token_cost


def test_cost_estimate_uses_cached_rate_and_reasoning_tokens() -> None:
    estimate = estimate_token_cost(
        UsageMetrics(
            input_tokens=2_000_000,
            output_tokens=100_000,
            reasoning_tokens=50_000,
            cached_input_tokens=500_000,
        ),
        TokenPricing(
            input_usd_per_million=1.0,
            output_usd_per_million=2.0,
            cached_input_usd_per_million=0.25,
            pricing_version="test-price",
        ),
    )

    assert estimate.input_tokens == 2_000_000
    assert estimate.output_tokens == 150_000
    assert estimate.cached_input_tokens == 500_000
    assert estimate.estimated_cost_usd == 1.925
    assert estimate.pricing_version == "test-price"
