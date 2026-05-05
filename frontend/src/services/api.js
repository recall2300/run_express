const API_BASE = ''; // Same origin

export const api = {
  async getStatus() {
    const res = await fetch(`${API_BASE}/api/status`);
    return res.json();
  },

  async getConfig() {
    const res = await fetch(`${API_BASE}/api/config`);
    return res.json();
  },

  async getProfiles(trainType) {
    const res = await fetch(`${API_BASE}/api/profiles/${trainType}`);
    return res.json();
  },

  async saveProfile(trainType, profileName, config) {
    const res = await fetch(`${API_BASE}/api/profiles/${trainType}/${profileName}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return res.json();
  },

  async deleteProfile(trainType, profileName) {
    const res = await fetch(`${API_BASE}/api/profiles/${trainType}/${profileName}`, {
      method: 'DELETE'
    });
    return res.json();
  },

  async searchTrains(trainType, config) {
    const res = await fetch(`${API_BASE}/api/search/${trainType}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...config, train_no: '' })
    });
    return res.json();
  },

  async startMacro(trainType, config) {
    const res = await fetch(`${API_BASE}/api/start/${trainType}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return res.json();
  },

  async stopMacro(trainType) {
    const res = await fetch(`${API_BASE}/api/stop/${trainType}`, {
      method: 'POST'
    });
    return res.json();
  }
};
