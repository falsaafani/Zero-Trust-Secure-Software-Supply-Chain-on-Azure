import os
import logging
import time
from datetime import datetime
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from werkzeug.exceptions import HTTPException
import structlog

app = Flask(__name__)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

REQUEST_COUNT = Counter(
    'app_request_count',
    'Application Request Count',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds',
    'Application Request Latency',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'app_active_requests',
    'Number of active requests'
)

APP_INFO = Gauge(
    'app_info',
    'Application Information',
    ['version', 'environment']
)

APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

APP_INFO.labels(version=APP_VERSION, environment=ENVIRONMENT).set(1)


@app.before_request
def before_request():
    request.start_time = time.time()
    ACTIVE_REQUESTS.inc()
    logger.info(
        "request_started",
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr
    )


@app.after_request
def after_request(response):
    ACTIVE_REQUESTS.dec()

    if hasattr(request, 'start_time'):
        request_latency = time.time() - request.start_time
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).observe(request_latency)

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        http_status=response.status_code
    ).inc()

    logger.info(
        "request_completed",
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        latency=request_latency if hasattr(request, 'start_time') else None
    )

    return response


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    logger.error(
        "http_error",
        error=str(e),
        status_code=e.code,
        path=request.path
    )
    response = {
        "error": e.name,
        "message": e.description,
        "status_code": e.code,
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(response), e.code


@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(
        "unhandled_error",
        error=str(e),
        path=request.path,
        exc_info=True
    )
    response = {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "status_code": 500,
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(response), 500


@app.route('/')
def root():
    return jsonify({
        "service": "Zero-Trust Secure Application",
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route('/health')
def health():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": APP_VERSION,
        "environment": ENVIRONMENT
    }
    return jsonify(health_status), 200


@app.route('/health/ready')
def readiness():
    readiness_status = {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "application": "ok"
        }
    }
    return jsonify(readiness_status), 200


@app.route('/health/live')
def liveness():
    liveness_status = {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(liveness_status), 200


@app.route('/metrics')
def metrics():
    return generate_latest()


@app.route('/api/v1/data', methods=['GET'])
def get_data():
    logger.info("data_requested", endpoint="/api/v1/data")
    return jsonify({
        "data": [
            {"id": 1, "name": "Item 1", "value": 100},
            {"id": 2, "name": "Item 2", "value": 200},
            {"id": 3, "name": "Item 3", "value": 300}
        ],
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route('/api/v1/data', methods=['POST'])
def create_data():
    if not request.is_json:
        logger.warning("invalid_content_type", content_type=request.content_type)
        return jsonify({
            "error": "Bad Request",
            "message": "Content-Type must be application/json"
        }), 400

    data = request.get_json()
    logger.info("data_created", data=data)

    return jsonify({
        "message": "Data created successfully",
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }), 201


@app.route('/api/v1/secure', methods=['GET'])
def secure_endpoint():
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        logger.warning("unauthorized_access_attempt", path=request.path)
        return jsonify({
            "error": "Unauthorized",
            "message": "Valid authorization token required"
        }), 401

    logger.info("secure_endpoint_accessed")
    return jsonify({
        "message": "Access granted to secure resource",
        "timestamp": datetime.utcnow().isoformat()
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(
        "starting_application",
        version=APP_VERSION,
        environment=ENVIRONMENT,
        port=port
    )
    app.run(host='0.0.0.0', port=port, debug=(ENVIRONMENT == 'development'))
