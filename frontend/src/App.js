import React, { useState } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import PreviewPanel from './components/PreviewPanel';
import { generateCode, saveProject } from './services/api';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

function App() {
  const [messages, setMessages] = useState([]);
  const [generatedCode, setGeneratedCode] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentProject, setCurrentProject] = useState(null);

  const handleSendPrompt = async (prompt) => {
    // Add user message
    const userMessage = { role: 'user', content: prompt };
    setMessages(prev => [...prev, userMessage]);
    
    setIsGenerating(true);
    
    try {
      // Call the backend API
      const response = await generateCode(prompt, messages);
      
      // Add AI response
      const aiMessage = { role: 'assistant', content: response.message };
      setMessages(prev => [...prev, aiMessage]);
      
      // Set generated code
      setGeneratedCode(response.code);
      
      toast({
        title: "Code Generated!",
        description: "Your app is ready in the preview panel.",
      });
      
    } catch (error) {
      console.error('Error generating code:', error);
      const errorMessage = { 
        role: 'assistant', 
        content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message}. Please try again.`
      };
      setMessages(prev => [...prev, errorMessage]);
      
      toast({
        title: "Error",
        description: "Failed to generate code. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleNewProject = () => {
    setMessages([]);
    setGeneratedCode('');
    setCurrentProject(null);
  };

  const handleSaveProject = async () => {
    if (!generatedCode || messages.length === 0) {
      toast({
        title: "Nothing to save",
        description: "Generate some code first before saving.",
        variant: "destructive"
      });
      return;
    }

    try {
      const projectName = `Project ${new Date().toLocaleDateString()}`;
      const project = await saveProject({
        name: projectName,
        description: messages[0]?.content.substring(0, 50) || 'New project',
        code: generatedCode,
        conversation_history: messages
      });
      
      setCurrentProject(project);
      
      toast({
        title: "Project Saved!",
        description: `${projectName} has been saved successfully.`,
      });
    } catch (error) {
      console.error('Error saving project:', error);
      toast({
        title: "Error",
        description: "Failed to save project. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleProjectSelect = async (project) => {
    // Load project details
    setMessages(project.conversation_history || []);
    setGeneratedCode(project.code || '');
    setCurrentProject(project);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f0f10]">
      <Sidebar 
        onNewProject={handleNewProject} 
        onProjectSelect={handleProjectSelect}
      />
      <ChatInterface 
        onSendPrompt={handleSendPrompt} 
        messages={messages} 
        onSave={handleSaveProject}
      />
      <PreviewPanel 
        generatedCode={generatedCode} 
        isGenerating={isGenerating} 
      />
      <Toaster />
    </div>
  );
}

export default App;