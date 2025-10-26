import React, { useState } from 'react';
import './App.css';
import { Menu, X } from 'lucide-react';
import { Button } from './components/ui/button';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import PreviewPanel from './components/PreviewPanel';
import Settings from './components/Settings';
import { generateCode, saveProject, createSession, updateSession, getSession } from './services/api';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

function App() {
  const [messages, setMessages] = useState([]);
  const [generatedCode, setGeneratedCode] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedModel, setSelectedModel] = useState(
    localStorage.getItem('selectedModel') || 'anthropic/claude-3.5-sonnet'
  );
  const [totalCost, setTotalCost] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  
  const [visualValidatorEnabled, setVisualValidatorEnabled] = useState(
    localStorage.getItem('visualValidatorEnabled') === 'true'
  );
  const [visualValidatorModel, setVisualValidatorModel] = useState(
    localStorage.getItem('visualValidatorModel') || 'google/gemini-2.0-flash-thinking-exp:free'
  );

  const [currentSessionId, setCurrentSessionId] = useState(null);

  const handleSendPrompt = async (prompt) => {
    const userMessage = { role: 'user', content: prompt };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    
    setIsGenerating(true);
    
    try {
      const response = await generateCode(prompt, messages, selectedModel);
      
      const aiMessage = { 
        role: 'assistant', 
        content: response.message,
        cost: response.cost 
      };
      const updatedMessages = [...newMessages, aiMessage];
      setMessages(updatedMessages);
      
      setGeneratedCode(response.code);
      
      let newTotalCost = totalCost;
      if (response.cost) {
        newTotalCost = totalCost + response.cost.total_cost;
        setTotalCost(newTotalCost);
      }

      if (currentSessionId) {
        await updateSession(currentSessionId, {
          messages: updatedMessages,
          generated_code: response.code,
          total_cost: newTotalCost
        });
      } else {
        const session = await createSession({
          name: prompt.substring(0, 50),
          messages: updatedMessages,
          generated_code: response.code,
          total_cost: newTotalCost
        });
        setCurrentSessionId(session.id);
      }

      if (window.innerWidth < 768) {
        setShowPreview(true);
      }
      
      toast({
        title: "Code Generated",
        description: "Your app is ready.",
      });
      
    } catch (error) {
      console.error('Error:', error);
      toast({
        title: "Error",
        description: "Failed to generate code.",
        variant: "destructive"
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleNewProject = () => {
    setMessages([]);
    setGeneratedCode('');
    setTotalCost(0);
    setShowPreview(false);
    setSidebarOpen(false);
    setCurrentSessionId(null);
  };

  const handleSaveProject = async () => {
    if (!generatedCode) {
      toast({
        title: "Nothing to save",
        description: "Generate code first.",
        variant: "destructive"
      });
      return;
    }

    try {
      await saveProject({
        name: 'Project ' + new Date().toLocaleDateString(),
        code: generatedCode,
        conversation_history: messages
      });
      
      toast({
        title: "Saved",
        description: "Project saved.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save.",
        variant: "destructive"
      });
    }
  };

  const handleSessionSelect = async (session) => {
    try {
      const fullSession = await getSession(session.id);
      setMessages(fullSession.messages || []);
      setGeneratedCode(fullSession.generated_code || '');
      setTotalCost(fullSession.total_cost || 0);
      setCurrentSessionId(fullSession.id);
      setSidebarOpen(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load session.",
        variant: "destructive"
      });
    }
  };

  const handleOpenSettings = () => {
    setShowSettings(true);
    setSidebarOpen(false);
  };

  if (showSettings) {
    return (
      <div className="flex h-screen overflow-hidden bg-[#0f0f10]">
        <Settings 
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          onClose={() => setShowSettings(false)}
          visualValidatorEnabled={visualValidatorEnabled}
          onVisualValidatorToggle={setVisualValidatorEnabled}
          visualValidatorModel={visualValidatorModel}
          onVisualValidatorModelChange={setVisualValidatorModel}
        />
        <Toaster />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f0f10]">
      <Button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 right-4 z-50 md:hidden bg-gray-800 hover:bg-gray-700"
        size="sm"
      >
        {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
      </Button>

      <div className={`
        fixed md:relative inset-y-0 left-0 z-40
        transform transition-transform duration-300
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        md:translate-x-0
      `}>
        <Sidebar 
          onNewProject={handleNewProject} 
          onOpenSettings={handleOpenSettings}
          onSessionSelect={handleSessionSelect}
          currentSessionId={currentSessionId}
        />
      </div>

      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        <div className={`${showPreview ? 'hidden md:flex' : 'flex'} flex-1`}>
          <ChatInterface 
            onSendPrompt={handleSendPrompt} 
            messages={messages} 
            onSave={handleSaveProject}
            totalCost={totalCost}
            activeModel={selectedModel}
            validatorEnabled={visualValidatorEnabled}
            validatorModel={visualValidatorModel}
          />
        </div>

        <div className={`${showPreview ? 'flex' : 'hidden md:flex'} flex-1 relative`}>
          {showPreview && (
            <Button
              onClick={() => setShowPreview(false)}
              className="md:hidden absolute top-4 left-4 z-10 bg-gray-800"
              size="sm"
            >
              <X className="w-4 h-4" />
            </Button>
          )}
          <PreviewPanel 
            generatedCode={generatedCode} 
            isGenerating={isGenerating} 
          />
        </div>
      </div>

      <Toaster />
    </div>
  );
}

export default App;
