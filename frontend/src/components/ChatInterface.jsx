import React, { useState, useEffect } from 'react';
import { Send, Sparkles, ChevronDown, Save, Settings } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { samplePrompts } from '../mockData';
import { getModels } from '../services/api';

const ChatInterface = ({ onSendPrompt, messages = [], onSave, selectedModel, onModelChange, totalCost }) => {
  const [prompt, setPrompt] = useState('');
  const [showSamples, setShowSamples] = useState(true);
  const [models, setModels] = useState([]);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const data = await getModels();
      setModels(data.models || []);
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const handleSubmit = () => {
    if (prompt.trim()) {
      onSendPrompt(prompt);
      setPrompt('');
      setShowSamples(false);
    }
  };

  const handleSampleClick = (sample) => {
    setPrompt(sample);
  };

  return (
    <div className="flex-1 flex flex-col bg-[#0f0f10] h-screen">
      {/* Header */}
      <div className="border-b border-gray-800 p-3 md:p-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <h2 className="text-white font-semibold text-sm md:text-base">AI Code Assistant</h2>
          </div>
          <div className="flex items-center gap-2">
            {/* Cost Display */}
            {totalCost > 0 && (
              <div className="px-3 py-1 bg-green-600/20 border border-green-600/30 rounded-lg">
                <span className="text-xs text-green-400 font-mono">
                  ${totalCost.toFixed(6)}
                </span>
              </div>
            )}
            {messages.length > 0 && (
              <>
                <Button
                  onClick={() => setShowSettings(!showSettings)}
                  variant="outline"
                  size="sm"
                  className="gap-2 border-gray-700 hover:bg-gray-800 text-white hidden md:flex"
                >
                  <Settings className="w-4 h-4" />
                  <span className="hidden lg:inline">Settings</span>
                </Button>
                <Button
                  onClick={onSave}
                  variant="outline"
                  size="sm"
                  className="gap-2 border-gray-700 hover:bg-gray-800 text-white"
                >
                  <Save className="w-4 h-4" />
                  <span className="hidden md:inline">Save</span>
                </Button>
              </>
            )}
          </div>
        </div>
        
        {/* Model Selector - Collapsible */}
        {showSettings && (
          <div className="mt-3 pt-3 border-t border-gray-700">
            <label className="text-xs text-gray-400 mb-2 block">AI Model</label>
            <Select value={selectedModel} onValueChange={onModelChange}>
              <SelectTrigger className="w-full md:w-64 bg-gray-800 border-gray-700 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                {models.map((model) => (
                  <SelectItem key={model.id} value={model.id} className="text-white hover:bg-gray-700">
                    <div className="flex flex-col">
                      <span>{model.name}</span>
                      <span className="text-xs text-gray-400">
                        ${model.input_cost_per_1m}/M in • ${model.output_cost_per_1m}/M out
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 md:p-6">
        {messages.length === 0 ? (
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-6 md:mb-8">
              <h1 className="text-2xl md:text-4xl font-bold text-white mb-2 md:mb-4">
                Prototype an app with AI
              </h1>
              <p className="text-sm md:text-base text-gray-400">
                Describe your app idea and watch it come to life
              </p>
            </div>

            {showSamples && (
              <div className="space-y-2 md:space-y-3 mb-6 md:mb-8">
                <div className="flex items-center justify-between mb-3 md:mb-4">
                  <span className="text-xs md:text-sm text-gray-400">Sample prompts</span>
                  <button
                    onClick={() => setShowSamples(!showSamples)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <ChevronDown className="w-4 h-4" />
                  </button>
                </div>
                {samplePrompts.map((sample, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSampleClick(sample)}
                    className="w-full p-3 md:p-4 bg-gray-800/50 hover:bg-gray-800 rounded-lg text-left text-sm md:text-base text-gray-300 transition-colors"
                  >
                    {sample}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-3 md:space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`p-3 md:p-4 rounded-lg text-sm md:text-base ${
                  msg.role === 'user'
                    ? 'bg-blue-600/20 border border-blue-600/30 ml-4 md:ml-12'
                    : 'bg-gray-800/50 border border-gray-700 mr-4 md:mr-12'
                }`}
              >
                <div className="flex items-start gap-2 md:gap-3">
                  {msg.role === 'assistant' && (
                    <Sparkles className="w-4 h-4 md:w-5 md:h-5 text-purple-400 mt-1" />
                  )}
                  <div className="flex-1">
                    <p className="text-xs md:text-sm text-gray-400 mb-1">
                      {msg.role === 'user' ? 'You' : 'AI Assistant'}
                    </p>
                    <p className="text-white whitespace-pre-wrap">{msg.content}</p>
                    {msg.cost && (
                      <p className="text-xs text-green-400 mt-2 font-mono">
                        Cost: ${msg.cost.total_cost.toFixed(6)} ({msg.cost.total_tokens} tokens)
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 p-3 md:p-6">
        <div className="max-w-3xl mx-auto">
          <div className="relative">
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder="Describe your app idea..."
              className="min-h-[80px] md:min-h-[120px] bg-gray-800/50 border-gray-700 text-sm md:text-base text-white resize-none pr-12"
            />
            <Button
              onClick={handleSubmit}
              disabled={!prompt.trim()}
              className="absolute bottom-2 md:bottom-3 right-2 md:right-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50"
              size="sm"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;