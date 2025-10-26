import React, { useState, useEffect } from 'react';
import { Plus, Upload, MoreVertical, Settings, MessageSquare, Trash2, Search } from 'lucide-react';
import { Button } from './ui/button';
import { getSessions, deleteSession, getSession } from '../services/api';
import { toast } from '../hooks/use-toast';

const Sidebar = ({ onNewProject, onProjectSelect, onOpenSettings, onSessionSelect, currentSessionId }) => {
  const [projects, setProjects] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('sessions'); // 'sessions' or 'projects'
  const [showSessionMenu, setShowSessionMenu] = useState(false);
  const [sessionIdInput, setSessionIdInput] = useState('');

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    // Close session menu when clicking outside
    const handleClickOutside = (e) => {
      if (showSessionMenu && !e.target.closest('.session-menu-container')) {
        setShowSessionMenu(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showSessionMenu]);

  const loadSessions = async () => {
    try {
      const data = await getSessions();
      setSessions(data);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation();
    if (window.confirm('Delete this session?')) {
      try {
        await deleteSession(sessionId);
        setSessions(prev => prev.filter(s => s.id !== sessionId));
        toast({
          title: "Session Deleted",
          description: "Session has been removed.",
        });
      } catch (error) {
        toast({
          title: "Error",
          description: "Failed to delete session.",
          variant: "destructive"
        });
      }
    }
  };

  const handleLoadSessionById = async () => {
    if (!sessionIdInput.trim()) {
      toast({
        title: "Error",
        description: "Please enter a session ID.",
        variant: "destructive"
      });
      return;
    }

    try {
      const session = await getSession(sessionIdInput.trim());
      onSessionSelect(session);
      setShowSessionMenu(false);
      setSessionIdInput('');
      toast({
        title: "Session Loaded",
        description: "Session has been loaded successfully.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load session. Check the ID and try again.",
        variant: "destructive"
      });
    }
  };

  const handleNewWorkspace = () => {
    onNewProject();
    setShowSessionMenu(false);
  };

  return (
    <div className="w-80 bg-[#1a1a1b] border-r border-gray-800 flex flex-col h-screen">
      {/* Header */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 bg-gradient-to-br from-gray-700 to-gray-800 rounded-lg"></div>
          <span className="text-xl font-semibold text-gray-300">AI Studio</span>
        </div>
        
        <h1 className="text-2xl font-bold mb-2 text-gray-300">
          Hello, Developer
        </h1>
        <p className="text-gray-500 text-sm">Welcome back</p>
      </div>

      {/* Start Coding Section */}
      <div className="p-6 border-b border-gray-800">
        <h2 className="text-sm text-gray-400 mb-4">Start coding an app</h2>
        <div className="space-y-2">
          {/* New Workspace Button with Dropdown */}
          <div className="relative session-menu-container">
            <Button
              onClick={() => setShowSessionMenu(!showSessionMenu)}
              className="w-full justify-start gap-2 bg-gray-800 hover:bg-gray-700 text-white border-0"
            >
              <Plus className="w-4 h-4" />
              New Workspace
            </Button>
            
            {/* Session Menu Dropdown */}
            {showSessionMenu && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50 p-4 space-y-3">
                <button
                  onClick={handleNewWorkspace}
                  className="w-full px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Create New Session
                </button>
                
                <div className="border-t border-gray-700 pt-3">
                  <p className="text-xs text-gray-400 mb-2">Load Session by ID</p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={sessionIdInput}
                      onChange={(e) => setSessionIdInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleLoadSessionById();
                        }
                      }}
                      placeholder="Enter session ID..."
                      className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
                    />
                    <Button
                      onClick={handleLoadSessionById}
                      size="sm"
                      className="bg-blue-600 hover:bg-blue-500 px-3"
                    >
                      <Search className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                
                {sessions.length > 0 && (
                  <div className="border-t border-gray-700 pt-3">
                    <p className="text-xs text-gray-400 mb-2">Recent Sessions</p>
                    <div className="max-h-48 overflow-y-auto space-y-1">
                      {sessions.slice(0, 5).map((session) => (
                        <button
                          key={session.id}
                          onClick={() => {
                            onSessionSelect(session);
                            setShowSessionMenu(false);
                          }}
                          className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                            currentSessionId === session.id
                              ? 'bg-purple-600 text-white'
                              : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                          }`}
                        >
                          <div className="truncate">{session.name}</div>
                          <div className="text-xs text-gray-500 mt-0.5">
                            {session.message_count} msgs • {session.last_updated}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          
          <Button
            className="w-full justify-start gap-2 bg-gray-800 hover:bg-gray-700 text-white border-0"
          >
            <Upload className="w-4 h-4" />
            Import Repo
          </Button>
          <Button
            onClick={onOpenSettings}
            className="w-full justify-start gap-2 bg-gray-800 hover:bg-gray-700 text-white border-0"
          >
            <Settings className="w-4 h-4" />
            Settings
          </Button>
        </div>
      </div>

      {/* Workspaces Section */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          {/* Tabs */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setActiveTab('sessions')}
              className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'sessions'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              <MessageSquare className="w-4 h-4 inline mr-2" />
              Sessions
            </button>
          </div>

          {loading ? (
            <div className="text-center text-gray-500 py-8">
              Loading...
            </div>
          ) : activeTab === 'sessions' ? (
            sessions.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                No sessions yet. Start a new one!
              </div>
            ) : (
              <div className="space-y-2">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    onClick={() => onSessionSelect(session)}
                    className={`p-4 rounded-lg cursor-pointer transition-colors group ${
                      currentSessionId === session.id
                        ? 'bg-purple-600/20 border border-purple-500'
                        : 'bg-gray-800/50 hover:bg-gray-800'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-white font-medium mb-1">{session.name}</h3>
                        <p className="text-xs text-gray-400">
                          {session.message_count} messages • {session.last_updated}
                        </p>
                        {session.total_cost > 0 && (
                          <p className="text-xs text-green-400 mt-1 font-mono">
                            ${session.total_cost.toFixed(6)}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={(e) => handleDeleteSession(session.id, e)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;