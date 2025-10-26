import React, { useState, useEffect } from 'react';
import { Plus, Upload, MoreVertical, Settings, MessageSquare, Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { getSessions, deleteSession } from '../services/api';
import { toast } from './hooks/use-toast';

const Sidebar = ({ onNewProject, onProjectSelect, onOpenSettings, onSessionSelect, currentSessionId }) => {
  const [projects, setProjects] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('sessions'); // 'sessions' or 'projects'

  useEffect(() => {
    loadSessions();
  }, []);

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

  return (
    <div className="w-80 bg-[#1a1a1b] border-r border-gray-800 flex flex-col h-screen">
      {/* Header */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 bg-gradient-to-br from-orange-500 to-pink-500 rounded-lg"></div>
          <span className="text-xl font-semibold text-white">Lovable Studio</span>
        </div>
        
        <h1 className="text-3xl font-bold mb-2">
          <span className="text-orange-400">Hello,</span>{' '}
          <span className="text-pink-400">Developer</span>
        </h1>
        <p className="text-gray-400 text-sm">Welcome back</p>
      </div>

      {/* Start Coding Section */}
      <div className="p-6 border-b border-gray-800">
        <h2 className="text-sm text-gray-400 mb-4">Start coding an app</h2>
        <div className="space-y-2">
          <Button
            onClick={onNewProject}
            className="w-full justify-start gap-2 bg-gray-800 hover:bg-gray-700 text-white border-0"
          >
            <Plus className="w-4 h-4" />
            New Workspace
          </Button>
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