import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor if needed
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Wiki Service Client
export const WikiApi = {
  listPages: async (limit = 50, offset = 0) => {
    const response = await api.get('/wiki/pages', { params: { limit, offset } });
    return response.data;
  },

  getPage: async (slug: string) => {
    const response = await api.get(`/wiki/pages/${slug}`);
    return response.data;
  },

  createPage: async (data: { slug: string; title: string; content: string; namespace?: string }) => {
    const response = await api.post('/wiki/pages', data);
    return response.data;
  },

  updatePage: async (slug: string, data: { content: string; version: number; commit_message?: string }) => {
    const response = await api.put(`/wiki/pages/${slug}`, data);
    return response.data;
  },

  search: async (query: string) => {
    const response = await api.get('/wiki/search', { params: { q: query } });
    return response.data;
  },
  
  getPages: async () => {
    const response = await api.get('/wiki/pages');
    return response.data;
  }
};
