import React, { useState } from 'react';
import { Send, ChevronDown, Save, Settings } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { samplePrompts } from '../mockData';
import StatusIndicator from './StatusIndicator';
import ModelIndicator from './ModelIndicator';

const ChatInterface = ({ onSendPrompt, messages = [], onSave, totalCost, activeModel, validatorEnabled, validatorModel, generationStatus = 'idle', onOpenSettings }) => {
  const [prompt, setPrompt] = useState('');
  const [showSamples, setShowSamples] = useState(true);

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
    <div className="flex-1 flex flex-col bg-[#0f0f10] h-screen border-2 border-transparent animated-gradient-border">
      {/* Header */}
      <div className="border-b border-gray-800 p-3 md:p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-white font-medium text-sm">AI Assistant</h2>
          
          <div className="flex items-center gap-4">
            {/* Model Indicators + Settings */}
            <div className="flex items-center gap-3">
              <ModelIndicator 
                type="code" 
                modelName={activeModel?.split('/').pop()}
                isActive={true}
              />
              <ModelIndicator 
                type="validator" 
                modelName={validatorModel?.split('/').pop()}
                isActive={validatorEnabled}
              />
              <button
                onClick={onOpenSettings}
                className="text-gray-400 hover:text-gray-300 transition-colors"
                title="Settings"
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>
            
            {/* Status & Save */}
            <div className="flex items-center gap-3">
              <StatusIndicator />
              
              {messages.length > 0 && (
                <Button
                  onClick={onSave}
                  variant="ghost"
                  size="sm"
                  className="text-gray-500 hover:text-gray-400 h-6 px-2"
                >
                  <Save className="w-3 h-3" />
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 md:p-6">
        {messages.length === 0 ? (
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-6 md:mb-8">
              <h1 className="text-2xl md:text-4xl font-bold text-white mb-2 md:mb-4">
                Build with AI
              </h1>
              <p className="text-sm md:text-base text-gray-400">
                Describe your app and watch it come to life
              </p>
            </div>

            {showSamples && (
              <div className="space-y-2 md:space-y-3 mb-6 md:mb-8">
                <div className="flex items-center justify-between mb-3 md:mb-4">
                  <span className="text-xs md:text-sm text-gray-500">Examples</span>
                  <button
                    onClick={() => setShowSamples(!showSamples)}
                    className="text-gray-500 hover:text-gray-400 transition-colors"
                  >
                    <ChevronDown className="w-4 h-4" />
                  </button>
                </div>
                {samplePrompts.map((sample, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSampleClick(sample)}
                    className="w-full p-3 md:p-4 bg-gray-900 hover:bg-gray-800 rounded-lg text-left text-sm md:text-base text-gray-400 hover:text-gray-300 transition-colors border border-gray-800 hover:border-purple-500/30"
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
                className={`p-3 md:p-4 rounded-lg text-sm md:text-base border ${
                  msg.role === 'user'
                    ? 'bg-gray-900 border-blue-500/30 ml-4 md:ml-12 glow-blue'
                    : msg.role === 'design'
                    ? 'bg-purple-900/20 border-purple-500/30 mr-4 md:mr-12 glow-purple'
                    : 'bg-gray-900/50 border-gray-700 mr-4 md:mr-12'
                }`}
              >
                <div className="flex items-start gap-2 md:gap-3">
                  <div className="flex-1">
                    <p className="text-xs text-gray-500 mb-1">
                      {msg.role === 'user' ? 'You' : msg.role === 'design' ? 'Design Proposal' : 'Assistant'}
                    </p>
                    <p className="text-gray-300 whitespace-pre-wrap">{msg.content}</p>
                    {msg.image && (
                      <img src={msg.image} alt="Design" className="mt-3 rounded-lg max-w-md" />
                    )}
                    {msg.cost && (
                      <p className="text-[10px] text-gray-600 mt-2 font-mono">
                        ${msg.cost.total_cost.toFixed(6)} • {msg.cost.total_tokens} tokens
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
              placeholder="Describe your app..."
              className={`min-h-[80px] md:min-h-[100px] bg-gray-900 text-sm md:text-base text-gray-300 resize-none pr-12 placeholder-gray-600 transition-all duration-300 ${
                generationStatus === 'generating' 
                  ? 'border-2 border-blue-400 shadow-lg shadow-blue-500/50' 
                  : generationStatus === 'success'
                  ? 'border-2 border-green-400 shadow-lg shadow-green-500/50'
                  : generationStatus === 'error'
                  ? 'border-2 border-red-400 shadow-lg shadow-red-500/50'
                  : 'border border-gray-700 focus:border-purple-500/50'
              }`}
            />
            <Button
              onClick={handleSubmit}
              disabled={!prompt.trim()}
              className="absolute bottom-2 md:bottom-3 right-2 md:right-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-30 h-7 w-7 p-0"
              size="sm"
            >
              <Send className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>
      </div>
      
      {/* Add CSS for animated gradient border */}
      <style jsx>{`
        .animated-gradient-border {
          position: relative;
          border: 2px solid transparent;
          background: linear-gradient(#0f0f10, #0f0f10) padding-box,
                      linear-gradient(90deg, 
                        rgba(139, 92, 246, 0.3),
                        rgba(59, 130, 246, 0.3),
                        rgba(16, 185, 129, 0.3),
                        rgba(59, 130, 246, 0.3),
                        rgba(139, 92, 246, 0.3)
                      ) border-box;
          background-size: 200% 100%;
          animation: gradientShift 3s ease infinite;
        }
        
        @keyframes gradientShift {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        
        .glow-blue {
          box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
        }
        
        .glow-purple {
          box-shadow: 0 0 10px rgba(139, 92, 246, 0.2);
        }
      `}</style>
    </div>
  );
};

export default ChatInterface;