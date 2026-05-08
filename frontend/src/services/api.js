const API_BASE = '';

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  async getStatus() {
    return fetchJson(`${API_BASE}/api/status`);
  },

  async getConfig() {
    return fetchJson(`${API_BASE}/api/config`);
  },

  async getProfiles(trainType) {
    return fetchJson(`${API_BASE}/api/profiles/${trainType}`);
  },

  async saveProfile(trainType, profileName, config) {
    return fetchJson(`${API_BASE}/api/profiles/${trainType}/${profileName}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
  },

  async deleteProfile(trainType, profileName) {
    return fetchJson(`${API_BASE}/api/profiles/${trainType}/${profileName}`, {
      method: 'DELETE'
    });
  },

  async searchTrains(trainType, config) {
    return fetchJson(`${API_BASE}/api/search/${trainType}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...config, train_no: '' })
    });
  },

  async startMacro(trainType, config) {
    return fetchJson(`${API_BASE}/api/start/${trainType}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
  },

  async stopMacro(trainType) {
    return fetchJson(`${API_BASE}/api/stop/${trainType}`, {
      method: 'POST'
    });
  }
};
