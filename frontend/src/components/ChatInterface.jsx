import React, { useState } from 'react';
import { Send, Sparkles, ChevronDown } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { samplePrompts } from '../mockData';

const ChatInterface = ({ onSendPrompt, messages = [] }) => {
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
      <div className="border-b border-gray-800 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <h2 className="text-white font-semibold">AI Code Assistant</h2>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-4">
                Prototype an app with AI
              </h1>
              <p className="text-gray-400">
                Describe your app idea and watch it come to life
              </p>
            </div>

            {showSamples && (
              <div className="space-y-3 mb-8">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-gray-400">Sample prompts</span>
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
                    className="w-full p-4 bg-gray-800/50 hover:bg-gray-800 rounded-lg text-left text-gray-300 transition-colors"
                  >
                    {sample}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-blue-600/20 border border-blue-600/30 ml-12'
                    : 'bg-gray-800/50 border border-gray-700 mr-12'
                }`}
              >
                <div className="flex items-start gap-3">
                  {msg.role === 'assistant' && (
                    <Sparkles className="w-5 h-5 text-purple-400 mt-1" />
                  )}
                  <div className="flex-1">
                    <p className="text-sm text-gray-400 mb-1">
                      {msg.role === 'user' ? 'You' : 'AI Assistant'}
                    </p>
                    <p className="text-white whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 p-6">
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
              className="min-h-[120px] bg-gray-800/50 border-gray-700 text-white resize-none pr-12"
            />
            <Button
              onClick={handleSubmit}
              disabled={!prompt.trim()}
              className="absolute bottom-3 right-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50"
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