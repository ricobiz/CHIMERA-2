import React, { useState } from 'react';
import { Send, ChevronDown, Save } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { samplePrompts } from '../mockData';
import { CodeIcon, EyeIcon } from './Icons';

const ChatInterface = ({ onSendPrompt, messages = [], onSave, totalCost, onOpenSettings, activeModel, validatorEnabled, validatorModel }) => {
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
    <div className="flex-1 flex flex-col bg-[#0f0f10] h-screen">
      {/* Header */}
      <div className="border-b border-gray-800 p-3 md:p-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <h2 className="text-white font-semibold text-sm md:text-base">AI Assistant</h2>
            
            {/* Active Models - Minimal Display */}
            <div className="flex items-center gap-3 text-[10px] ml-4">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
                <CodeIcon className="w-3 h-3 text-blue-400" />
                <span className="text-blue-400">{activeModel?.split('/')[1]?.substring(0, 15) || 'claude-3.5-sonnet'}</span>
              </div>
              {validatorEnabled && (
                <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
                  <EyeIcon className="w-3 h-3 text-green-400" />
                  <span className="text-green-400">{validatorModel?.split('/')[1]?.substring(0, 15) || 'haiku'}</span>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Cost Display */}
            {totalCost > 0 && (
              <div className="px-2 py-1 bg-gray-800 rounded">
                <span className="text-[10px] text-gray-400 font-mono">
                  ${totalCost.toFixed(4)}
                </span>
              </div>
            )}
            {messages.length > 0 && (
              <Button
                onClick={onSave}
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white h-7"
              >
                <Save className="w-3.5 h-3.5" />
                <span className="hidden md:inline ml-1 text-xs">Save</span>
              </Button>
            )}
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
                    className="w-full p-3 md:p-4 bg-gray-900 hover:bg-gray-800 rounded-lg text-left text-sm md:text-base text-gray-400 hover:text-gray-300 transition-colors border border-gray-800"
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
                    ? 'bg-gray-900 border-gray-800 ml-4 md:ml-12'
                    : 'bg-gray-900/50 border-gray-800/50 mr-4 md:mr-12'
                }`}
              >
                <div className="flex items-start gap-2 md:gap-3">
                  <div className="flex-1">
                    <p className="text-xs text-gray-500 mb-1">
                      {msg.role === 'user' ? 'You' : 'Assistant'}
                    </p>
                    <p className="text-gray-300 whitespace-pre-wrap">{msg.content}</p>
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
              className="min-h-[80px] md:min-h-[100px] bg-gray-900 border-gray-800 text-sm md:text-base text-gray-300 resize-none pr-12 placeholder-gray-600"
            />
            <Button
              onClick={handleSubmit}
              disabled={!prompt.trim()}
              className="absolute bottom-2 md:bottom-3 right-2 md:right-3 bg-gray-700 hover:bg-gray-600 disabled:opacity-30 h-7 w-7 p-0"
              size="sm"
            >
              <Send className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;