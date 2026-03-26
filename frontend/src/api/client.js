import axios from 'axios';

export const API_BASE_URL = 'http://127.0.0.1:8000/api';

const http = axios.create({ baseURL: API_BASE_URL, timeout: 60000 });

export const projectsApi = {
  list:   ()     => http.get('/projects/'),
  create: (body) => http.post('/projects/', body),
  get:    (id)   => http.get(`/projects/${id}`),
  del:    (id)   => http.delete(`/projects/${id}`),
};

export const datasetsApi = {
  upload:  (fd, onProgress) => http.post('/datasets/upload', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  }),
  get:     (id)       => http.get(`/datasets/${id}`),
  preview: (id, n=20) => http.get(`/datasets/${id}/preview`, { params: { n } }),
  del:     (id)       => http.delete(`/datasets/${id}`),

  // Misure suggerite
  getSuggestedFeatures:    (id)           => http.get(`/datasets/${id}/suggested-features`),
  updateFeatureDecisions:  (id, decisions) => http.patch(`/datasets/${id}/suggested-features`, { decisions }),
  acceptAllFeatures:       (id)           => http.post(`/datasets/${id}/suggested-features/accept-all`),
  rejectAllFeatures:       (id)           => http.post(`/datasets/${id}/suggested-features/reject-all`),
};

export const analysisApi = {
  run:     (datasetId, body) => http.post(`/analysis/run/${datasetId}`, body),
  status:  (id)              => http.get(`/analysis/${id}/status`),
  results: (id)              => http.get(`/analysis/${id}/results`),
  section: (id, sec)         => http.get(`/analysis/${id}/section/${sec}`),
  sampleData: (analysisId, { columns = [], includeTarget = false } = {}) => {
    const colsParam = columns && columns.length ? columns.join(',') : '';
    return http.get(`/analysis/${analysisId}/sample-data`, {
      params: { columns: colsParam, includeTarget },
    });
  },
};

export const reportsApi = {
  generate: (analysisId) => http.post(`/reports/generate/${analysisId}`),
  status: (reportId) => http.get(`/reports/${reportId}/status`),
  downloadUrl: (reportId) => `${API_BASE_URL}/reports/${reportId}/download`,
};
