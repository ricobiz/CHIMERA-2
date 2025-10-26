import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, ChevronLeft, Check, Plus, Trash2, Eye, EyeOff, Server, Link2, AlertCircle, CheckCircle2, XCircle, Search, Book } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Switch } from './ui/switch';
import { getModels, createIntegration, getIntegrations, updateIntegration, deleteIntegration, createMCPServer, getMCPServers, updateMCPServer, deleteMCPServer, healthCheckMCPServer } from '../services/api';
import { toast } from '../hooks/use-toast';
import { CodeIcon, EyeIcon } from './Icons';
import KnowledgeBase from './KnowledgeBase';

const Settings = ({ selectedModel, onModelChange, onClose, visualValidatorEnabled, onVisualValidatorToggle, visualValidatorModel, onVisualValidatorModelChange, researchPlannerEnabled, onResearchPlannerToggle, researchPlannerModel, onResearchPlannerModelChange }) => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [localValidatorEnabled, setLocalValidatorEnabled] = useState(visualValidatorEnabled);
  const [localValidatorModel, setLocalValidatorModel] = useState(visualValidatorModel);
  const [validatorSearchTerm, setValidatorSearchTerm] = useState('');
  const [localResearchEnabled, setLocalResearchEnabled] = useState(researchPlannerEnabled);
  const [localResearchModel, setLocalResearchModel] = useState(researchPlannerModel);
  const [researchSearchTerm, setResearchSearchTerm] = useState('');
  
  // Secrets management
  const [activeTab, setActiveTab] = useState('models'); // 'models', 'secrets', 'integrations', 'mcp'
  const [showKnowledgeBase, setShowKnowledgeBase] = useState(false);
  const [language, setLanguage] = useState(localStorage.getItem('chimera_language') || 'en');
  const [secrets, setSecrets] = useState(() => {
    const saved = localStorage.getItem('user_secrets');
    return saved ? JSON.parse(saved) : [];
  });
  const [newSecretName, setNewSecretName] = useState('');
  const [newSecretValue, setNewSecretValue] = useState('');
  const [showValues, setShowValues] = useState({});

  // Integrations state
  const [integrations, setIntegrations] = useState([]);
  const [integrationsLoading, setIntegrationsLoading] = useState(false);
  const [newIntegration, setNewIntegration] = useState({
    service_type: 'huggingface',
    name: '',
    credentials: {},
    enabled: true
  });

  // MCP Servers state
  const [mcpServers, setMcpServers] = useState([]);
  const [mcpLoading, setMcpLoading] = useState(false);
  const [newMCPServer, setNewMCPServer] = useState({
    name: '',
    server_type: 'custom',
    endpoint_url: '',
    authentication: {},
    enabled: true,
    priority: 0,
    fallback_order: null
  });

  useEffect(() => {
    loadModels();
    if (activeTab === 'integrations') {
      loadIntegrations();
    } else if (activeTab === 'mcp') {
      loadMCPServers();
    }
  }, [activeTab]);

  const loadModels = async () => {
    try {
      const data = await getModels();
      setModels(data.models || []);
    } catch (error) {
      console.error('Failed to load models:', error);
      toast({
        title: "Error",
        description: "Failed to load models.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleModelSelect = (modelId) => {
    onModelChange(modelId);
    localStorage.setItem('selectedModel', modelId);
    toast({
      title: "Model Updated",
      description: "Your AI model has been updated.",
    });
  };

  const handleValidatorToggle = (enabled) => {
    setLocalValidatorEnabled(enabled);
    onVisualValidatorToggle(enabled);
    localStorage.setItem('visualValidatorEnabled', enabled);
    toast({
      title: enabled ? "Validator Enabled" : "Validator Disabled",
      description: enabled ? "Visual validation is now active." : "Visual validation disabled.",
    });
  };

  const handleValidatorModelSelect = (modelId) => {
    setLocalValidatorModel(modelId);
    onVisualValidatorModelChange(modelId);
    localStorage.setItem('visualValidatorModel', modelId);
    toast({
      title: "Validator Model Updated",
      description: "Validation model changed.",
    });
  };

  // Research Planner functions
  const handleResearchToggle = (enabled) => {
    setLocalResearchEnabled(enabled);
    onResearchPlannerToggle(enabled);
    localStorage.setItem('researchPlannerEnabled', enabled);
    toast({
      title: enabled ? "Research Planner Enabled" : "Research Planner Disabled",
      description: enabled ? "Task research is now active." : "Research disabled.",
    });
  };

  const handleResearchModelSelect = (modelId) => {
    setLocalResearchModel(modelId);
    onResearchPlannerModelChange(modelId);
    localStorage.setItem('researchPlannerModel', modelId);
    toast({
      title: "Research Model Updated",
      description: "Research planner model changed.",
    });
  };

  // Secrets management functions
  const handleAddSecret = () => {
    if (!newSecretName.trim() || !newSecretValue.trim()) {
      toast({
        title: "Invalid Input",
        description: "Please provide both name and value.",
        variant: "destructive"
      });
      return;
    }

    const newSecret = {
      id: Date.now().toString(),
      name: newSecretName.trim(),
      value: newSecretValue.trim(),
      createdAt: new Date().toISOString()
    };

    const updatedSecrets = [...secrets, newSecret];
    setSecrets(updatedSecrets);
    localStorage.setItem('user_secrets', JSON.stringify(updatedSecrets));
    
    setNewSecretName('');
    setNewSecretValue('');
    
    toast({
      title: "Secret Added",
      description: `${newSecretName} has been saved.`,
    });
  };

  const handleDeleteSecret = (id) => {
    const updatedSecrets = secrets.filter(s => s.id !== id);
    setSecrets(updatedSecrets);
    localStorage.setItem('user_secrets', JSON.stringify(updatedSecrets));
    
    toast({
      title: "Secret Deleted",
      description: "Secret has been removed.",
    });
  };

  const toggleShowValue = (id) => {
    setShowValues(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  // ========== Integrations Functions ==========

  const loadIntegrations = async () => {
    setIntegrationsLoading(true);
    try {
      const data = await getIntegrations();
      setIntegrations(data || []);
    } catch (error) {
      console.error('Failed to load integrations:', error);
      toast({
        title: "Error",
        description: "Failed to load integrations.",
        variant: "destructive"
      });
    } finally {
      setIntegrationsLoading(false);
    }
  };

  const handleAddIntegration = async () => {
    if (!newIntegration.name.trim()) {
      toast({
        title: "Invalid Input",
        description: "Please provide integration name.",
        variant: "destructive"
      });
      return;
    }

    try {
      await createIntegration(newIntegration);
      toast({
        title: "Integration Added",
        description: `${newIntegration.name} has been added.`,
      });
      setNewIntegration({
        service_type: 'huggingface',
        name: '',
        credentials: {},
        enabled: true
      });
      loadIntegrations();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add integration.",
        variant: "destructive"
      });
    }
  };

  const handleDeleteIntegration = async (id) => {
    try {
      await deleteIntegration(id);
      toast({
        title: "Integration Deleted",
        description: "Integration has been removed.",
      });
      loadIntegrations();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete integration.",
        variant: "destructive"
      });
    }
  };

  const handleToggleIntegration = async (id, enabled) => {
    try {
      await updateIntegration(id, { enabled });
      toast({
        title: enabled ? "Integration Enabled" : "Integration Disabled",
        description: "Integration status updated.",
      });
      loadIntegrations();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update integration.",
        variant: "destructive"
      });
    }
  };

  // ========== MCP Servers Functions ==========

  const loadMCPServers = async () => {
    setMcpLoading(true);
    try {
      const data = await getMCPServers();
      setMcpServers(data || []);
    } catch (error) {
      console.error('Failed to load MCP servers:', error);
      toast({
        title: "Error",
        description: "Failed to load MCP servers.",
        variant: "destructive"
      });
    } finally {
      setMcpLoading(false);
    }
  };

  const handleAddMCPServer = async () => {
    if (!newMCPServer.name.trim()) {
      toast({
        title: "Invalid Input",
        description: "Please provide server name.",
        variant: "destructive"
      });
      return;
    }

    if (newMCPServer.server_type === 'custom' && !newMCPServer.endpoint_url.trim()) {
      toast({
        title: "Invalid Input",
        description: "Custom servers require an endpoint URL.",
        variant: "destructive"
      });
      return;
    }

    try {
      await createMCPServer(newMCPServer);
      toast({
        title: "MCP Server Added",
        description: `${newMCPServer.name} has been added.`,
      });
      setNewMCPServer({
        name: '',
        server_type: 'custom',
        endpoint_url: '',
        authentication: {},
        enabled: true,
        priority: 0,
        fallback_order: null
      });
      loadMCPServers();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add MCP server.",
        variant: "destructive"
      });
    }
  };

  const handleDeleteMCPServer = async (id) => {
    try {
      await deleteMCPServer(id);
      toast({
        title: "Server Deleted",
        description: "MCP server has been removed.",
      });
      loadMCPServers();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete MCP server.",
        variant: "destructive"
      });
    }
  };

  const handleToggleMCPServer = async (id, enabled) => {
    try {
      await updateMCPServer(id, { enabled });
      toast({
        title: enabled ? "Server Enabled" : "Server Disabled",
        description: "Server status updated.",
      });
      loadMCPServers();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update server.",
        variant: "destructive"
      });
    }
  };

  const handleHealthCheck = async (id) => {
    try {
      const result = await healthCheckMCPServer(id);
      toast({
        title: "Health Check",
        description: `Server is ${result.status}`,
      });
      loadMCPServers();
    } catch (error) {
      toast({
        title: "Health Check Failed",
        description: "Unable to reach server.",
        variant: "destructive"
      });
    }
  };

  // Language change handler
  const handleLanguageChange = (newLanguage) => {
    setLanguage(newLanguage);
    localStorage.setItem('chimera_language', newLanguage);
    
    // Update i18n language
    import('i18next').then((i18n) => {
      if (i18n.default && i18n.default.changeLanguage) {
        i18n.default.changeLanguage(newLanguage);
      }
    });
    
    toast({
      title: newLanguage === 'en' ? "Language Changed" : "Язык Изменен",
      description: newLanguage === 'en' ? "Interface language updated to English." : "Язык интерфейса изменен на Русский.",
    });
  };

  const filteredModels = models.filter(model => {
    const matchesSearch = model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      model.id.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = 
      filterType === 'all' ? true :
      filterType === 'free' ? (model.pricing.prompt === 0 && model.pricing.completion === 0) :
      filterType === 'paid' ? (model.pricing.prompt > 0 || model.pricing.completion > 0) :
      true;
    
    return matchesSearch && matchesFilter;
  });

  const visionModels = models
    .filter(model => {
      const hasVision = model.capabilities?.vision;
      const matchesSearch = validatorSearchTerm === '' || 
                          model.name.toLowerCase().includes(validatorSearchTerm.toLowerCase()) ||
                          model.id.toLowerCase().includes(validatorSearchTerm.toLowerCase());
      
      return hasVision && matchesSearch;
    })
    .sort((a, b) => {
      const priceA = a.pricing.prompt + a.pricing.completion;
      const priceB = b.pricing.prompt + b.pricing.completion;
      return priceA - priceB;
    });

  return (
    <div className="flex-1 flex flex-col bg-[#0f0f10] overflow-x-hidden" style={{ height: '100dvh' }}>
      {/* Header */}
      <div className="border-b border-gray-800 p-4 w-full">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <Button
              onClick={onClose}
              variant="ghost"
              size="sm"
              className="text-gray-500 hover:text-gray-400 flex-shrink-0"
            >
              <ChevronLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-2 min-w-0">
              <SettingsIcon className="w-5 h-5 text-gray-400 flex-shrink-0" />
              <h2 className="text-gray-300 font-semibold text-base md:text-lg truncate">Settings</h2>
            </div>
          </div>
          <Button
            onClick={onClose}
            className="bg-gray-700 hover:bg-gray-600 text-gray-300 flex-shrink-0 text-xs md:text-sm"
            size="sm"
          >
            <span className="hidden sm:inline">Save & Close</span>
            <span className="sm:hidden">Save</span>
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-3 md:p-4 lg:p-6 w-full">
        <div className="max-w-4xl mx-auto space-y-4 md:space-y-6 w-full">
          
          {/* Tabs - Scrollable on mobile */}
          <div className="flex gap-2 border-b border-gray-800 pb-2 overflow-x-auto scrollbar-hide">
            <button
              onClick={() => setActiveTab('models')}
              className={`px-3 md:px-4 py-2 text-xs md:text-sm font-medium transition-colors rounded-t-lg whitespace-nowrap ${
                activeTab === 'models'
                  ? 'bg-gray-800 text-white border-b-2 border-purple-500'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              Models
            </button>
            <button
              onClick={() => setActiveTab('secrets')}
              className={`px-3 md:px-4 py-2 text-xs md:text-sm font-medium transition-colors rounded-t-lg whitespace-nowrap ${
                activeTab === 'secrets'
                  ? 'bg-gray-800 text-white border-b-2 border-purple-500'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              API Keys & Secrets
            </button>
            <button
              onClick={() => setActiveTab('integrations')}
              className={`px-3 md:px-4 py-2 text-xs md:text-sm font-medium transition-colors rounded-t-lg whitespace-nowrap ${
                activeTab === 'integrations'
                  ? 'bg-gray-800 text-white border-b-2 border-purple-500'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              Integrations
            </button>
            <button
              onClick={() => setActiveTab('mcp')}
              className={`px-3 md:px-4 py-2 text-xs md:text-sm font-medium transition-colors rounded-t-lg whitespace-nowrap ${
                activeTab === 'mcp'
                  ? 'bg-gray-800 text-white border-b-2 border-purple-500'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              MCP Servers
            </button>
            <button
              onClick={() => setActiveTab('language')}
              className={`px-3 md:px-4 py-2 text-xs md:text-sm font-medium transition-colors rounded-t-lg whitespace-nowrap ${
                activeTab === 'language'
                  ? 'bg-gray-800 text-white border-b-2 border-purple-500'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              Language
            </button>
          </div>

          {/* Models Tab */}
          {activeTab === 'models' && (
            <>
          {/* Visual Validator Section */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <EyeIcon className="w-4 h-4 text-gray-400" />
                  <h3 className="text-gray-300 font-semibold text-base">Visual Validator</h3>
                </div>
                <p className="text-gray-500 text-sm">
                  Enable AI-powered visual validation to ensure UI quality and catch layout issues.
                </p>
              </div>
              <Switch
                checked={localValidatorEnabled}
                onCheckedChange={handleValidatorToggle}
                className="data-[state=checked]:bg-gray-600"
              />
            </div>

            {localValidatorEnabled && (
              <div className="mt-4 pt-4 border-t border-gray-800">
                <label className="text-xs text-gray-500 mb-3 block font-medium">Validator Model ({visionModels.length} available)</label>
                
                <input
                  type="text"
                  placeholder="Search..."
                  value={validatorSearchTerm}
                  onChange={(e) => setValidatorSearchTerm(e.target.value)}
                  className="w-full p-2 mb-3 bg-gray-900 border border-gray-800 rounded text-gray-300 text-xs placeholder-gray-600"
                />

                <div className="grid gap-2 max-h-72 overflow-y-auto pr-2">
                  {visionModels.map((model) => {
                    const isFree = model.pricing.prompt === 0 && model.pricing.completion === 0;
                    return (
                      <div
                        key={model.id}
                        onClick={() => handleValidatorModelSelect(model.id)}
                        className={`p-2.5 rounded cursor-pointer transition-all border text-xs ${
                          localValidatorModel === model.id
                            ? 'bg-gray-800 border-gray-700'
                            : 'bg-gray-900/50 border-gray-800/50 hover:border-gray-700'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <p className="text-gray-300 font-medium">{model.name}</p>
                              {localValidatorModel === model.id && (
                                <Check className="w-3 h-3 text-gray-500" />
                              )}
                              {isFree && (
                                <span className="text-[10px] text-gray-500">FREE</span>
                              )}
                            </div>
                            <p className="text-[10px] text-gray-600 mb-1.5">{model.id}</p>
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] text-gray-600 font-mono">
                                {isFree ? 'No cost' : `$${(model.pricing.prompt * 1000000).toFixed(2)}/M`}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Research Planner Section */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Search className="w-4 h-4 text-gray-400" />
                  <h3 className="text-gray-300 font-semibold text-base">Research Planner</h3>
                </div>
                <p className="text-gray-500 text-sm">
                  Enable AI-powered research to investigate current best practices before complex tasks. 
                  Ensures modern approaches and up-to-date technology stacks.
                </p>
              </div>
              <Switch
                checked={localResearchEnabled}
                onCheckedChange={handleResearchToggle}
                className="data-[state=checked]:bg-gray-600"
              />
            </div>

            {localResearchEnabled && (
              <div className="mt-4 pt-4 border-t border-gray-800">
                <label className="text-xs text-gray-500 mb-3 block font-medium">Research Model ({models.length} available)</label>
                
                <input
                  type="text"
                  placeholder="Search..."
                  value={researchSearchTerm}
                  onChange={(e) => setResearchSearchTerm(e.target.value)}
                  className="w-full p-2 mb-3 bg-gray-900 border border-gray-800 rounded text-gray-300 text-xs placeholder-gray-600"
                />

                <div className="grid gap-2 max-h-72 overflow-y-auto pr-2">
                  {models
                    .filter(model => {
                      const matchesSearch = researchSearchTerm === '' || 
                                          model.name.toLowerCase().includes(researchSearchTerm.toLowerCase()) ||
                                          model.id.toLowerCase().includes(researchSearchTerm.toLowerCase());
                      return matchesSearch;
                    })
                    .map((model) => {
                      const isFree = model.pricing.prompt === 0 && model.pricing.completion === 0;
                      return (
                        <div
                          key={model.id}
                          onClick={() => handleResearchModelSelect(model.id)}
                          className={`p-2.5 rounded cursor-pointer transition-all border text-xs ${
                            localResearchModel === model.id
                              ? 'bg-gray-800 border-gray-700'
                              : 'bg-gray-900/50 border-gray-800/50 hover:border-gray-700'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <p className="text-gray-300 font-medium">{model.name}</p>
                                {localResearchModel === model.id && (
                                  <Check className="w-3 h-3 text-gray-500" />
                                )}
                                {isFree && (
                                  <span className="text-[10px] text-gray-500">FREE</span>
                                )}
                              </div>
                              <p className="text-[10px] text-gray-600 mb-1.5">{model.id}</p>
                              <div className="flex items-center gap-2">
                                <span className="text-[10px] text-gray-600 font-mono">
                                  {isFree ? 'No cost' : `$${(model.pricing.prompt * 1000000).toFixed(2)}/M`}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            )}
          </div>

          {/* Model Selection Section */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-3">
              <CodeIcon className="w-4 h-4 text-gray-400" />
              <h3 className="text-gray-300 font-semibold text-base">Code Generation Model</h3>
            </div>
            <p className="text-gray-500 text-sm mb-4">
              Select the AI model for generating code.
            </p>

            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="Search models..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1 p-2 bg-gray-900 border border-gray-800 rounded text-gray-300 text-xs placeholder-gray-600"
              />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="p-2 bg-gray-900 border border-gray-800 rounded text-gray-300 text-xs"
              >
                <option value="all">All</option>
                <option value="free">Free</option>
                <option value="paid">Paid</option>
              </select>
            </div>

            <p className="text-[10px] text-gray-600 mb-3">
              {filteredModels.length} of {models.length} models
            </p>

            {loading ? (
              <div className="text-center py-6 text-gray-600 text-sm">Loading...</div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
                {filteredModels.map((model) => (
                  <Card
                    key={model.id}
                    onClick={() => handleModelSelect(model.id)}
                    className={`p-2.5 cursor-pointer transition-all text-xs ${
                      selectedModel === model.id
                        ? 'bg-gray-800 border-gray-700'
                        : 'bg-gray-900/50 border-gray-800/50 hover:border-gray-700'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-gray-300 font-medium">{model.name}</h4>
                          {selectedModel === model.id && (
                            <Check className="w-3 h-3 text-gray-500" />
                          )}
                        </div>
                        
                        <div className="flex items-center gap-2 mb-1.5">
                          {model.capabilities.vision && (
                            <span className="text-[10px] text-gray-600">Vision</span>
                          )}
                          {model.capabilities.tools && (
                            <span className="text-[10px] text-gray-600">Tools</span>
                          )}
                          {model.context_length > 0 && (
                            <span className="text-[10px] text-gray-600">
                              {(model.context_length / 1000).toFixed(0)}K
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 text-[10px]">
                          <span className="text-gray-600 font-mono">
                            ${(model.pricing.prompt * 1000000).toFixed(2)}/M in
                          </span>
                          <span className="text-gray-600 font-mono">
                            ${(model.pricing.completion * 1000000).toFixed(2)}/M out
                          </span>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
            </>
          )}

          {/* Secrets Tab */}
          {activeTab === 'secrets' && (
            <div className="space-y-6">
              {/* Add New Secret */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
                <h3 className="text-gray-300 font-semibold text-base mb-4">Add New Secret</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Secret Name</label>
                    <input
                      type="text"
                      value={newSecretName}
                      onChange={(e) => setNewSecretName(e.target.value)}
                      placeholder="e.g., OPENROUTER_API_KEY, STRIPE_SECRET_KEY"
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 placeholder-gray-600 focus:border-purple-500 focus:outline-none text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Secret Value</label>
                    <input
                      type="password"
                      value={newSecretValue}
                      onChange={(e) => setNewSecretValue(e.target.value)}
                      placeholder="Enter API key or secret value"
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 placeholder-gray-600 focus:border-purple-500 focus:outline-none text-sm"
                    />
                  </div>
                  <Button
                    onClick={handleAddSecret}
                    className="w-full bg-purple-600 hover:bg-purple-500 text-white flex items-center justify-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add Secret
                  </Button>
                </div>
              </div>

              {/* Saved Secrets */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
                <h3 className="text-gray-300 font-semibold text-base mb-4">Saved Secrets ({secrets.length})</h3>
                {secrets.length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-4">No secrets saved yet</p>
                ) : (
                  <div className="space-y-3">
                    {secrets.map((secret) => (
                      <div key={secret.id} className="bg-gray-800/50 border border-gray-700 rounded-lg p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="text-gray-300 font-medium text-sm">{secret.name}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <p className="text-gray-500 text-xs font-mono">
                                {showValues[secret.id] ? secret.value : '••••••••••••••••'}
                              </p>
                              <button
                                onClick={() => toggleShowValue(secret.id)}
                                className="text-gray-500 hover:text-gray-400"
                              >
                                {showValues[secret.id] ? (
                                  <EyeOff className="w-3 h-3" />
                                ) : (
                                  <Eye className="w-3 h-3" />
                                )}
                              </button>
                            </div>
                            <p className="text-gray-600 text-xs mt-1">
                              Added: {new Date(secret.createdAt).toLocaleDateString()}
                            </p>
                          </div>
                          <button
                            onClick={() => handleDeleteSecret(secret.id)}
                            className="text-red-500 hover:text-red-400 p-2"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="bg-blue-900/20 border border-blue-800/50 rounded-lg p-4">
                <p className="text-blue-400 text-sm">
                  <strong>Note:</strong> Secrets are stored securely in your browser's localStorage. 
                  AI models will have access to these secrets when needed for API calls and integrations.
                </p>
              </div>
            </div>
          )}

          {/* Integrations Tab */}
          {activeTab === 'integrations' && (
            <div className="space-y-6">
              {/* Add New Integration */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Link2 className="w-5 h-5 text-gray-400" />
                  <h3 className="text-gray-300 font-semibold text-base">Add Service Integration</h3>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Service Type</label>
                    <select
                      value={newIntegration.service_type}
                      onChange={(e) => setNewIntegration({...newIntegration, service_type: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 focus:border-purple-500 focus:outline-none text-sm"
                    >
                      <option value="huggingface">Hugging Face</option>
                      <option value="github">GitHub</option>
                      <option value="gmail">Gmail</option>
                      <option value="google_drive">Google Drive</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Integration Name</label>
                    <input
                      type="text"
                      value={newIntegration.name}
                      onChange={(e) => setNewIntegration({...newIntegration, name: e.target.value})}
                      placeholder="e.g., My Hugging Face Account"
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 placeholder-gray-600 focus:border-purple-500 focus:outline-none text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">API Key / Token</label>
                    <input
                      type="password"
                      value={newIntegration.credentials.api_key || ''}
                      onChange={(e) => setNewIntegration({
                        ...newIntegration, 
                        credentials: {...newIntegration.credentials, api_key: e.target.value}
                      })}
                      placeholder="Enter API key or access token"
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 placeholder-gray-600 focus:border-purple-500 focus:outline-none text-sm"
                    />
                  </div>
                  <Button
                    onClick={handleAddIntegration}
                    className="w-full bg-purple-600 hover:bg-purple-500 text-white flex items-center justify-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add Integration
                  </Button>
                </div>
              </div>

              {/* Saved Integrations */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
                <h3 className="text-gray-300 font-semibold text-base mb-4">Service Integrations ({integrations.length})</h3>
                {integrationsLoading ? (
                  <div className="text-center py-6 text-gray-600 text-sm">Loading...</div>
                ) : integrations.length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-4">No integrations configured yet</p>
                ) : (
                  <div className="space-y-3">
                    {integrations.map((integration) => (
                      <div key={integration.id} className="bg-gray-800/50 border border-gray-700 rounded-lg p-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <p className="text-gray-300 font-medium text-sm">{integration.name}</p>
                              <Badge className="text-[10px] bg-gray-700 text-gray-300">{integration.service_type}</Badge>
                            </div>
                            <p className="text-gray-500 text-xs">
                              Added: {new Date(integration.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Switch
                              checked={integration.enabled}
                              onCheckedChange={(enabled) => handleToggleIntegration(integration.id, enabled)}
                              className="data-[state=checked]:bg-gray-600"
                            />
                            <button
                              onClick={() => handleDeleteIntegration(integration.id)}
                              className="text-red-500 hover:text-red-400 p-2"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="bg-blue-900/20 border border-blue-800/50 rounded-lg p-4">
                <p className="text-blue-400 text-sm">
                  <strong>Info:</strong> Integrations allow your AI agent to interact with external services like GitHub, 
                  Hugging Face, Gmail, and Google Drive. Enable/disable them as needed.
                </p>
              </div>
            </div>
          )}

          {/* MCP Servers Tab */}
          {activeTab === 'mcp' && (
            <div className="space-y-6">
              {/* Add New MCP Server */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Server className="w-5 h-5 text-gray-400" />
                  <h3 className="text-gray-300 font-semibold text-base">Add MCP Server</h3>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Server Type</label>
                    <select
                      value={newMCPServer.server_type}
                      onChange={(e) => setNewMCPServer({...newMCPServer, server_type: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 focus:border-purple-500 focus:outline-none text-sm"
                    >
                      <option value="browser_automation">Browser Automation (Puppeteer)</option>
                      <option value="filesystem">Filesystem Operations</option>
                      <option value="sequential_thinking">Sequential Thinking</option>
                      <option value="context">Context Management</option>
                      <option value="git">Git Operations</option>
                      <option value="custom">Custom Server</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Server Name</label>
                    <input
                      type="text"
                      value={newMCPServer.name}
                      onChange={(e) => setNewMCPServer({...newMCPServer, name: e.target.value})}
                      placeholder="e.g., My Browser Automation Server"
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 placeholder-gray-600 focus:border-purple-500 focus:outline-none text-sm"
                    />
                  </div>
                  {newMCPServer.server_type === 'custom' && (
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Endpoint URL</label>
                      <input
                        type="text"
                        value={newMCPServer.endpoint_url}
                        onChange={(e) => setNewMCPServer({...newMCPServer, endpoint_url: e.target.value})}
                        placeholder="https://your-mcp-server.com/api"
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 placeholder-gray-600 focus:border-purple-500 focus:outline-none text-sm"
                      />
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Priority (0-100)</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={newMCPServer.priority}
                        onChange={(e) => setNewMCPServer({...newMCPServer, priority: parseInt(e.target.value)})}
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 focus:border-purple-500 focus:outline-none text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Fallback Order</label>
                      <input
                        type="number"
                        min="0"
                        value={newMCPServer.fallback_order || ''}
                        onChange={(e) => setNewMCPServer({...newMCPServer, fallback_order: e.target.value ? parseInt(e.target.value) : null})}
                        placeholder="Optional"
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 placeholder-gray-600 focus:border-purple-500 focus:outline-none text-sm"
                      />
                    </div>
                  </div>
                  <Button
                    onClick={handleAddMCPServer}
                    className="w-full bg-purple-600 hover:bg-purple-500 text-white flex items-center justify-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add MCP Server
                  </Button>
                </div>
              </div>

              {/* Saved MCP Servers */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
                <h3 className="text-gray-300 font-semibold text-base mb-4">MCP Servers ({mcpServers.length})</h3>
                {mcpLoading ? (
                  <div className="text-center py-6 text-gray-600 text-sm">Loading...</div>
                ) : mcpServers.length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-4">No MCP servers configured yet</p>
                ) : (
                  <div className="space-y-3">
                    {mcpServers.map((server) => (
                      <div key={server.id} className="bg-gray-800/50 border border-gray-700 rounded-lg p-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <p className="text-gray-300 font-medium text-sm">{server.name}</p>
                              <Badge className="text-[10px] bg-gray-700 text-gray-300">{server.server_type}</Badge>
                              {server.health_status === 'healthy' && <CheckCircle2 className="w-3 h-3 text-green-500" />}
                              {server.health_status === 'unhealthy' && <XCircle className="w-3 h-3 text-red-500" />}
                              {server.health_status === 'unknown' && <AlertCircle className="w-3 h-3 text-gray-500" />}
                            </div>
                            <div className="flex items-center gap-3 text-xs text-gray-500">
                              <span>Priority: {server.priority}</span>
                              {server.fallback_order !== null && <span>Fallback: #{server.fallback_order}</span>}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleHealthCheck(server.id)}
                              className="text-gray-500 hover:text-gray-400 p-1 text-xs"
                              title="Health Check"
                            >
                              Test
                            </button>
                            <Switch
                              checked={server.enabled}
                              onCheckedChange={(enabled) => handleToggleMCPServer(server.id, enabled)}
                              className="data-[state=checked]:bg-gray-600"
                            />
                            <button
                              onClick={() => handleDeleteMCPServer(server.id)}
                              className="text-red-500 hover:text-red-400 p-2"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Advanced Features Info */}
              <div className="bg-blue-900/20 border border-blue-800/50 rounded-lg p-4">
                <p className="text-blue-400 text-sm mb-2">
                  <strong>Advanced Features:</strong>
                </p>
                <ul className="text-blue-400 text-xs space-y-1 list-disc list-inside">
                  <li><strong>Priority:</strong> Higher values are tried first (0-100)</li>
                  <li><strong>Fallback Order:</strong> If primary server fails, try servers in fallback order (0, 1, 2...)</li>
                  <li><strong>Health Check:</strong> Click "Test" to verify server connectivity</li>
                  <li><strong>Load Balancing:</strong> Multiple servers with same priority are load-balanced</li>
                </ul>
              </div>
            </div>
          )}

          {/* Language Tab */}
          {activeTab === 'language' && (
            <div className="space-y-6">
              {/* Language Selection */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
                <h3 className="text-gray-300 font-semibold text-base mb-4">Language Settings</h3>
                <p className="text-gray-500 text-sm mb-4">
                  Choose your preferred language for the interface
                </p>
                
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => handleLanguageChange('en')}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      language === 'en'
                        ? 'border-purple-500 bg-purple-500/10'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="text-center">
                      <div className="text-4xl mb-2">🇬🇧</div>
                      <div className="text-gray-300 font-semibold">English</div>
                      {language === 'en' && (
                        <div className="mt-2">
                          <Check className="w-5 h-5 text-purple-400 mx-auto" />
                        </div>
                      )}
                    </div>
                  </button>
                  
                  <button
                    onClick={() => handleLanguageChange('ru')}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      language === 'ru'
                        ? 'border-purple-500 bg-purple-500/10'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="text-center">
                      <div className="text-4xl mb-2">🇷🇺</div>
                      <div className="text-gray-300 font-semibold">Русский</div>
                      {language === 'ru' && (
                        <div className="mt-2">
                          <Check className="w-5 h-5 text-purple-400 mx-auto" />
                        </div>
                      )}
                    </div>
                  </button>
                </div>
              </div>

              {/* Knowledge Base Button */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Book className="w-5 h-5 text-blue-400" />
                  <h3 className="text-gray-300 font-semibold text-base">Knowledge Base</h3>
                </div>
                <p className="text-gray-500 text-sm mb-4">
                  {language === 'en' 
                    ? 'Access comprehensive documentation about all platform features, tips, and best practices.'
                    : 'Доступ к полной документации о всех возможностях платформы, советах и лучших практиках.'
                  }
                </p>
                <Button
                  onClick={() => setShowKnowledgeBase(true)}
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center gap-2"
                >
                  <Book className="w-4 h-4" />
                  {language === 'en' ? 'Open Knowledge Base' : 'Открыть Базу Знаний'}
                </Button>
              </div>

              {/* Info */}
              <div className="bg-blue-900/20 border border-blue-800/50 rounded-lg p-4">
                <p className="text-blue-400 text-sm">
                  {language === 'en' 
                    ? 'The interface will automatically switch to your selected language. AI responses will also adapt to match your language preferences based on your messages.'
                    : 'Интерфейс автоматически переключится на выбранный язык. AI ответы также адаптируются под ваш язык на основе ваших сообщений.'
                  }
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Knowledge Base Modal */}
      {showKnowledgeBase && (
        <KnowledgeBase 
          onClose={() => setShowKnowledgeBase(false)}
          language={language}
        />
      )}
    </div>
  );
};

export default Settings;