"""Инициализация OpenTelemetry для трейсинга."""

import os

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor


def init_tracing():
    """Инициализация OpenTelemetry для трейсинга.

    Если задан OTEL_ENDPOINT, настраивается OTLP экспорт.
    Иначе используется консольный экспортер для локальной разработки.
    """
    try:
        otel_endpoint = os.getenv("OTEL_ENDPOINT", "").strip()
        otel_service_name = os.getenv("OTEL_SERVICE_NAME", "mcp-finance")

        tracer_provider = TracerProvider(
            resource=Resource.create({
                "service.name": otel_service_name,
                "service.version": "1.0.0",
            })
        )

        if otel_endpoint:
            if otel_endpoint.startswith("http"):
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPHTTPSpanExporter
                otlp_exporter = OTLPHTTPSpanExporter(endpoint=otel_endpoint)
            else:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
                otlp_exporter = OTLPSpanExporter(endpoint=otel_endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)
            print(f"✅ OpenTelemetry настроен для OTLP экспорта: {otel_endpoint}")
        else:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            console_exporter = ConsoleSpanExporter()
            span_processor = BatchSpanProcessor(console_exporter)
            tracer_provider.add_span_processor(span_processor)
            print("✅ OpenTelemetry настроен для консольного вывода")

        trace.set_tracer_provider(tracer_provider)
        HTTPXClientInstrumentor().instrument()
        print("✅ OpenTelemetry инициализирован")
    except Exception as e:
        print(f"⚠️ Не удалось инициализировать OpenTelemetry: {e}")
        print("ℹ️ Продолжаем работу без трейсинга")


# Экземпляр tracer для инструментов
tracer = trace.get_tracer(__name__)
