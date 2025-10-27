/**
 * Agent API Service
 * Communication layer for AI Entry Point - Agent Hook
 */

import axios from 'axios';

// IMPORTANT: REACT_APP_BACKEND_URL must be set in environment
// No localhost fallback to ensure proper production configuration
const API = process.env.REACT_APP_BACKEND_URL;

if (!API) {
  console.error('REACT_APP_BACKEND_URL is not set! API calls will fail.');
}

// Helper to add nocache params
const getNoCacheParams = () => ({
  nocache: 1,
  ts: Date.now()
});

/**
 * Send task to agent for execution
 * @param {string} text - Task description in natural language
 * @returns {Promise<{status: string, job_id: string}>}
 */
export const sendTask = async (text) => {
  try {
    console.log(`[AgentAPI] Sending task: ${text.substring(0, 100)}...`);
    
    const response = await axios.post(`${API}/api/hook/exec`, {
      text,
      timestamp: Date.now(),
      nocache: true
    });
    
    console.log(`[AgentAPI] Task accepted - Job ID: ${response.data.job_id}`);
    return response.data;
  } catch (error) {
    console.error('[AgentAPI] Error sending task:', error);
    throw error;
  }
};

/**
 * Get execution logs from agent
 * @param {boolean} read - If true, just read logs without expecting updates
 * @returns {Promise<{logs: Array, status: string, total_steps: number}>}
 */
export const getLogs = async (read = false) => {
  try {
    const params = {
      ...getNoCacheParams(),
      ...(read && { read: true })
    };
    
    const response = await axios.get(`${API}/api/hook/log`, { params });
    return response.data;
  } catch (error) {
    console.error('[AgentAPI] Error getting logs:', error);
    throw error;
  }
};

/**
 * Force refresh the agent watcher
 * @param {string} target - Target to refresh (default: 'main')
 * @returns {Promise<{status: string}>}
 */
export const refreshAgent = async (target = 'main') => {
  try {
    console.log(`[AgentAPI] Refreshing agent (target: ${target})`);
    
    const response = await axios.get(`${API}/api/hook/refresh`, {
      params: {
        target,
        ...getNoCacheParams()
      }
    });
    
    console.log(`[AgentAPI] Agent refreshed: ${response.data.status}`);
    return response.data;
  } catch (error) {
    console.error('[AgentAPI] Error refreshing agent:', error);
    throw error;
  }
};

/**
 * Get current active task
 * @returns {Promise<{text: string, job_id: string}>}
 */
export const getCurrentTask = async () => {
  try {
    const response = await axios.get(`${API}/api/hook/text`, {
      params: getNoCacheParams()
    });
    
    return response.data;
  } catch (error) {
    console.error('[AgentAPI] Error getting current task:', error);
    throw error;
  }
};

/**
 * Get agent status
 * @returns {Promise<{status: string, current_task: string, active: boolean}>}
 */
export const getAgentStatus = async () => {
  try {
    const response = await axios.get(`${API}/api/hook/status`, {
      params: getNoCacheParams()
    });
    
    return response.data;
  } catch (error) {
    console.error('[AgentAPI] Error getting agent status:', error);
    throw error;
  }
};

/**
 * Force execute with task parameter
 * @param {string} task - Quick task to execute
 * @returns {Promise<any>}
 */
export const forceExecute = async (task = 'run') => {
  try {
    const response = await axios.get(`${API}/api/hook/exec`, {
      params: {
        task,
        ...getNoCacheParams()
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('[AgentAPI] Error force executing:', error);
    throw error;
  }
};

/**
 * Get task result - credentials, screenshot, completion
 * @returns {Promise<{result: object}>}
 */
export const getResult = async () => {
  try {
    const response = await axios.get(`${API}/api/hook/result`, {
      params: getNoCacheParams()
    });
    
    return response.data;
  } catch (error) {
    console.error('[AgentAPI] Error getting result:', error);
    throw error;
  }
};

/**
 * Control agent execution mode
 * @param {string} mode - ACTIVE, PAUSED, or STOP
 * @returns {Promise<{success: boolean, run_mode: string}>}
 */
export const controlAgent = async (mode) => {
  try {
    console.log(`[AgentAPI] Setting agent mode to: ${mode}`);
    
    const response = await axios.post(`${API}/api/hook/control`, {
      mode
    });
    
    console.log(`[AgentAPI] Agent mode updated: ${response.data.run_mode}`);
    return response.data;
  } catch (error) {
    console.error('[AgentAPI] Error controlling agent:', error);
    throw error;
  }
};


// ========== New Automation APIs for AI Entry Point ==========
export const automationCreateSession = async (sessionId, useProxy = true) => {
  const response = await axios.post(`${API}/api/automation/session/create`, { session_id: sessionId, use_proxy: useProxy });
  return response.data;
};
export const automationNavigate = async (sessionId, url) => {
  const response = await axios.post(`${API}/api/automation/navigate`, { session_id: sessionId, url });
  return response.data;
};
export const automationScreenshot = async (sessionId) => {
  const response = await axios.get(`${API}/api/automation/screenshot`, { params: { session_id: sessionId } });
  return response.data;
};
export const automationClickCell = async (sessionId, cell) => {
  const response = await axios.post(`${API}/api/automation/click-cell`, { session_id: sessionId, cell });
  return response.data;
};
export const automationTypeAtCell = async (sessionId, cell, text) => {
  const response = await axios.post(`${API}/api/automation/type-at-cell`, { session_id: sessionId, cell, text });
  return response.data;
};
export const automationHoldDrag = async (sessionId, fromCell, toCell) => {
  const response = await axios.post(`${API}/api/automation/hold-drag`, { session_id: sessionId, from_cell: fromCell, to_cell: toCell });
  return response.data;
};
export const automationScroll = async (sessionId, dx = 0, dy = 400) => {
  const response = await axios.post(`${API}/api/automation/scroll`, { session_id: sessionId, dx, dy });
  return response.data;
};
export const brainNextStep = async (payload) => {
  const response = await axios.post(`${API}/api/automation/brain/next-step`, payload);
  return response.data;
};
