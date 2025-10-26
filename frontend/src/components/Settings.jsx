import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, ChevronLeft, Check, Plus, Trash2, Eye, EyeOff } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Switch } from './ui/switch';
import { getModels } from '../services/api';
import { toast } from '../hooks/use-toast';
import { CodeIcon, EyeIcon } from './Icons';

const Settings = ({ selectedModel, onModelChange, onClose, visualValidatorEnabled, onVisualValidatorToggle, visualValidatorModel, onVisualValidatorModelChange }) => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [localValidatorEnabled, setLocalValidatorEnabled] = useState(visualValidatorEnabled);
  const [localValidatorModel, setLocalValidatorModel] = useState(visualValidatorModel);
  const [validatorSearchTerm, setValidatorSearchTerm] = useState('');
  
  // Secrets management
  const [activeTab, setActiveTab] = useState('models'); // 'models' or 'secrets'
  const [secrets, setSecrets] = useState(() => {
    const saved = localStorage.getItem('user_secrets');
    return saved ? JSON.parse(saved) : [];
  });
  const [newSecretName, setNewSecretName] = useState('');
  const [newSecretValue, setNewSecretValue] = useState('');
  const [showValues, setShowValues] = useState({});

  useEffect(() => {
    loadModels();
  }, []);

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
    <div className="flex-1 flex flex-col bg-[#0f0f10] h-screen">
      {/* Header */}
      <div className="border-b border-gray-800 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              onClick={onClose}
              variant="ghost"
              size="sm"
              className="text-gray-500 hover:text-gray-400"
            >
              <ChevronLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-2">
              <SettingsIcon className="w-5 h-5 text-gray-400" />
              <h2 className="text-gray-300 font-semibold text-lg">Settings</h2>
            </div>
          </div>
          <Button
            onClick={onClose}
            className="bg-gray-700 hover:bg-gray-600 text-gray-300"
            size="sm"
          >
            Save & Close
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          
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
        </div>
      </div>
    </div>
  );
};

export default Settings;