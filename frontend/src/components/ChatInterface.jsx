import React, { useState, useEffect } from 'react';
import { Send, ChevronDown, Save, Settings, Square, Paperclip, Mic, Plus, Upload, Check, Edit, List, Trash2, RotateCcw, Edit2 } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { samplePrompts } from '../mockData';
import StatusIndicator from './StatusIndicator';
import ModelIndicator from './ModelIndicator';
import TaskProgress from './TaskProgress';
import LoadingIndicator from './LoadingIndicator';
import { toast } from '../hooks/use-toast';
import { getSessions, getSession } from '../services/api';

const ChatInterface = ({ onSendPrompt, messages = [], onSave, totalCost, apiBalance, activeModel, validatorEnabled, validatorModel, generationStatus = 'idle', onOpenSettings, onNewProject, currentSessionId, isGenerating, onStopGeneration, chatMode = 'chat', onChatModeChange, developmentPlan = [], currentTaskIndex = 0, showApprovalButtons = false, onApprove, onRevise }) => {
  const [prompt, setPrompt] = useState('');
  const [showSamples, setShowSamples] = useState(true);
  const [showSettingsMenu, setShowSettingsMenu] = useState(false);
  const [sessionIdInput, setSessionIdInput] = useState('');
  const [showSessionMenu, setShowSessionMenu] = useState(false);
  const [allSessions, setAllSessions] = useState([]);
  const [loadingSessionId, setLoadingSessionId] = useState('');
  const [editingMessageIndex, setEditingMessageIndex] = useState(null);
  const [editedContent, setEditedContent] = useState('');

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

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      console.log('File uploaded:', file.name);
      toast({
        title: "File Upload",
        description: `File ${file.name} selected. Feature coming soon!`,
      });
      // TODO: Implement file upload logic
    }
  };

  const handleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      toast({
        title: "Not Supported",
        description: "Voice input is not supported in your browser.",
        variant: "destructive"
      });
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      toast({
        title: "Listening...",
        description: "Speak now",
      });
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setPrompt(transcript);
      toast({
        title: "Voice Input Captured",
        description: transcript,
      });
    };

    recognition.onerror = (event) => {
      toast({
        title: "Voice Input Error",
        description: event.error,
        variant: "destructive"
      });
    };

    recognition.start();
  };

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (showSettingsMenu && !e.target.closest('.settings-menu-container')) {
        setShowSettingsMenu(false);
      }
      if (showSessionMenu && !e.target.closest('.session-menu-container')) {
        setShowSessionMenu(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showSettingsMenu, showSessionMenu]);

  useEffect(() => {
    loadAllSessions();
  }, [currentSessionId]);

  const loadAllSessions = async () => {
    try {
      const sessions = await getSessions();
      setAllSessions(sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const handleLoadSessionById = async () => {
    if (!loadingSessionId.trim()) {
      toast({
        title: "Invalid ID",
        description: "Please enter a session ID.",
        variant: "destructive"
      });
      return;
    }

    try {
      const session = await getSession(loadingSessionId.trim());
      
      // Update app state through parent
      window.location.href = `/?session=${session.id}`;
      
      toast({
        title: "Session Loaded",
        description: `Loaded session: ${session.name}`,
      });
      
      setShowSessionMenu(false);
      setLoadingSessionId('');
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load session. Check the ID and try again.",
        variant: "destructive"
      });
    }
  };

  const handleSessionClick = async (sessionId) => {
    try {
      const session = await getSession(sessionId);
      
      // Reload page with session ID
      window.location.href = `/?session=${session.id}`;
      
      setShowSessionMenu(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load session.",
        variant: "destructive"
      });
    }
  };

  const handleDeleteMessage = (index) => {
    if (window.confirm('Delete this message?')) {
      // TODO: Implement message deletion
      toast({
        title: "Message Deleted",
        description: "Message has been removed.",
      });
    }
  };

  const handleEditMessage = (index, content) => {
    setEditingMessageIndex(index);
    setEditedContent(content);
  };

  const handleSaveEdit = () => {
    if (editingMessageIndex !== null) {
      // TODO: Implement message edit save
      toast({
        title: "Message Updated",
        description: "Message has been edited.",
      });
      setEditingMessageIndex(null);
      setEditedContent('');
    }
  };

  const handleCancelEdit = () => {
    setEditingMessageIndex(null);
    setEditedContent('');
  };

  const handleRegenerateFromPoint = (index) => {
    if (window.confirm('Regenerate from this point? All messages after this will be replaced.')) {
      // TODO: Implement regeneration logic
      toast({
        title: "Regenerating",
        description: "Generating response from this point...",
      });
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0f0f10] border-2 border-transparent animated-gradient-border">
      {/* Header */}
      <div className="border-b border-gray-800 p-3 md:p-4">
        <div className="flex items-center justify-between">
          {/* Session Info - Clickable */}
          <div className="relative session-menu-container">
            <button
              onClick={() => setShowSessionMenu(!showSessionMenu)}
              className="flex items-center gap-2 hover:bg-gray-800/50 rounded-lg px-3 py-2 transition-all group border border-transparent hover:border-gray-700"
            >
              <h2 className="text-white font-semibold text-sm">AI Assistant</h2>
              {currentSessionId && (
                <span className="text-xs text-gray-400 group-hover:text-gray-300 font-mono bg-gray-800/50 px-2 py-0.5 rounded border border-gray-700">
                  ID: {currentSessionId.slice(0, 8)}...
                </span>
              )}
              <List className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors" />
            </button>

            {/* Session Menu Dropdown */}
            {showSessionMenu && (
              <div className="absolute top-full left-0 mt-2 w-96 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50 max-h-96 overflow-hidden flex flex-col">
                {/* Load by ID */}
                <div className="p-3 border-b border-gray-800">
                  <p className="text-xs text-gray-400 mb-2">Load Session by ID</p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={loadingSessionId}
                      onChange={(e) => setLoadingSessionId(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleLoadSessionById();
                        }
                      }}
                      placeholder="Enter full session ID..."
                      className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
                    />
                    <Button
                      onClick={handleLoadSessionById}
                      size="sm"
                      className="bg-purple-600 hover:bg-purple-500 px-3 text-xs"
                    >
                      Load
                    </Button>
                  </div>
                </div>

                {/* All Sessions List */}
                <div className="flex-1 overflow-y-auto p-3">
                  <p className="text-xs text-gray-400 mb-2">All Sessions ({allSessions.length})</p>
                  {allSessions.length === 0 ? (
                    <p className="text-gray-600 text-xs text-center py-4">No sessions yet</p>
                  ) : (
                    <div className="space-y-2">
                      {allSessions.map((session) => (
                        <button
                          key={session.id}
                          onClick={() => handleSessionClick(session.id)}
                          className={`w-full text-left px-3 py-2 rounded text-xs transition-colors ${
                            currentSessionId === session.id
                              ? 'bg-purple-600/20 border border-purple-600'
                              : 'bg-gray-800/50 hover:bg-gray-800 border border-transparent'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <p className={`font-medium truncate ${
                                currentSessionId === session.id ? 'text-purple-400' : 'text-gray-300'
                              }`}>
                                {session.name || 'Untitled'}
                              </p>
                              <p className="text-gray-500 text-[10px] mt-0.5 font-mono">
                                ID: {session.id}
                              </p>
                              <div className="flex items-center gap-2 mt-1 text-gray-600 text-[10px]">
                                <span>{session.message_count || 0} msgs</span>
                                <span>•</span>
                                <span>${(session.total_cost || 0).toFixed(4)}</span>
                                <span>•</span>
                                <span>{session.last_updated || 'N/A'}</span>
                              </div>
                            </div>
                            {currentSessionId === session.id && (
                              <Check className="w-3 h-3 text-purple-400 flex-shrink-0" />
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* New Session Button */}
                <div className="p-3 border-t border-gray-800">
                  <Button
                    onClick={() => {
                      onNewProject();
                      setShowSessionMenu(false);
                    }}
                    className="w-full bg-green-600 hover:bg-green-500 text-white text-xs flex items-center justify-center gap-2"
                  >
                    <Plus className="w-3 h-3" />
                    New Session
                  </Button>
                </div>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-4">
            {/* Model Indicators + Settings Menu */}
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
              
              {/* Settings Dropdown Menu */}
              <div className="relative settings-menu-container">
                <button
                  onClick={() => setShowSettingsMenu(!showSettingsMenu)}
                  className="p-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700 hover:border-gray-600 transition-all"
                  title="Menu"
                >
                  <Settings className="w-4 h-4 text-gray-300 hover:text-white transition-colors" />
                </button>
                
                {showSettingsMenu && (
                  <div className="absolute top-full right-0 mt-2 w-64 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50 py-2">
                    <button
                      onClick={() => {
                        onOpenSettings();
                        setShowSettingsMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800 transition-colors flex items-center gap-2"
                    >
                      <Settings className="w-4 h-4" />
                      Settings
                    </button>
                    
                    <button
                      onClick={() => {
                        onNewProject();
                        setShowSettingsMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800 transition-colors flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      New Workspace
                    </button>
                    
                    <button
                      className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800 transition-colors flex items-center gap-2"
                    >
                      <Upload className="w-4 h-4" />
                      Repository
                    </button>
                    
                    <div className="border-t border-gray-700 my-2"></div>
                    
                    <div className="px-4 py-2">
                      <p className="text-xs text-gray-500 mb-2">Load Session by ID</p>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={sessionIdInput}
                          onChange={(e) => setSessionIdInput(e.target.value)}
                          placeholder="Session ID..."
                          className="flex-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
                        />
                        <Button
                          onClick={() => {
                            if (sessionIdInput.trim()) {
                              console.log('Load session:', sessionIdInput);
                              // TODO: Load session logic
                              setShowSettingsMenu(false);
                            }
                          }}
                          size="sm"
                          className="bg-purple-600 hover:bg-purple-500 px-2 text-xs"
                        >
                          Load
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            {/* Status & Save */}
            <div className="flex items-center gap-3">
              <StatusIndicator />
              
              {messages.length > 0 && (
                <button
                  onClick={onSave}
                  className="p-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700 hover:border-gray-600 transition-all group relative"
                  title="Save Project"
                >
                  <Save className="w-4 h-4 text-gray-300 group-hover:text-white transition-colors" />
                  <span className="absolute -bottom-8 right-0 bg-gray-900 text-gray-300 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none border border-gray-700">
                    Save as Project
                  </span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 md:p-6">
        <div className="max-w-3xl mx-auto">
          {/* Task Progress Panel */}
          {developmentPlan.length > 0 && chatMode === 'agent' && (
            <div className="mb-6">
              <TaskProgress 
                tasks={developmentPlan} 
                currentTaskIndex={currentTaskIndex} 
              />
              
              {/* Approval Buttons */}
              {showApprovalButtons && (
                <div className="mt-4 flex items-center justify-center gap-4">
                  <Button
                    onClick={onApprove}
                    className="bg-green-600 hover:bg-green-500 text-white px-6 py-2 flex items-center gap-2"
                  >
                    <Check className="w-4 h-4" />
                    Принять
                  </Button>
                  <Button
                    onClick={onRevise}
                    className="bg-orange-600 hover:bg-orange-500 text-white px-6 py-2 flex items-center gap-2"
                  >
                    <Edit className="w-4 h-4" />
                    Править
                  </Button>
                </div>
              )}
            </div>
          )}

          {messages.length === 0 ? (
            <div>
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
            <div className="space-y-4 md:space-y-5">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`group relative ${
                  msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'
                }`}
              >
                <div
                  className={`max-w-[85%] md:max-w-[75%] rounded-2xl p-4 shadow-xl transition-all duration-200 ${
                    msg.role === 'user'
                      ? 'bg-gray-700 backdrop-blur border-2 border-gray-500 hover:border-gray-400 rounded-br-sm'
                      : msg.role === 'design'
                      ? 'bg-purple-900/50 backdrop-blur border-2 border-purple-600 hover:border-purple-500 rounded-bl-sm'
                      : 'bg-gray-750 backdrop-blur border-2 border-gray-600 hover:border-gray-500 rounded-bl-sm'
                  }`}
                  style={{ backgroundColor: msg.role === 'user' ? 'rgba(55, 65, 81, 1)' : 'rgba(41, 50, 65, 1)' }}
                >
                  {/* Message Header */}
                  <div className="flex items-center justify-between mb-2">
                    <p className={`text-xs font-semibold ${
                      msg.role === 'user' ? 'text-gray-300' : 'text-gray-400'
                    }`}>
                      {msg.role === 'user' ? 'You' : msg.role === 'design' ? 'Design Proposal' : 'Assistant'}
                    </p>
                    
                    {/* Action Buttons */}
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleEditMessage(idx, msg.content)}
                        className="p-1.5 bg-gray-600/50 hover:bg-gray-500/70 rounded transition-colors"
                        title="Edit message"
                      >
                        <Edit2 className="w-3.5 h-3.5 text-gray-200" />
                      </button>
                      <button
                        onClick={() => handleRegenerateFromPoint(idx)}
                        className="p-1.5 bg-gray-600/50 hover:bg-gray-500/70 rounded transition-colors"
                        title="Regenerate from here"
                      >
                        <RotateCcw className="w-3.5 h-3.5 text-gray-200" />
                      </button>
                      <button
                        onClick={() => handleDeleteMessage(idx)}
                        className="p-1.5 bg-red-900/50 hover:bg-red-800/70 rounded transition-colors"
                        title="Delete message"
                      >
                        <Trash2 className="w-3.5 h-3.5 text-red-300" />
                      </button>
                    </div>
                  </div>

                  {/* Message Content */}
                  {editingMessageIndex === idx ? (
                    <div className="space-y-2">
                      <textarea
                        value={editedContent}
                        onChange={(e) => setEditedContent(e.target.value)}
                        className="w-full bg-gray-800 border-2 border-gray-600 rounded p-3 text-sm text-gray-100 resize-none focus:outline-none focus:border-gray-400"
                        rows={4}
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={handleSaveEdit}
                          className="px-4 py-1.5 bg-green-700 hover:bg-green-600 border-2 border-green-600 rounded text-xs font-semibold text-white shadow-lg"
                        >
                          Save
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 border-2 border-gray-600 rounded text-xs font-semibold text-gray-200"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm md:text-base text-gray-100 font-medium whitespace-pre-wrap leading-relaxed">
                        {msg.content}
                      </p>
                      {msg.image && (
                        <img src={msg.image} alt="Design" className="mt-3 rounded-lg max-w-full border-2 border-gray-600" />
                      )}
                    </>
                  )}

                  {/* Cost Info */}
                  {msg.cost && (
                    <div className="mt-2 pt-2 border-t border-gray-600">
                      <p className="text-[10px] text-gray-400 font-mono font-semibold">
                        ${msg.cost.total_cost.toFixed(6)} • {msg.cost.total_tokens} tokens
                        {apiBalance && apiBalance.remaining !== undefined && (
                          <span className="ml-2 text-[10px] text-green-400">
                            • Balance: ${apiBalance.remaining.toFixed(2)}
                          </span>
                        )}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isGenerating && (
              <div className="flex justify-start">
                <div className="bg-gray-750 backdrop-blur border-2 border-gray-600 rounded-2xl rounded-bl-sm p-4 shadow-xl" style={{ backgroundColor: 'rgba(41, 50, 65, 1)' }}>
                  <LoadingIndicator size="sm" />
                </div>
              </div>
            )}
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 p-3 md:p-6 bg-[#0f0f10] mt-auto">
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
              placeholder={chatMode === 'chat' ? 'Chat about your app idea...' : 'Describe your app...'}
              className={`min-h-[80px] md:min-h-[100px] bg-gray-900 text-sm md:text-base text-gray-300 resize-none pr-32 pl-3 pb-10 placeholder-gray-600 transition-all duration-300 ${
                generationStatus === 'generating' 
                  ? 'border-2 border-blue-400 shadow-lg shadow-blue-500/50' 
                  : generationStatus === 'success'
                  ? 'border-2 border-green-400 shadow-lg shadow-green-500/50'
                  : generationStatus === 'error'
                  ? 'border-2 border-red-400 shadow-lg shadow-red-500/50'
                  : 'border border-gray-700 focus:border-purple-500/50'
              }`}
            />
            
            {/* Bottom left controls */}
            <div className="absolute bottom-2 md:bottom-3 left-3 flex items-center gap-3">
              {/* Mode Toggle Switch - DISABLED during generation */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => !isGenerating && onChatModeChange(chatMode === 'chat' ? 'agent' : 'chat')}
                  disabled={isGenerating}
                  className={`relative w-12 h-5 rounded-full transition-all duration-300 ${
                    isGenerating ? 'opacity-50 cursor-not-allowed' : ''
                  } ${
                    chatMode === 'agent' 
                      ? 'bg-gray-700 border border-blue-500/50' 
                      : 'bg-gray-700 border border-gray-600'
                  }`}
                  title={isGenerating ? 'Cannot switch during generation' : chatMode === 'chat' ? 'Switch to Agent mode' : 'Switch to Chat mode'}
                >
                  <div
                    className={`absolute top-0.5 w-4 h-4 rounded-full transition-all duration-300 ${
                      chatMode === 'agent'
                        ? 'left-[26px] bg-blue-500 shadow-lg shadow-blue-500/50'
                        : 'left-0.5 bg-gray-500'
                    }`}
                  />
                </button>
                <span className="text-[10px] text-gray-500 font-medium">
                  {chatMode === 'chat' ? 'Chat' : 'Agent'}
                </span>
              </div>
              
              {/* File upload */}
              <label className="cursor-pointer text-gray-500 hover:text-gray-400 transition-colors">
                <input
                  type="file"
                  onChange={handleFileUpload}
                  className="hidden"
                  accept="*/*"
                />
                <Paperclip className="w-4 h-4" />
              </label>
              
              {/* Voice input */}
              <button
                onClick={handleVoiceInput}
                className="text-gray-500 hover:text-gray-400 transition-colors"
                title="Voice input"
              >
                <Mic className="w-4 h-4" />
              </button>
            </div>
            
            {/* Action buttons (right side) */}
            <div className="absolute bottom-2 md:bottom-3 right-2 md:right-3 flex items-center gap-2">
              
              {/* Send/Stop button */}
              {isGenerating ? (
                <Button
                  onClick={onStopGeneration}
                  className="bg-red-600 hover:bg-red-500 h-7 w-7 p-0"
                  size="sm"
                  title="Stop generation"
                >
                  <Square className="w-3.5 h-3.5" />
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={!prompt.trim()}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-30 h-7 w-7 p-0"
                  size="sm"
                  title="Send message"
                >
                  <Send className="w-3.5 h-3.5" />
                </Button>
              )}
            </div>
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