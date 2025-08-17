"""OpenTelemetry tracing setup."""

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.semconv.attributes import service_attributes

from myunla.utils.logger import get_logger

logger = get_logger(__name__)


def setup_tracing(
    service_name: str = "mcp-gateway",
    jaeger_endpoint: str | None = None,
    otlp_endpoint: str | None = None,
):
    """Setup OpenTelemetry tracing."""

    # Set up resource
    resource = Resource.create(
        {
            service_attributes.SERVICE_NAME: service_name,
            service_attributes.SERVICE_VERSION: "1.0.0",
        }
    )

    # Set up tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Add console exporter for development
    console_exporter = ConsoleSpanExporter()
    span_processor = BatchSpanProcessor(console_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Add Jaeger exporter if configured
    if jaeger_endpoint:
        try:
            jaeger_exporter = JaegerExporter(
                agent_host_name=(
                    jaeger_endpoint.split(":")[0]
                    if ":" in jaeger_endpoint
                    else "localhost"
                ),
                agent_port=(
                    int(jaeger_endpoint.split(":")[1])
                    if ":" in jaeger_endpoint
                    else 6831
                ),
            )
            jaeger_processor = BatchSpanProcessor(jaeger_exporter)
            tracer_provider.add_span_processor(jaeger_processor)
            logger.info(f"Jaeger exporter configured: {jaeger_endpoint}")
        except Exception as e:
            logger.warning(f"Failed to setup Jaeger exporter: {e}")

    # Add OTLP exporter if configured
    if otlp_endpoint:
        try:
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            otlp_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(otlp_processor)
            logger.info(f"OTLP exporter configured: {otlp_endpoint}")
        except Exception as e:
            logger.warning(f"Failed to setup OTLP exporter: {e}")

    # Instrument FastAPI and HTTPX
    FastAPIInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    logger.info("OpenTelemetry tracing setup complete")


def get_tracer():
    """Get a tracer instance."""
    return trace.get_tracer(__name__)
