import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, ChevronLeft, Check } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { getModels } from '../services/api';
import { toast } from '../hooks/use-toast';

const Settings = ({ selectedModel, onModelChange, onClose, visualValidatorEnabled, onVisualValidatorToggle, visualValidatorModel, onVisualValidatorModelChange }) => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, free, paid
  const [localValidatorEnabled, setLocalValidatorEnabled] = useState(visualValidatorEnabled);
  const [localValidatorModel, setLocalValidatorModel] = useState(visualValidatorModel);

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
        description: "Failed to load models. Using default.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleModelSelect = (modelId) => {
    onModelChange(modelId);
    // Save to localStorage
    localStorage.setItem('selectedModel', modelId);
    toast({
      title: "Model Updated",
      description: "Your AI model preference has been saved.",
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
              className="text-gray-400 hover:text-white"
            >
              <ChevronLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-2">
              <SettingsIcon className="w-5 h-5 text-purple-400" />
              <h2 className="text-white font-semibold text-lg">Settings</h2>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Model Selection Section */}
          <div>
            <h3 className="text-white font-semibold text-xl mb-2">AI Model Selection</h3>
            <p className="text-gray-400 text-sm mb-4">
              Choose the AI model that best fits your needs. Each model has different capabilities and pricing.
            </p>

            {/* Search */}
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="Search models..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1 p-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500"
              />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="p-3 bg-gray-800 border border-gray-700 rounded-lg text-white"
              >
                <option value="all">All Models</option>
                <option value="free">Free Only</option>
                <option value="paid">Paid Only</option>
              </select>
            </div>

            {/* Model Count */}
            <p className="text-sm text-gray-400 mb-4">
              Showing {filteredModels.length} of {models.length} models
            </p>

            {/* Models List */}
            {loading ? (
              <div className="text-center py-8 text-gray-400">Loading models...</div>
            ) : (
              <div className="space-y-3">
                {filteredModels.map((model) => (
                  <Card
                    key={model.id}
                    onClick={() => handleModelSelect(model.id)}
                    className={`p-4 cursor-pointer transition-all hover:border-purple-500 ${
                      selectedModel === model.id
                        ? 'bg-purple-600/20 border-purple-500'
                        : 'bg-gray-800/50 border-gray-700'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="text-white font-medium">{model.name}</h4>
                          {selectedModel === model.id && (
                            <Check className="w-5 h-5 text-purple-400" />
                          )}
                        </div>
                        
                        {model.description && (
                          <p className="text-sm text-gray-400 mb-3 line-clamp-2">
                            {model.description}
                          </p>
                        )}

                        {/* Capabilities */}
                        <div className="flex flex-wrap gap-2 mb-3">
                          {model.capabilities.tools && (
                            <Badge variant="secondary" className="text-xs bg-blue-600/20 text-blue-400 border-blue-600/30">
                              Tools
                            </Badge>
                          )}
                          {model.capabilities.vision && (
                            <Badge variant="secondary" className="text-xs bg-green-600/20 text-green-400 border-green-600/30">
                              Vision
                            </Badge>
                          )}
                          {model.capabilities.streaming && (
                            <Badge variant="secondary" className="text-xs bg-purple-600/20 text-purple-400 border-purple-600/30">
                              Streaming
                            </Badge>
                          )}
                          {model.context_length > 0 && (
                            <Badge variant="secondary" className="text-xs bg-gray-600/20 text-gray-400 border-gray-600/30">
                              {(model.context_length / 1000).toFixed(0)}K context
                            </Badge>
                          )}
                        </div>

                        {/* Pricing */}
                        <div className="flex items-center gap-4 text-xs">
                          <div className="text-gray-400">
                            <span className="text-gray-500">Input:</span>{' '}
                            <span className="text-green-400 font-mono">
                              ${(model.pricing.prompt * 1000000).toFixed(2)}/M
                            </span>
                          </div>
                          <div className="text-gray-400">
                            <span className="text-gray-500">Output:</span>{' '}
                            <span className="text-green-400 font-mono">
                              ${(model.pricing.completion * 1000000).toFixed(2)}/M
                            </span>
                          </div>
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