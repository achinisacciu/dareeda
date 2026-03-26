import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { projectsApi, datasetsApi, analysisApi } from '../api/client';

const LEGACY_STORAGE_KEYS = ['dareeda-session-store'];
const MAX_PROJECT_CACHE = 6;
const MAX_ANALYSIS_CACHE = 2;

function cleanupLegacyStorage(storage) {
  LEGACY_STORAGE_KEYS.forEach(key => {
    try {
      storage.removeItem(key);
    } catch {
      // ignore storage cleanup errors
    }
  });
}

function createSafeSessionStorage() {
  return {
    getItem: (name) => {
      try {
        cleanupLegacyStorage(sessionStorage);
        return sessionStorage.getItem(name);
      } catch {
        return null;
      }
    },
    setItem: (name, value) => {
      try {
        cleanupLegacyStorage(sessionStorage);
        sessionStorage.setItem(name, value);
      } catch {
        // ignore quota/storage errors to avoid crashing the app
      }
    },
    removeItem: (name) => {
      try {
        sessionStorage.removeItem(name);
      } catch {
        // ignore storage cleanup errors
      }
    },
  };
}

function withLimitedCache(cache, key, value, maxEntries) {
  const next = { ...cache };
  delete next[key];
  next[key] = value;

  const keys = Object.keys(next);
  while (keys.length > maxEntries) {
    const oldest = keys.shift();
    if (oldest) delete next[oldest];
  }

  return next;
}

export const useStore = create(persist((set, get) => ({
  // Projects
  projects: [],
  loadingProjects: false,
  projectsError: null,
  projectCache: {},
  fetchProjects: async () => {
    set({ loadingProjects: true, projectsError: null });
    try {
      const { data } = await projectsApi.list();
      set({ projects: data });
      return data;
    } catch (e) {
      const message = e?.code === 'ECONNABORTED'
        ? 'Timeout nel caricamento dei progetti.'
        : (e?.response?.data?.detail || e?.message || 'Errore caricamento progetti.');
      set({ projectsError: String(message) });
      console.error(e);
      return null;
    } finally { set({ loadingProjects: false }); }
  },
  createProject: async (name, description = '') => {
    const { data } = await projectsApi.create({ name, description });
    set(s => ({ projects: [data, ...s.projects] }));
    return data;
  },
  deleteProject: async (id) => {
    await projectsApi.del(id);
    set(s => ({ projects: s.projects.filter(p => p.id !== id) }));
  },

  // Active project
  activeProject: null,
  activeDatasets: [],
  activeProjectError: null,
  fetchProject: async (id) => {
    const cached = get().projectCache[id];
    if (cached) {
      set({ activeProject: cached, activeProjectError: null });
    }
    try {
      const { data } = await projectsApi.get(id);
      set(state => ({
        activeProject: data,
        activeProjectError: null,
        projectCache: withLimitedCache(state.projectCache, id, data, MAX_PROJECT_CACHE),
      }));
      return data;
    } catch (e) {
      const message = e?.code === 'ECONNABORTED'
        ? 'Timeout nel caricamento del progetto.'
        : (e?.response?.data?.detail || e?.message || 'Errore caricamento progetto.');
      set(state => ({
        activeProject: cached || state.activeProject,
        activeProjectError: String(message),
      }));
      console.error(e);
      return null;
    }
  },

  // Upload
  uploadResult: null,
  uploadProgress: 0,
  resetUpload: () => set({ uploadResult: null, uploadProgress: 0 }),
  uploadDataset: async (file, projectId) => {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('project_id', projectId);
    set({ uploadProgress: 0, uploadResult: null });
    const { data } = await datasetsApi.upload(fd, e => {
      if (e.total) set({ uploadProgress: Math.round(e.loaded / e.total * 100) });
    });
    set({ uploadResult: data, uploadProgress: 100 });
    return data;
  },

  // Analysis
  analysisStatus: null,
  analysisResults: null,
  analysisStatusCache: {},
  analysisResultsCache: {},
  pollingInterval: null,

  startAnalysis: async (datasetId, payload) => {
    const { data } = await analysisApi.run(datasetId, payload);
    set({ analysisStatus: data, analysisResults: null });
    return data;
  },

  pollStatus: (analysisId) => {
    const cachedStatus = get().analysisStatusCache[analysisId] || null;
    const cachedResults = get().analysisResultsCache[analysisId] || null;

    set({
      analysisStatus: cachedStatus,
      analysisResults: cachedResults,
    });

    if (cachedStatus?.status === 'completed' && cachedResults) {
      return;
    }

    const check = async () => {
      try {
        const { data } = await analysisApi.status(analysisId);
        set(state => ({
          analysisStatus: data,
          analysisStatusCache: withLimitedCache(
            state.analysisStatusCache,
            analysisId,
            data,
            MAX_ANALYSIS_CACHE,
          ),
        }));
        if (data.status === 'completed') {
          const { data: results } = await analysisApi.results(analysisId);
          set(state => ({
            analysisResults: results,
            analysisResultsCache: withLimitedCache(
              state.analysisResultsCache,
              analysisId,
              results,
              MAX_ANALYSIS_CACHE,
            ),
          }));
          return true;
        }
        if (data.status === 'failed') return true;
        return false;
      } catch (e) {
        return true;
      }
    };

    check().then(done => {
      if (done) return;
      const iv = setInterval(async () => {
        const done = await check();
        if (done) {
          clearInterval(iv);
          set({ pollingInterval: null });
        }
      }, 1500);
      set({ pollingInterval: iv });
    });
  },

  stopPolling: () => {
    const iv = get().pollingInterval;
    if (iv) { clearInterval(iv); set({ pollingInterval: null }); }
  },
}), {
  name: 'dareeda-ui-store-v2',
  storage: createJSONStorage(createSafeSessionStorage),
  partialize: (state) => ({
    projects: state.projects,
  }),
}));
