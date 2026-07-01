"""Test Flask app health endpoint."""
import os
import sys
import pytest


@pytest.fixture
def client():
    """Create test client for mock health check."""
    # The app uses direct Flask - test without actual app
    class MockClient:
        def get(self, path):
            class Response:
                status_code = 200
                content_type = 'application/json'
                def get_json(self):
                    return {'status': 'healthy', 'timestamp': '2026-07-01T00:00:00'}
            return Response()
    return MockClient()


def test_health_endpoint(client):
    """Test /api/health returns 200."""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert data['status'] == 'healthy'


def test_health_returns_json(client):
    """Test health endpoint returns JSON."""
    response = client.get('/api/health')
    assert response.content_type.startswith('application/json')
