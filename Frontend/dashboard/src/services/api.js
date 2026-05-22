// Centralized API Service
// This makes it easy to change the backend URL in one place
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Remove Content-Type if sending FormData (browser sets it automatically with boundary)
    if (options.body instanceof FormData) {
      delete headers['Content-Type'];
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      // Handle non-JSON responses gracefully
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.indexOf("application/json") !== -1) {
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || 'API Error');
        return data;
      }
      return response;
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: data instanceof FormData ? data : JSON.stringify(data)
    });
  }

  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  getConfig() {
    return this.get('/api/config');
  }

  saveConfig(data) {
    return this.post('/api/config', data);
  }

  getTestCases(dataset) {
    const params = new URLSearchParams({ dataset });
    return this.get(`/api/test-cases?${params.toString()}`);
  }

  getDatasetPreview(dataset, limit = 50) {
    const params = new URLSearchParams({ dataset, limit: String(limit) });
    return this.get(`/api/dataset-preview?${params.toString()}`);
  }

  createTestCase(dataset, data) {
    const params = new URLSearchParams({ dataset });
    return this.post(`/api/test-cases?${params.toString()}`, data);
  }

  updateTestCase(dataset, testId, data) {
    const params = new URLSearchParams({ dataset });
    return this.put(`/api/test-cases/${testId}?${params.toString()}`, data);
  }

  deleteTestCase(dataset, testId) {
    const params = new URLSearchParams({ dataset });
    return this.delete(`/api/test-cases/${testId}?${params.toString()}`);
  }

  generateQuery(prompt, context = '') {
    return this.post('/api/generate-query', { prompt, context });
  }

  executeAudit(dataset, query = null) {
    return this.post('/api/execute', { dataset, query });
  }
}

export const api = new ApiService();
