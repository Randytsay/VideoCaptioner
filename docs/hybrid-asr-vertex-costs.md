# Vertex AI Gemini full-cloud mode and cost records

## Scope

`GeminiVertexTranscriber` is the Hybrid ASR provider for a full-cloud run: every
prepared audio segment is sent to Gemini on Vertex AI. It uses Application
Default Credentials (ADC), not the existing Gemini Developer API key field.

The provider returns faithful transcript text. A configured forced aligner still
owns final SRT timestamps.

## Local setup

Install the optional SDK in the VideoCaptioner environment:

```bash
uv sync --extra vertex
```

Select the Google Cloud project that is linked to the intended Billing account,
enable Vertex AI, then create local ADC credentials:

```bash
gcloud services enable aiplatform.googleapis.com --project PROJECT_ID
gcloud auth application-default login
gcloud auth application-default set-quota-project PROJECT_ID
```

Do not put a service-account key, API key, or credential path into this
repository. ADC is stored outside the repository by the Google Cloud CLI.

## Mode selection

Inject `GeminiVertexTranscriber(GeminiVertexConfig(...))` into
`SegmentPipeline` to select a full-cloud transcription run. The existing PyQt
workflow is deliberately unchanged until the CLI/orchestrator has completed
real Vertex integration testing.

```python
from app.core.hybrid_asr import GeminiVertexConfig, GeminiVertexTranscriber

transcriber = GeminiVertexTranscriber(
    GeminiVertexConfig(project="vertex-trial-300", model="gemini-2.5-flash")
)
```

Use the project that is linked to the US$300 trial Billing account when the
goal is to spend that credit. A project can only have one linked Cloud Billing
account at a time.

## Usage versus billing

For every Gemini response, the provider stores the response's reported
`prompt_token_count`, candidate output tokens, thought tokens, and cached-input
tokens in `TranscriptionResult.usage`. It also calculates an estimated USD cost
using the configured `TokenPricing` rate and records its `pricing_version`.

`JobRepository.record_transcription_usage(...)` persists those values, and
`JobRepository.usage_summary(media_file_id)` returns tokens and estimated cost
per task. These values are **not** the final invoice: promotional credits,
currency conversion, taxes, SKU changes, and billing-report delays are only
authoritative in Cloud Billing.

Before each production batch, update `GeminiVertexConfig.pricing` from the
official Vertex AI pricing page and change `pricing_version` to the date/model
used for that run.

## Verification state

Unit tests use injected fake clients and do not contact Google Cloud. A real
Vertex integration test is still required after the user selects a project and
authenticates ADC. Until that succeeds, do not claim the Vertex provider is
usable with the user's credits.
