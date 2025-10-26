import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const generateCode = async (prompt, conversationHistory = [], model = 'anthropic/claude-3.5-sonnet') => {
  try {
    const response = await axios.post(`${API}/generate-code`, {
      prompt,
      conversation_history: conversationHistory,
      model
    });
    return response.data;
  } catch (error) {
    console.error('Error generating code:', error);
    throw error;
  }
};

export const saveProject = async (projectData) => {
  try {
    const response = await axios.post(`${API}/projects`, projectData);
    return response.data;
  } catch (error) {
    console.error('Error saving project:', error);
    throw error;
  }
};

export const getProjects = async () => {
  try {
    const response = await axios.get(`${API}/projects`);
    return response.data;
  } catch (error) {
    console.error('Error fetching projects:', error);
    throw error;
  }
};

export const getProject = async (projectId) => {
  try {
    const response = await axios.get(`${API}/projects/${projectId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching project:', error);
    throw error;
  }
};

export const deleteProject = async (projectId) => {
  try {
    const response = await axios.delete(`${API}/projects/${projectId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting project:', error);
    throw error;
  }
};

export const getModels = async () => {
  try {
    const response = await axios.get(`${API}/models`);
    return response.data;
  } catch (error) {
    console.error('Error fetching models:', error);
    throw error;
  }
};

export const exportProject = async (code, projectName) => {
  try {
    const response = await axios.post(`${API}/export`, 
      { code, project_name: projectName },
      { responseType: 'blob' }
    );
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${projectName}.zip`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    
    return { success: true };
  } catch (error) {
    console.error('Error exporting project:', error);
    throw error;
  }
};

// Session APIs
export const createSession = async (sessionData) => {
  try {
    const response = await axios.post(`${API}/sessions`, sessionData);
    return response.data;
  } catch (error) {
    console.error('Error creating session:', error);
    throw error;
  }
};

export const getSessions = async () => {
  try {
    const response = await axios.get(`${API}/sessions`);
    return response.data;
  } catch (error) {
    console.error('Error fetching sessions:', error);
    throw error;
  }
};

export const getSession = async (sessionId) => {
  try {
    const response = await axios.get(`${API}/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching session:', error);
    throw error;
  }
};

export const updateSession = async (sessionId, sessionData) => {
  try {
    const response = await axios.put(`${API}/sessions/${sessionId}`, sessionData);
    return response.data;
  } catch (error) {
    console.error('Error updating session:', error);
    throw error;
  }
};

export const deleteSession = async (sessionId) => {
  try {
    const response = await axios.delete(`${API}/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting session:', error);
    throw error;
  }
};

// Visual Validation
export const validateVisual = async (screenshot, userRequest, validatorModel) => {
  try {
    const response = await axios.post(`${API}/validate-visual`, {
      screenshot,
      user_request: userRequest,
      validator_model: validatorModel
    });
    return response.data;
  } catch (error) {
    console.error('Error in visual validation:', error);
    throw error;
  }
};

// Design Generation
export const generateDesign = async (userRequest, model) => {
  try {
    const response = await axios.post(`${API}/generate-design`, {
      user_request: userRequest,
      model
    });
    return response.data;
  } catch (error) {
    console.error('Error generating design:', error);
    throw error;
  }
};

// ========== Service Integrations ==========

export const createIntegration = async (integrationData) => {
  try {
    const response = await axios.post(`${API}/integrations`, integrationData);
    return response.data;
  } catch (error) {
    console.error('Error creating integration:', error);
    throw error;
  }
};

export const getIntegrations = async () => {
  try {
    const response = await axios.get(`${API}/integrations`);
    return response.data;
  } catch (error) {
    console.error('Error fetching integrations:', error);
    throw error;
  }
};

export const getIntegration = async (integrationId) => {
  try {
    const response = await axios.get(`${API}/integrations/${integrationId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching integration:', error);
    throw error;
  }
};

export const updateIntegration = async (integrationId, updateData) => {
  try {
    const response = await axios.put(`${API}/integrations/${integrationId}`, updateData);
    return response.data;
  } catch (error) {
    console.error('Error updating integration:', error);
    throw error;
  }
};

export const deleteIntegration = async (integrationId) => {
  try {
    const response = await axios.delete(`${API}/integrations/${integrationId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting integration:', error);
    throw error;
  }
};

// ========== MCP Servers ==========

export const createMCPServer = async (serverData) => {
  try {
    const response = await axios.post(`${API}/mcp-servers`, serverData);
    return response.data;
  } catch (error) {
    console.error('Error creating MCP server:', error);
    throw error;
  }
};

export const getMCPServers = async () => {
  try {
    const response = await axios.get(`${API}/mcp-servers`);
    return response.data;
  } catch (error) {
    console.error('Error fetching MCP servers:', error);
    throw error;
  }
};

export const getMCPServer = async (serverId) => {
  try {
    const response = await axios.get(`${API}/mcp-servers/${serverId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching MCP server:', error);
    throw error;
  }
};

export const updateMCPServer = async (serverId, updateData) => {
  try {
    const response = await axios.put(`${API}/mcp-servers/${serverId}`, updateData);
    return response.data;
  } catch (error) {
    console.error('Error updating MCP server:', error);
    throw error;
  }
};

export const deleteMCPServer = async (serverId) => {
  try {
    const response = await axios.delete(`${API}/mcp-servers/${serverId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting MCP server:', error);
    throw error;
  }
};

export const healthCheckMCPServer = async (serverId) => {
  try {
    const response = await axios.post(`${API}/mcp-servers/${serverId}/health-check`);
    return response.data;
  } catch (error) {
    console.error('Error performing health check:', error);
    throw error;
  }
};

export const getActiveMCPServers = async () => {
  try {
    const response = await axios.get(`${API}/mcp-servers/active/list`);
    return response.data;
  } catch (error) {
    console.error('Error fetching active MCP servers:', error);
    throw error;
  }
};

// OpenRouter Balance
export const getOpenRouterBalance = async () => {
  try {
    const response = await axios.get(`${API}/openrouter/balance`);
    return response.data;
  } catch (error) {
    console.error('Error fetching OpenRouter balance:', error);
    throw error;
  }
};

// Research Planner
export const researchTask = async (userRequest, model, researchMode = 'full') => {
  try {
    const response = await axios.post(`${API}/research-task`, {
      user_request: userRequest,
      model,
      research_mode: researchMode
    });
    return response.data;
  } catch (error) {
    console.error('Error in research task:', error);
    throw error;
  }
};

// Context Management API
export const getContextStatus = async (history, model) => {
  try {
    const response = await axios.post(`${API}/context/status`, {
      history,
      model
    });
    return response.data;
  } catch (error) {
    console.error('Error getting context status:', error);
    throw error;
  }
};

export const switchModelWithContext = async (sessionId, newModel, history, oldModel) => {
  try {
    const response = await axios.post(`${API}/context/switch-model`, {
      session_id: sessionId,
      new_model: newModel,
      history,
      old_model: oldModel
    });
    return response.data;
  } catch (error) {
    console.error('Error switching model:', error);
    throw error;
  }

};

// Browser Automation API
export const createAutomationSession = async (sessionId) => {
  try {
    const response = await axios.post(`${API}/automation/session/create`, {
      session_id: sessionId
    });
    return response.data;
  } catch (error) {
    console.error('Error creating automation session:', error);
    throw error;
  }
};

export const navigateAutomation = async (sessionId, url) => {
  try {
    const response = await axios.post(`${API}/automation/navigate`, {
      session_id: sessionId,
      url
    });
    return response.data;
  } catch (error) {
    console.error('Error navigating:', error);
    throw error;
  }
};

export const findElements = async (sessionId, description) => {
  try {
    const response = await axios.post(`${API}/automation/find-elements`, {
      session_id: sessionId,
      description
    });
    return response.data;
  } catch (error) {
    console.error('Error finding elements:', error);
    throw error;
  }
};

export const smartClick = async (sessionId, description) => {
  try {
    const response = await axios.post(`${API}/automation/smart-click`, {
      session_id: sessionId,
      description
    });
    return response.data;
  } catch (error) {
    console.error('Error smart clicking:', error);
    throw error;
  }
};

export const typeText = async (sessionId, description, text) => {
  try {
    const response = await axios.post(`${API}/automation/type-text`, {
      session_id: sessionId,
      description,
      text
    });
    return response.data;
  } catch (error) {
    console.error('Error typing text:', error);
    throw error;
  }
};

export const getAutomationScreenshot = async (sessionId) => {
  try {
    const response = await axios.get(`${API}/automation/screenshot/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting screenshot:', error);
    throw error;
  }
};

export const closeAutomationSession = async (sessionId) => {
  try {
    const response = await axios.post(`${API}/automation/session/close`, {
      session_id: sessionId
    });
    return response.data;
  } catch (error) {
    console.error('Error closing session:', error);
    throw error;
  }
};

// Planning API
export const generatePlan = async (goal, model = 'openai/gpt-5') => {
  try {
    console.log(`[API] generatePlan called with goal: "${goal}", model: ${model}`);
    const response = await axios.post(`${API}/planning/generate`, {
      goal,
      model
    });
    console.log(`[API] generatePlan response:`, response.data);
    return response.data;
  } catch (error) {
    console.error('[API] Error generating plan:', error);
    console.error('[API] Error response:', error.response?.data);
    throw error;
  }
};