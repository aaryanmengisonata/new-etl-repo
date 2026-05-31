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
        if (!response.ok) {
          const detailMsg = data.message || (typeof data.detail === 'string' ? data.detail : (data.detail ? JSON.stringify(data.detail) : ''));
          throw new Error(detailMsg || 'API Error');
        }
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

  getDbConfig() {
    return this.get('/api/config/db');
  }

  saveDbConfig(data) {
    return this.post('/api/config/db', data);
  }

  getPipelineConfig() {
    return this.get('/api/config/pipeline');
  }

  savePipelineConfig(data) {
    return this.post('/api/config/pipeline', data);
  }

  getApiSentryConfig() {
    return this.get('/api/config/api-sentry');
  }

  saveApiSentryConfig(data) {
    return this.post('/api/config/api-sentry', data);
  }

  getIntegrationConfig() {
    return this.get('/api/config/integration');
  }

  saveIntegrationConfig(data) {
    return this.post('/api/config/integration', data);
  }

  getTestingConfig() {
    return this.get('/api/config/testing');
  }

  saveTestingConfig(data) {
    return this.post('/api/config/testing', data);
  }

  getReportingConfig() {
    return this.get('/api/config/reporting');
  }

  saveReportingConfig(data) {
    return this.post('/api/config/reporting', data);
  }

  analyzeIntegrationSystems(data) {
    return this.post('/api/integration-sentry/analyze', data);
  }

  executeIntegrationReconciliation(data) {
    return this.post('/api/integration-sentry/execute', data);
  }


  getDbTables() {
    return this.get('/api/interactive-testing/db-tables');
  }

  analyzeSchemaDetails(tableName, columns) {
    return this.post('/api/interactive-testing/analyze-schema-details', {
      table_name: tableName,
      columns
    });
  }

  analyzeSchemaImage(formData) {
    return this.post('/api/analyze-schema-image', formData);
  }

  executeBatchDbValidations(requests) {
    return this.post('/api/interactive-testing/execute-batch-db-validations', requests);
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

  // ── Reports ─────────────────────────────────────────────────

  getRecentReports(limit = 50) {
    return this.get(`/recent-reports?limit=${limit}`);
  }

  getReportById(id) {
    return this.get(`/api/reports/${id}`);
  }

  getReportSummary() {
    return this.get('/api/reports/summary');
  }

  async exportReportsCSV() {
    const res = await this.request('/api/reports/export/csv', { method: 'GET' });
    // res is a Response object since Content-Type is text/csv, not JSON
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'reports_export.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  }

  deleteReport(id) {
    return this.delete(`/api/reports/${id}`);
  }

  // ── Pipeline Auditor ───────────────────────────────────────
  testPipelineConnection(payload) {
    return this.post('/api/pipeline-auditor/test-connection', payload);
  }

  analyzePipeline(payload) {
    return this.post('/api/pipeline-auditor/analyze', payload);
  }

  executePipelineAudit(payload) {
    return this.post('/api/pipeline-auditor/execute', payload);
  }

  getPipelineAuditHistory(params = {}) {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.append('page', String(params.page));
    if (params.page_size) searchParams.append('page_size', String(params.page_size));
    if (params.status) searchParams.append('status', params.status);
    if (params.environment) searchParams.append('environment', params.environment);
    if (params.pipeline_type) searchParams.append('pipeline_type', params.pipeline_type);
    
    return this.get(`/api/pipeline-auditor/history?${searchParams.toString()}`);
  }

  getPipelineAuditDetail(auditId) {
    return this.get(`/api/pipeline-auditor/history/${auditId}`);
  }

  async exportPipelineAuditReport(auditId, format) {
    const response = await this.request('/api/pipeline-auditor/export', {
      method: 'POST',
      body: JSON.stringify({ audit_id: auditId, format })
    });
    return response;
  }

  deletePipelineAudit(auditId) {
    return this.delete(`/api/pipeline-auditor/history/${auditId}`);
  }
}

export const api = new ApiService();
