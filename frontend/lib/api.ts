import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
        }
        return Promise.reject(error);
      }
    );
  }

  async get(url: string, params?: Record<string, any>) {
    const response = await this.client.get(url, { params });
    return response.data;
  }

  async post(url: string, data?: any) {
    const response = await this.client.post(url, data);
    return response.data;
  }

  async put(url: string, data?: any) {
    const response = await this.client.put(url, data);
    return response.data;
  }

  async delete(url: string) {
    const response = await this.client.delete(url);
    return response.data;
  }
}

export const api = new ApiClient();

// Project API
export const projectsApi = {
  list: () => api.get('/projects/'),
  get: (id: string) => api.get(`/projects/${id}`),
  create: (data: { name: string; description?: string }) => api.post('/projects/', data),
  delete: (id: string) => api.delete(`/projects/${id}`),
  uploadRtl: (projectId: string, data: { content: string; filename: string }) =>
    api.post(`/projects/${projectId}/rtl`, data),
  getStats: () => api.get('/projects/stats'),
};

// RTL API
export const rtlApi = {
  analyze: (content: string, filename: string = 'design.sv') =>
    api.post('/rtl/analyze', { content, filename }),
  getFifoExample: () => api.get('/rtl/examples/fifo'),
};

// Verification API
export const verificationApi = {
  generatePlan: (rtlContent: string, specification?: string) =>
    api.post('/verification/plan', { rtl_content: rtlContent, specification }),
  generateAssertions: (rtlContent: string) =>
    api.post('/verification/assertions', { rtl_content: rtlContent }),
  generateTests: (rtlContent: string, coverageGaps?: any[], testTypes?: string[]) =>
    api.post('/verification/tests', { rtl_content: rtlContent, coverage_gaps: coverageGaps, test_types: testTypes }),
  generateUvm: (rtlContent: string) =>
    api.post('/verification/uvm', { rtl_content: rtlContent }),
  fullFlow: (rtlContent: string, specification?: string) =>
    api.post('/verification/full-flow', { rtl_content: rtlContent, specification }),
};

// Simulation API
export const simulationApi = {
  compile: (data: {
    rtl_files: string[];
    testbench: string;
    top_module: string;
    simulator?: string;
    timeout?: number;
  }) => api.post('/simulation/compile', data),
  run: (data: {
    rtl_content: string;
    test_code: string;
    top_module: string;
    simulator?: string;
    timeout?: number;
  }) => api.post('/simulation/run', data),
  analyzeLog: (logContent: string, logType: string = 'simulation') =>
    api.post('/simulation/analyze-log', { log_content: logContent, log_type: logType }),
};

// Failure API
export const failureApi = {
  analyze: (data: {
    failure_info: any;
    rtl_content?: string;
    log_analysis?: any;
  }) => api.post('/failures/analyze', data),
  list: (projectId: string) => api.get(`/failures/${projectId}`),
};

// Coverage API
export const coverageApi = {
  analyze: (data: {
    coverage_report: string;
    rtl_content?: string;
    module_name?: string;
  }) => api.post('/coverage/analyze', data),
  identifyGaps: (data: {
    coverage_report: string;
    rtl_content: string;
    module_name: string;
  }) => api.post('/coverage/gaps', data),
  generateTargetedTests: (data: {
    coverage_report: string;
    rtl_content: string;
    module_name: string;
  }) => api.post('/coverage/generate-targeted-tests', data),
  compare: (before: any, after: any) =>
    api.post('/coverage/compare', { coverage_before: before, coverage_after: after }),
};

// Traceability API
export const traceabilityApi = {
  createLink: (data: {
    requirement_id: string;
    artifact_type: string;
    artifact_id: string;
  }) => api.post('/traceability/link', data),
  get: (requirementId: string) => api.get(`/traceability/${requirementId}`),
  getAll: () => api.get('/traceability/'),
  getUnverified: () => api.get('/traceability/unverified'),
};

// Regression API
export const regressionApi = {
  run: (data: {
    rtl_files: string[];
    test_files: string[];
    top_module: string;
    simulator?: string;
    timeout?: number;
  }) => api.post('/regression/run', data),
  getHistory: (projectId: string) => api.get(`/regression/${projectId}`),
};