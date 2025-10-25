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