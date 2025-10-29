import React, { useState, useEffect } from 'react';
import { Send, ChevronDown, Save, Settings, Square, Paperclip, Mic, Plus, Upload, Check, Edit, List, Trash2, RotateCcw, Edit2, Activity } from 'lucide-react';
import { Button } from './ui/button';
import ChimeraLogo from './ChimeraLogo';
import { Textarea } from './ui/textarea';
import { samplePrompts, platformFeatures } from '../mockData';
import StatusIndicator from './StatusIndicator';
import ModelIndicator from './ModelIndicator';
import TaskProgress from './TaskProgress';
import LoadingIndicator from './LoadingIndicator';
import { toast } from '../hooks/use-toast';
import { getSessions, getSession } from '../services/api';

const ChatInterface = ({ onSendPrompt, messages = [], onSave, totalCost, apiBalance, activeModel, chatModel, validatorEnabled, validatorModel, generationStatus = 'idle', onOpenSettings, onOpenAutomation, onOpenDocVerification, onOpenSelfImprovement, onOpenAIEntry, onOpenPreview, onNewProject, currentSessionId, isGenerating, onStopGeneration, chatMode = 'chat', onChatModeChange, developmentPlan = [], currentTaskIndex = 0, showApprovalButtons = false, onApprove, onRevise, onDeleteMessage, onEditMessage, onRegenerateFromMessage, onApproveDesign, onRequestDesignChanges, onAnnotateMockup }) => {
  const [showSamples, setShowSamples] = useState(true);
  const [expandedFeature, setExpandedFeature] = useState(null);
  const [showSettingsMenu, setShowSettingsMenu] = useState(false);
  const [sessionIdInput, setSessionIdInput] = useState('');
  const [showSessionMenu, setShowSessionMenu] = useState(false);
  const [allSessions, setAllSessions] = useState([]);
  const [loadingSessionId, setLoadingSessionId] = useState('');
  const [editingMessageIndex, setEditingMessageIndex] = useState(null);
  const [editedContent, setEditedContent] = useState('');
  
  // Automation mode определяется на основе chatMode
  const isAutomationMode = chatMode === 'automation';
  const [prompt, setPrompt] = useState('');
  
  // Personalization: User and AI names
  const [userName, setUserName] = useState(localStorage.getItem('chimera_user_name') || null);
  const [aiName] = useState(localStorage.getItem('chimera_ai_name') || 'Aria'); // AI chooses her name
  const [showNamePrompt, setShowNamePrompt] = useState(!userName && messages.length === 0);

  // Content folder state
  const [showContent, setShowContent] = useState(false);
  const [sessionContent, setSessionContent] = useState([]);
  const [showFunctionsMenu, setShowFunctionsMenu] = useState(false);

  // AI Introduction on first launch
  useEffect(() => {
    if (!userName && messages.length === 0) {
      // AI introduces herself
      const introMessage = {
        role: 'assistant',
        content: `Hello! I'm ${aiName}, your AI companion for creating amazing applications. 🎨✨\n\nI can help you build full-stack apps, automate browser tasks, verify documents, and much more!\n\nWhat should I call you? Feel free to share your name, or we can dive right into creating something awesome together!`
      };
      // Add intro message (would need to update messages in parent, but for now just show prompt)
      setShowNamePrompt(true);
    }
  }, []);

  const handleSubmit = async () => {
    if (!prompt.trim()) return;
    
    if (isAutomationMode) {
      // Automation Mode: отправляем в automation brain
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/hook/automation-chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: prompt })
        });
        const data = await response.json();
        
        // Добавляем сообщения в чат как обычно
        onSendPrompt(prompt); // User message
        // TODO: показать ответ от automation brain через messages
        
        toast({
          title: "Automation Brain",
          description: data.reply || "Message sent"
        });
      } catch (e) {
        toast({
          title: "Error",
          description: "Failed to send message to automation brain",
          variant: "destructive"
        });
      }
    } else {
      // Normal Mode: обычный чат
      onSendPrompt(prompt);
    }
    
    setPrompt('');
    setShowSamples(false);
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
      if (showFunctionsMenu && !e.target.closest('.functions-menu-container')) {
        setShowFunctionsMenu(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showSettingsMenu, showSessionMenu, showFunctionsMenu]);

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
    if (window.confirm('Delete this message and all messages after it? This will reset the conversation to this point.')) {
      if (onDeleteMessage) {
        onDeleteMessage(index);
        toast({
          title: "Messages Deleted",
          description: `Message and all following messages removed. Context reset.`,
        });
      }
    }
  };

  const handleEditMessage = (index, content) => {
    setEditingMessageIndex(index);
    setEditedContent(content);
  };

  const handleSaveEdit = () => {
    if (editingMessageIndex !== null && editedContent.trim()) {
      if (onEditMessage) {
        onEditMessage(editingMessageIndex, editedContent);
        toast({
          title: "Message Updated",
          description: "Message has been edited successfully.",
        });
      }
      setEditingMessageIndex(null);
      setEditedContent('');
    }
  };

  const handleCancelEdit = () => {
    setEditingMessageIndex(null);
    setEditedContent('');
  };

  const handleRegenerateFromPoint = (index) => {
    if (window.confirm('Regenerate response from this point? This will replace all messages after this one.')) {
      if (onRegenerateFromMessage) {
        onRegenerateFromMessage(index);
        toast({
          title: "Regenerating",
          description: "Generating new response from this point...",
        });
      }
    }
  };

  return (
    <div className={`flex flex-col h-full bg-[#0f0f10] border-2 border-transparent relative ${
      isAutomationMode 
        ? 'animated-gradient-border-green' 
        : chatMode === 'agent' 
          ? 'animated-gradient-border-purple'
          : 'animated-gradient-border'
    }`}>
      {/* Header - redesigned */}
      <div className="flex-shrink-0 border-b border-gray-800 p-3 md:p-4">
        <div className="flex items-start justify-between">
          {/* Left: 3 Mode Squares (smaller) */}
          <div className="flex items-center gap-2">
            {/* Chat Mode - Blue Square */}
            <button
              onClick={() => {
                setIsAutomationMode(false);
                if (onChatModeChange) onChatModeChange('chat');
              }}
              className={`w-4 h-4 rounded transition-all relative group ${
                !isAutomationMode && chatMode === 'chat'
                  ? 'bg-gradient-to-br from-blue-400 to-blue-600 shadow-lg shadow-blue-500/50 ring-2 ring-blue-400/40'
                  : 'bg-blue-900/40 hover:bg-blue-800/60 border border-blue-700/60 hover:scale-105'
              }`}
              title="Chat Mode"
            >
              <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 bg-gray-900 text-gray-300 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none border border-gray-700 z-10">
                Chat
              </span>
            </button>
            
            {/* Code Mode - Purple Square */}
            <button
              onClick={() => {
                setIsAutomationMode(false);
                if (onChatModeChange) onChatModeChange('agent');
              }}
              className={`w-4 h-4 rounded transition-all relative group ${
                !isAutomationMode && chatMode === 'agent'
                  ? 'bg-gradient-to-br from-purple-400 to-purple-600 shadow-lg shadow-purple-500/50 ring-2 ring-purple-400/40'
                  : 'bg-purple-900/40 hover:bg-purple-800/60 border border-purple-700/60 hover:scale-105'
              }`}
              title="Code Mode"
            >
              <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 bg-gray-900 text-gray-300 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none border border-gray-700 z-10">
                Code
              </span>
            </button>
            
            {/* Automation Mode - Green Square */}
            <button
              onClick={() => {
                setIsAutomationMode(true);
                // НЕ переключаем сразу на вкладку, только меняем режим
                // Вкладка откроется через Preview
              }}
              className={`w-4 h-4 rounded transition-all relative group ${
                isAutomationMode
                  ? 'bg-gradient-to-br from-green-400 to-green-600 shadow-lg shadow-green-500/50 ring-2 ring-green-400/40'
                  : 'bg-green-900/40 hover:bg-green-800/60 border border-green-700/60 hover:scale-105'
              }`}
              title="Automation Mode"
            >
              <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 bg-gray-900 text-gray-300 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none border border-gray-700 z-10">
                Automation
              </span>
            </button>
          </div>
          
          {/* Center: ChimeraLogo (larger) */}
          <div className="absolute left-1/2 -translate-x-1/2 top-3">
            <ChimeraLogo className="h-7" />
          </div>
          
          {/* Right: Icons + Session ID */}
          <div className="flex flex-col items-end gap-2">
            {/* Top row: 3 Icons БЕЗ квадратов */}
            <div className="flex items-center gap-2">
              {/* Preview Eye - просто иконка */}
              <button
                onClick={() => {
                  if (isAutomationMode) {
                    if (onOpenAutomation) onOpenAutomation();
                  } else if (chatMode === 'agent') {
                    if (onOpenPreview) onOpenPreview();
                  } else {
                    toast({
                      title: "Artifacts",
                      description: "Artifacts preview (TODO: implement)"
                    });
                  }
                }}
                className="hover:opacity-70 transition-opacity"
                title={
                  isAutomationMode 
                    ? "Open Browser Automation" 
                    : chatMode === 'agent' 
                      ? "Preview Code" 
                      : "Preview Artifacts"
                }
              >
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
              
              {/* Code Icon - просто иконка */}
              <button className="hover:opacity-70 transition-opacity">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
              </button>
              
              {/* Settings Icon - просто иконка */}
              <button
                onClick={() => setShowSettingsMenu(!showSettingsMenu)}
                className="hover:opacity-70 transition-opacity relative"
                title="Settings"
              >
                <Settings className="w-4 h-4 text-gray-400" />
                
                {/* Settings Dropdown Menu */}
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
                        if (onOpenSelfImprovement) {
                          onOpenSelfImprovement();
                          setShowSettingsMenu(false);
                        }
                      }}
                      className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800 transition-colors flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      Self-Improvement
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
              </button>
            </div>
            
            {/* Bottom row: Session ID - editable yellow */}
            {currentSessionId && (
              <input
                type="text"
                value={currentSessionId}
                readOnly
                onClick={(e) => e.target.select()}
                className="text-[9px] text-yellow-500 font-mono bg-transparent px-1 rounded cursor-pointer hover:bg-gray-800/30 transition-colors w-24"
                title="Click to select session ID"
              />
            )}
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
                <h1 className="text-3xl md:text-5xl font-bold mb-2 md:mb-4">
                  <span className="inline-block animate-gradient-text bg-gradient-to-r from-purple-400 via-blue-400 to-purple-400 bg-clip-text text-transparent bg-[length:200%_100%]">
                    Chimera AI
                  </span>
                </h1>
                <p className="text-sm md:text-base text-gray-400">
                  Describe your app and watch it come to life
                </p>
              </div>
              
              <style jsx>{`
                @keyframes gradient-text {
                  0%, 100% { background-position: 0% 50%; }
                  50% { background-position: 100% 50%; }
                }
                
                .animate-gradient-text {
                  animation: gradient-text 3s ease infinite;
                }
              `}</style>

            {showSamples && (
              <div className="space-y-2 mb-8">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-gray-400 font-medium">Platform Capabilities</span>
                  <button
                    onClick={() => setShowSamples(!showSamples)}
                    className="text-gray-500 hover:text-gray-400 transition-colors"
                  >
                    <ChevronDown className="w-4 h-4" />
                  </button>
                </div>
                
                {/* Feature Cards - minimal transparent */}
                {platformFeatures.map((feature) => (
                  <div
                    key={feature.id}
                    className="bg-gray-900/20 backdrop-blur-sm border border-gray-800/30 hover:border-gray-700/50 rounded-lg transition-all overflow-hidden"
                  >
                    <button
                      onClick={() => setExpandedFeature(expandedFeature === feature.id ? null : feature.id)}
                      className="w-full p-3 text-left flex items-start justify-between gap-3"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <h3 className="text-sm font-medium text-gray-200">{feature.title}</h3>
                          <span className="px-1.5 py-0.5 bg-gray-700/30 text-gray-400 text-[10px] rounded border border-gray-700/30">
                            {feature.category}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 line-clamp-1">{feature.description}</p>
                      </div>
                      <ChevronDown 
                        className={`w-4 h-4 text-gray-500 flex-shrink-0 transition-transform ${
                          expandedFeature === feature.id ? 'rotate-180' : ''
                        }`}
                      />
                    </button>
                    
                    {/* Expanded Content */}
                    {expandedFeature === feature.id && (
                      <div className="px-4 pb-4 space-y-3 border-t border-gray-800">
                        <div className="pt-3">
                          <p className="text-xs font-semibold text-gray-400 mb-2">📝 What it does:</p>
                          <p className="text-sm text-gray-300 leading-relaxed">{feature.description}</p>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-gray-400 mb-2">⚙️ How it works:</p>
                          <p className="text-sm text-gray-300 leading-relaxed">{feature.howItWorks}</p>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                
                {/* Quick Start Examples */}
                <div className="mt-6 pt-4 border-t border-gray-800">
                  <span className="text-xs text-gray-500 mb-3 block">💡 Quick Start Examples:</span>
                  <div className="grid grid-cols-1 gap-2">
                    {samplePrompts.map((sample, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSampleClick(sample)}
                        className="p-3 bg-gray-900/30 hover:bg-gray-800/50 rounded-lg text-left text-sm text-gray-400 hover:text-gray-300 transition-colors border border-gray-800/50 hover:border-blue-500/30"
                      >
                        {sample}
                      </button>
                    ))}
                  </div>
                </div>
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
                  className={`max-w-[85%] md:max-w-[75%] rounded-2xl p-4 shadow-2xl transition-all duration-300 backdrop-blur-lg ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-br from-blue-600/20 to-purple-600/20 border border-blue-500/30 hover:border-blue-400/50 rounded-br-sm hover:shadow-blue-500/20'
                      : msg.role === 'design'
                      ? 'bg-gradient-to-br from-purple-600/20 to-pink-600/20 border border-purple-500/30 hover:border-purple-400/50 rounded-bl-sm hover:shadow-purple-500/20'
                      : msg.role === 'system'
                      ? 'bg-gradient-to-br from-cyan-600/15 to-blue-600/15 border border-cyan-500/25 rounded-lg'
                      : 'bg-gradient-to-br from-gray-800/40 to-gray-900/40 border border-gray-700/40 hover:border-gray-600/50 rounded-bl-sm hover:shadow-gray-500/10'
                  }`}
                >
                  {/* Message Header */}
                  <div className="flex items-center justify-between mb-2">
                    <p className={`text-xs font-semibold flex items-center gap-2 ${
                      msg.role === 'user' ? 'text-blue-300' : msg.role === 'system' ? 'text-cyan-300' : 'text-purple-300'
                    }`}>
                      {msg.role === 'user' ? (
                        <>
                          <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                          {userName || 'You'}
                        </>
                      ) : msg.role === 'design' ? (
                        <>
                          <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                          {aiName} • Design
                        </>
                      ) : msg.role === 'system' ? (
                        <>
                          <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                          System
                        </>
                      ) : (
                        <>
                          <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                          {aiName}
                        </>
                      )}
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
                      {msg.type === 'mockup' && msg.image && (
                        <div className="mt-3 flex items-center gap-2">
                          <button
                            onClick={() => {
                              if (window.onAnnotateMockup) window.onAnnotateMockup(msg.image);
                            }}
                            className="px-3 py-1.5 text-xs bg-purple-700/30 hover:bg-purple-700/50 border border-purple-600/40 rounded text-purple-200"
                          >
                            Annotate
                          </button>
                          <button
                            onClick={() => {
                              if (window.onApproveDesign) window.onApproveDesign();
                            }}
                            className="px-3 py-1.5 text-xs bg-green-700/30 hover:bg-green-700/50 border border-green-600/40 rounded text-green-200"
                          >
                            Approve Design
                          </button>
                        </div>
                      )}

                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm md:text-base text-gray-100 font-medium whitespace-pre-wrap leading-relaxed">
                        {msg.content}
                      </p>
                      {msg.image && (
                        <>
                          {/* Check if image is a valid URL/data URI or just text */}
                          {(msg.image.startsWith('http') || msg.image.startsWith('data:image') || msg.image.startsWith('blob:')) ? (
                            <img 
                              src={msg.image} 
                              alt="Design Mockup" 
                              className="mt-3 rounded-lg max-w-full border-2 border-gray-600" 
                              onError={(e) => {
                                // If image fails to load, hide it and show text instead
                                e.target.style.display = 'none';
                                const textDiv = document.createElement('div');
                                textDiv.className = 'mt-3 p-4 bg-gray-800/50 rounded-lg border border-gray-700 text-sm text-gray-300';
                                textDiv.textContent = msg.image;
                                e.target.parentNode.appendChild(textDiv);
                              }}
                            />
                          ) : (
                            // If it's not a URL, display as formatted text (mockup description)
                            <div className="mt-3 p-4 bg-purple-900/20 rounded-lg border border-purple-700/30">
                              <p className="text-xs font-semibold text-purple-300 mb-2">🎨 Design Mockup Description:</p>
                              <p className="text-sm text-gray-300 whitespace-pre-wrap">{msg.image}</p>
                            </div>
                          )}
                          
                          {/* Approval buttons for mockup messages */}
                          {msg.type === 'mockup' && (
                            <div className="mt-3 flex items-center gap-2">
                              <button
                                onClick={() => {
                                  if (window.onAnnotateMockup) window.onAnnotateMockup(msg.image);
                                }}
                                className="px-3 py-1.5 text-xs bg-purple-700/30 hover:bg-purple-700/50 border border-purple-600/40 rounded text-purple-200 transition-colors"
                              >
                                ✏️ Annotate
                              </button>
                              <button
                                onClick={() => {
                                  if (window.onApproveDesign) window.onApproveDesign();
                                }}
                                className="px-3 py-1.5 text-xs bg-green-700/30 hover:bg-green-700/50 border border-green-600/40 rounded text-green-200 transition-colors"
                              >
                                ✅ Approve Design
                              </button>
                            </div>
                          )}
                        </>
                      )}
                    </>
                  )}

                  {/* Cost Info */}
                  {msg.cost && (
                    <div className="mt-2 pt-2 border-t border-gray-600">
                      <p className="text-[10px] text-gray-400 font-mono font-semibold">
                        ${msg.cost.total_cost?.toFixed(6) || '0.000000'} • {msg.cost.total_tokens || 0} tokens
                        {apiBalance && apiBalance.remaining !== undefined && (
                          <span className="ml-2 text-[10px] text-green-400">
                            • Balance: ${apiBalance.remaining.toFixed(2)}
                          </span>
                        )}
                        {msg.context_info && msg.context_info.percentage_display && (
                          <span className="ml-2 text-[10px] text-blue-400">
                            • Context: {msg.context_info.percentage_display}
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

      {/* Input - fixed at bottom, adapts to keyboard */}
      <div className="flex-shrink-0 border-t border-gray-800 p-2 md:p-6 bg-[#0f0f10]">
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
              {/* Triple mode toggle: Chat | Code | Automation */}
              <div className="flex items-center gap-2 bg-gray-800/50 rounded-full p-1">
                <button
                  onClick={() => !isGenerating && onChatModeChange('chat')}
                  disabled={isGenerating}
                  className={`px-3 py-1 rounded-full text-[10px] font-medium transition-all ${
                    chatMode === 'chat'
                      ? 'bg-purple-600 text-white shadow-lg'
                      : 'text-gray-500 hover:text-gray-300'
                  } ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
                  title="Chat mode"
                >
                  💬 Chat
                </button>
                <button
                  onClick={() => !isGenerating && onChatModeChange('agent')}
                  disabled={isGenerating}
                  className={`px-3 py-1 rounded-full text-[10px] font-medium transition-all ${
                    chatMode === 'agent'
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-gray-500 hover:text-gray-300'
                  } ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
                  title="Code generation mode"
                >
                  🤖 Code
                </button>
                <button
                  onClick={() => !isGenerating && onChatModeChange('automation')}
                  disabled={isGenerating}
                  className={`px-3 py-1 rounded-full text-[10px] font-medium transition-all ${
                    chatMode === 'automation'
                      ? 'bg-green-600 text-white shadow-lg'
                      : 'text-gray-500 hover:text-gray-300'
                  } ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
                  title="Browser automation mode"
                >
                  🌐 Auto
                </button>
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

      {/* Content Panel - Slide-in from right */}
      {showContent && (
        <div className="fixed inset-y-0 right-0 w-80 bg-gray-900/95 backdrop-blur-lg border-l border-gray-700 shadow-2xl z-50 flex flex-col">
          {/* Content Header */}
          <div className="p-4 border-b border-gray-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              <h3 className="text-white font-semibold">Session Content</h3>
            </div>
            <button
              onClick={() => setShowContent(false)}
              className="p-1 hover:bg-gray-800 rounded transition-colors"
            >
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content List */}
          <div className="flex-1 overflow-y-auto p-4">
            {sessionContent.length === 0 ? (
              <div className="text-center py-12">
                <svg className="w-16 h-16 text-gray-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                <p className="text-gray-400 text-sm">No content yet</p>
                <p className="text-gray-500 text-xs mt-1">Generated images, code, and files will appear here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {sessionContent.map((item, idx) => (
                  <div key={idx} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700 hover:border-amber-500/50 transition-colors">
                    <div className="flex items-start gap-3">
                      {item.type === 'image' ? (
                        <svg className="w-5 h-5 text-purple-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      ) : item.type === 'code' ? (
                        <svg className="w-5 h-5 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-white text-sm font-medium truncate">{item.name}</p>
                        <p className="text-gray-500 text-xs mt-0.5">{item.timestamp}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Add CSS for animated gradient border and mobile fixes */}
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
        
        .animated-gradient-border-purple {
          position: relative;
          border: 2px solid transparent;
          background: linear-gradient(#0f0f10, #0f0f10) padding-box,
                      linear-gradient(90deg, 
                        rgba(139, 92, 246, 0.5),
                        rgba(168, 85, 247, 0.5),
                        rgba(192, 132, 252, 0.5),
                        rgba(168, 85, 247, 0.5),
                        rgba(139, 92, 246, 0.5)
                      ) border-box;
          background-size: 200% 100%;
          animation: gradientShift 3s ease infinite;
        }
        
        .animated-gradient-border-green {
          position: relative;
          border: 2px solid transparent;
          background: linear-gradient(#0f0f10, #0f0f10) padding-box,
                      linear-gradient(90deg, 
                        rgba(16, 185, 129, 0.5),
                        rgba(52, 211, 153, 0.5),
                        rgba(110, 231, 183, 0.5),
                        rgba(52, 211, 153, 0.5),
                        rgba(16, 185, 129, 0.5)
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
        
        /* Mobile viewport fixes */
        @media (max-width: 768px) {
          .animated-gradient-border,
          .animated-gradient-border-purple,
          .animated-gradient-border-green {
            height: 100vh;
            height: 100dvh; /* Dynamic viewport height for mobile browsers */
            max-height: 100vh;
            max-height: 100dvh;
            overflow: hidden;
          }
        }
      `}</style>
    </div>
  );
};

export default ChatInterface;