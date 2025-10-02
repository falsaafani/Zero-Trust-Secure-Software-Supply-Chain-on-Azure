import pytest
import json
from datetime import datetime


class TestHealthEndpoints:
    def test_health_endpoint(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
        assert 'environment' in data

    def test_readiness_endpoint(self, client):
        response = client.get('/health/ready')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ready'
        assert 'checks' in data
        assert data['checks']['application'] == 'ok'

    def test_liveness_endpoint(self, client):
        response = client.get('/health/live')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'alive'
        assert 'timestamp' in data


class TestRootEndpoint:
    def test_root_endpoint(self, client):
        response = client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['service'] == 'Zero-Trust Secure Application'
        assert 'version' in data
        assert 'environment' in data
        assert 'timestamp' in data


class TestMetricsEndpoint:
    def test_metrics_endpoint(self, client):
        response = client.get('/metrics')
        assert response.status_code == 200
        assert b'app_request_count' in response.data
        assert b'app_request_latency_seconds' in response.data
        assert b'app_active_requests' in response.data
        assert b'app_info' in response.data


class TestDataEndpoints:
    def test_get_data(self, client):
        response = client.get('/api/v1/data')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) == 3
        assert data['data'][0]['id'] == 1

    def test_create_data_valid_json(self, client):
        test_data = {"name": "Test Item", "value": 500}
        response = client.post(
            '/api/v1/data',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Data created successfully'
        assert data['data'] == test_data

    def test_create_data_invalid_content_type(self, client):
        response = client.post(
            '/api/v1/data',
            data='not json',
            content_type='text/plain'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestSecureEndpoint:
    def test_secure_endpoint_without_auth(self, client):
        response = client.get('/api/v1/secure')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'Unauthorized'

    def test_secure_endpoint_with_invalid_auth(self, client):
        response = client.get(
            '/api/v1/secure',
            headers={'Authorization': 'InvalidToken'}
        )
        assert response.status_code == 401

    def test_secure_endpoint_with_valid_auth(self, client):
        response = client.get(
            '/api/v1/secure',
            headers={'Authorization': 'Bearer valid-token-123'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data


class TestErrorHandling:
    def test_404_error(self, client):
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'timestamp' in data

    def test_405_method_not_allowed(self, client):
        response = client.delete('/health')
        assert response.status_code == 405
        data = json.loads(response.data)
        assert 'error' in data


class TestIntegration:
    def test_full_request_lifecycle(self, client):
        response = client.get('/')
        assert response.status_code == 200

        response = client.get('/health')
        assert response.status_code == 200

        test_data = {"name": "Integration Test", "value": 999}
        response = client.post(
            '/api/v1/data',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        assert response.status_code == 201

        response = client.get('/api/v1/data')
        assert response.status_code == 200

        response = client.get('/metrics')
        assert response.status_code == 200
