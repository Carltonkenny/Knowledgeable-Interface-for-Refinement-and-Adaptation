# middleware/otel_tracing.py
# ─────────────────────────────────────────────
# OpenTelemetry Tracing — Infrastructure Tracing
#
# Replaces in-memory MetricsCollector with proper distributed tracing.
# Exports to Jaeger (self-hosted) via OTLP protocol.
# Tracks: DB calls, cache operations, agent execution, middleware latency.
# ─────────────────────────────────────────────

import os
import logging
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

logger = logging.getLogger(__name__)

_initialized = False


def init_otel_tracing(app_name: str = "promptforge-api") -> None:
    """Initialize OpenTelemetry tracing with Jaeger exporter."""
    global _initialized
    if _initialized:
        return

    exporter_type = os.getenv("OTEL_EXPORTER", "jaeger")
    environment = os.getenv("ENVIRONMENT", "development")

    resource = Resource.create({
        "service.name": app_name,
        "deployment.environment": environment,
    })

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    if exporter_type == "jaeger":
        endpoint = os.getenv("OTEL_EXPORTER_JAEGER_ENDPOINT", "http://localhost:4317")
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    else:
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    _initialized = True
    logger.info(f"[otel] initialized — exporter: {exporter_type}, service: {app_name}")


def get_tracer(name: str = "promptforge") -> trace.Tracer:
    """Get a tracer by name."""
    return trace.get_tracer(name)


def inject_request_id(request_id: str) -> None:
    """Inject X-Request-ID into the current span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute("http.request_id", request_id)


__all__ = ["init_otel_tracing", "get_tracer", "inject_request_id"]
