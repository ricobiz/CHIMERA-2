/**
 * Agent API Service
 * Communication layer for AI Entry Point - Agent Hook
 */

import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

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
