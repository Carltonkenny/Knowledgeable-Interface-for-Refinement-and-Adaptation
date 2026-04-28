from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import Request
import time

class OpenTelemetryTracing:
    """
    OpenTelemetry tracing middleware for distributed tracing
    """
    
    def __init__(self, service_name: str = "multi-agent-system"):
        # Initialize tracer provider
        self.tracer_provider = TracerProvider()
        
        # Add console exporter for development
        console_exporter = ConsoleSpanExporter()
        batch_processor = BatchSpanProcessor(console_exporter)
        self.tracer_provider.add_span_processor(batch_processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        
        self.service_name = service_name
        
    def setup_instrumentation(self, app):
        """
        Setup OpenTelemetry instrumentation for FastAPI app
        """
        FastAPIInstrumentor.instrument_app(app)
        
    def create_span(self, name: str, request: Request):
        """
        Create a tracing span for the request
        """
        tracer = trace.get_tracer(self.service_name)
        span = tracer.start_span(name)
        
        # Add request attributes
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
        
        return span