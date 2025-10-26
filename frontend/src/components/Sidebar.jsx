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
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm text-gray-400">My workspaces</h2>
          </div>
          {loading ? (
            <div className="text-center text-gray-500 py-8">
              Loading projects...
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No projects yet. Create your first one!
            </div>
          ) : (
            <div className="space-y-2">
              {projects.map((project) => (
                <div
                  key={project.id}
                  onClick={() => onProjectSelect && onProjectSelect(project)}
                  className="p-4 bg-gray-800/50 hover:bg-gray-800 rounded-lg cursor-pointer transition-colors group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-2xl">{project.icon}</span>
                        <h3 className="text-white font-medium">{project.name}</h3>
                      </div>
                      <p className="text-sm text-gray-400">{project.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Accessed {project.last_accessed}
                      </p>
                    </div>
                    <button className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-white">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;