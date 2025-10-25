import React, { useState } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import PreviewPanel from './components/PreviewPanel';
import { mockGeneratedCode } from './mockData';

function App() {
  const [messages, setMessages] = useState([]);
  const [generatedCode, setGeneratedCode] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSendPrompt = async (prompt) => {
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: prompt }]);
    
    // Simulate AI generation
    setIsGenerating(true);
    
    // Simulate API delay
    setTimeout(() => {
      const aiResponse = `I'll create ${prompt.toLowerCase()} for you. Generating the code now...`;
      setMessages(prev => [...prev, { role: 'assistant', content: aiResponse }]);
      
      // Set mock code after a short delay
      setTimeout(() => {
        setGeneratedCode(mockGeneratedCode);
        setIsGenerating(false);
        
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: 'Your app is ready! Check the preview panel on the right. You can continue chatting to modify or enhance it.'
          }
        ]);
      }, 1500);
    }, 1000);
  };

  const handleNewProject = () => {
    setMessages([]);
    setGeneratedCode('');
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f0f10]">
      <Sidebar onNewProject={handleNewProject} />
      <ChatInterface onSendPrompt={handleSendPrompt} messages={messages} />
      <PreviewPanel generatedCode={generatedCode} isGenerating={isGenerating} />
    </div>
  );
}

export default App;