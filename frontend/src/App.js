import React, { useState, useEffect } from 'react';
import './App.css';
import { Menu, X } from 'lucide-react';
import { Button } from './components/ui/button';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import PreviewPanel from './components/PreviewPanel';
import Settings from './components/Settings';
import { generateCode, saveProject, createSession, updateSession, getSession, validateVisual, generateDesign } from './services/api';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

function App() {
  const [messages, setMessages] = useState([]);
  const [generatedCode, setGeneratedCode] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentProject, setCurrentProject] = useState(null);
  const [selectedModel, setSelectedModel] = useState(
    localStorage.getItem('selectedModel') || 'anthropic/claude-3.5-sonnet'
  );
  const [totalCost, setTotalCost] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  
  // Visual Validator states
  const [visualValidatorEnabled, setVisualValidatorEnabled] = useState(
    localStorage.getItem('visualValidatorEnabled') === 'true'
  );
  const [visualValidatorModel, setVisualValidatorModel] = useState(
    localStorage.getItem('visualValidatorModel') || 'anthropic/claude-3-haiku'
  );

  // Session states
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessionName, setSessionName] = useState('New Session');
  const [isValidating, setIsValidating] = useState(false);
  const [validationFeedback, setValidationFeedback] = useState(null);
  const [originalUserRequest, setOriginalUserRequest] = useState('');
  const [awaitingDesignApproval, setAwaitingDesignApproval] = useState(false);
  const [proposedDesign, setProposedDesign] = useState(null);

  const handleSendPrompt = async (prompt) => {
    // Check if this is a design approval response
    if (awaitingDesignApproval) {
      const lowerPrompt = prompt.toLowerCase();
      if (lowerPrompt.includes('yes') || lowerPrompt.includes('да') || lowerPrompt.includes('approve') || lowerPrompt.includes('подтверждаю')) {
        // User approved design, proceed with code generation
        setAwaitingDesignApproval(false);
        await generateCodeWithDesign(originalUserRequest, proposedDesign);
        return;
      } else if (lowerPrompt.includes('no') || lowerPrompt.includes('нет') || lowerPrompt.includes('reject')) {
        // User rejected, ask for modifications
        setAwaitingDesignApproval(false);
        setProposedDesign(null);
        const rejectMessage = { role: 'assistant', content: 'Please describe what you\'d like to change in the design.' };
        setMessages(prev => [...prev, rejectMessage]);
        return;
      }
    }
    
    // Store original request
    if (!originalUserRequest && !awaitingDesignApproval) {
      setOriginalUserRequest(prompt);
    }
    
    const userMessage = { role: 'user', content: prompt };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    
    // Step 1: Generate design first (if validator enabled)
    if (visualValidatorEnabled && !awaitingDesignApproval) {
      setIsGenerating(true);
      try {
        const designMessage = { role: 'assistant', content: 'Generating design concept...' };
        setMessages(prev => [...prev, designMessage]);
        
        const designResult = await generateDesign(prompt, visualValidatorModel);
        
        setProposedDesign(designResult.design_spec);
        
        const designProposal = {
          role: 'design',
          content: `**Design Proposal:**\n\n${designResult.design_spec}\n\n---\n\n**Do you approve this design?** Reply with "yes" to proceed with code generation, or describe changes you'd like.`
        };
        
        setMessages(prev => [...prev.slice(0, -1), designProposal]);
        setAwaitingDesignApproval(true);
        setIsGenerating(false);
        
        toast({
          title: \"Design Ready\",\n          description: \"Review the design and approve to continue.\",\n        });\n        \n        return;\n        \n      } catch (error) {\n        console.error('Design generation error:', error);\n        toast({\n          title: \"Design Error\",\n          description: \"Proceeding with direct code generation.\",\n          variant: \"destructive\"\n        });\n        setIsGenerating(false);\n        // Fall through to normal code generation\n      }\n    }\n    \n    // Normal flow: direct code generation\n    await generateCodeDirectly(prompt, newMessages);\n  };\n\n  const generateCodeWithDesign = async (userRequest, designSpec) => {\n    setIsGenerating(true);\n    \n    try {\n      const enhancedPrompt = `${userRequest}\n\nDesign Specification:\n${designSpec}`;\n      \n      const response = await generateCode(enhancedPrompt, messages, selectedModel);\n      \n      const aiMessage = { \n        role: 'assistant', \n        content: response.message,\n        cost: response.cost \n      };\n      const updatedMessages = [...messages, aiMessage];\n      setMessages(updatedMessages);\n      \n      setGeneratedCode(response.code);\n      \n      let newTotalCost = totalCost;\n      if (response.cost) {\n        newTotalCost = totalCost + response.cost.total_cost;\n        setTotalCost(newTotalCost);\n      }\n\n      // Auto-save session\n      if (currentSessionId) {\n        await updateSession(currentSessionId, {\n          messages: updatedMessages,\n          generated_code: response.code,\n          model_used: selectedModel,\n          validator_model: visualValidatorModel,\n          validator_enabled: visualValidatorEnabled,\n          total_cost: newTotalCost\n        });\n      } else {\n        const session = await createSession({\n          name: userRequest.substring(0, 50) + (userRequest.length > 50 ? '...' : ''),\n          messages: updatedMessages,\n          generated_code: response.code,\n          model_used: selectedModel,\n          validator_model: visualValidatorModel,\n          validator_enabled: visualValidatorEnabled,\n          total_cost: newTotalCost\n        });\n        setCurrentSessionId(session.id);\n        setSessionName(session.name);\n      }\n\n      if (window.innerWidth < 768) {\n        setShowPreview(true);\n      }\n      \n      toast({\n        title: \"Code Generated!\",\n        description: visualValidatorEnabled ? \"Validating UI...\" : \"Your app is ready.\",\n      });\n      \n      // Run visual validation if enabled\n      if (visualValidatorEnabled && response.code) {\n        setTimeout(() => runVisualValidation(userRequest), 2000);\n      }\n      \n    } catch (error) {\n      console.error('Error generating code:', error);\n      const errorMessage = { \n        role: 'assistant', \n        content: `Error: ${error.response?.data?.detail || error.message}`\n      };\n      setMessages(prev => [...prev, errorMessage]);\n      \n      toast({\n        title: \"Error\",\n        description: \"Failed to generate code.\",\n        variant: \"destructive\"\n      });\n    } finally {\n      setIsGenerating(false);\n    }\n  };\n\n  const generateCodeDirectly = async (prompt, newMessages) => {\n    setIsGenerating(true);\n    \n    try {\n      const response = await generateCode(prompt, messages, selectedModel);\n      \n      const aiMessage = { \n        role: 'assistant', \n        content: response.message,\n        cost: response.cost \n      };\n      const updatedMessages = [...newMessages, aiMessage];\n      setMessages(updatedMessages);\n      \n      setGeneratedCode(response.code);\n      \n      let newTotalCost = totalCost;\n      if (response.cost) {\n        newTotalCost = totalCost + response.cost.total_cost;\n        setTotalCost(newTotalCost);\n      }\n\n      if (currentSessionId) {\n        await updateSession(currentSessionId, {\n          messages: updatedMessages,\n          generated_code: response.code,\n          model_used: selectedModel,\n          validator_model: visualValidatorModel,\n          validator_enabled: visualValidatorEnabled,\n          total_cost: newTotalCost\n        });\n      } else {\n        const session = await createSession({\n          name: prompt.substring(0, 50) + (prompt.length > 50 ? '...' : ''),\n          messages: updatedMessages,\n          generated_code: response.code,\n          model_used: selectedModel,\n          validator_model: visualValidatorModel,\n          validator_enabled: visualValidatorEnabled,\n          total_cost: newTotalCost\n        });\n        setCurrentSessionId(session.id);\n        setSessionName(session.name);\n      }\n\n      if (window.innerWidth < 768) {\n        setShowPreview(true);\n      }\n      \n      toast({\n        title: \"Code Generated!\",\n        description: \"Your app is ready.\",\n      });\n      \n    } catch (error) {\n      console.error('Error generating code:', error);\n      const errorMessage = { \n        role: 'assistant', \n        content: `Error: ${error.response?.data?.detail || error.message}`\n      };\n      setMessages(prev => [...prev, errorMessage]);\n      \n      toast({\n        title: \"Error\",\n        description: \"Failed to generate code.\",\n        variant: \"destructive\"\n      });\n    } finally {\n      setIsGenerating(false);\n    }\n  };

  const runVisualValidation = async (userRequest) => {
    if (!generatedCode) return;
    
    setIsValidating(true);
    
    try {
      // Capture screenshot of preview iframe
      const previewIframe = document.querySelector('iframe[title="Preview"]');
      if (!previewIframe) {
        throw new Error('Preview not ready');
      }
      
      // Use html2canvas or similar to capture
      // For now, we'll use a placeholder
      const screenshotBase64 = await capturePreviewScreenshot();
      
      // Send to validator
      const validationResult = await validateVisual(
        screenshotBase64,
        userRequest,
        visualValidatorModel
      );
      
      setValidationFeedback(validationResult);
      
      // Show validation result
      if (validationResult.verdict === 'APPROVED') {
        toast({
          title: "✅ UI Validated!",
          description: `Score: ${validationResult.overall_score}/10 - ${validationResult.feedback}`,
        });
      } else {
        toast({
          title: "⚠️ UI Needs Improvement",
          description: `Score: ${validationResult.overall_score}/10 - Check feedback`,
          variant: "destructive"
        });
        
        // Optionally auto-fix
        // await handleAutoFix(validationResult.fix_instructions);
      }
      
    } catch (error) {
      console.error('Validation error:', error);
      toast({
        title: "Validation Error",
        description: "Could not validate UI. Showing code anyway.",
        variant: "destructive"
      });
    } finally {
      setIsValidating(false);
    }
  };

  const capturePreviewScreenshot = async () => {
    // Simple implementation - return placeholder
    // In production, use html2canvas or similar
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";
  };

  const handleNewProject = () => {
    setMessages([]);
    setGeneratedCode('');
    setCurrentProject(null);
    setTotalCost(0);
    setShowPreview(false);
    setSidebarOpen(false);
    setCurrentSessionId(null);
    setSessionName('New Session');
  };

  const handleSessionSelect = async (session) => {
    try {
      const fullSession = await getSession(session.id);
      setMessages(fullSession.messages || []);
      setGeneratedCode(fullSession.generated_code || '');
      setTotalCost(fullSession.total_cost || 0);
      setCurrentSessionId(fullSession.id);
      setSessionName(fullSession.name);
      setSidebarOpen(false);
      
      toast({
        title: "Session Loaded",
        description: `Loaded "${fullSession.name}"`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load session.",
        variant: "destructive"
      });
    }
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
    setMessages(project.conversation_history || []);
    setGeneratedCode(project.code || '');
    setCurrentProject(project);
    setSidebarOpen(false);
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
      {/* Mobile Menu Button - Moved to RIGHT */}
      <Button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 right-4 z-50 md:hidden bg-gray-800 hover:bg-gray-700"
        size="sm"
      >
        {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
      </Button>

      {/* Sidebar - Hidden on mobile unless open */}
      <div className={`
        fixed md:relative inset-y-0 left-0 z-40
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        md:translate-x-0
      `}>
        <Sidebar 
          onNewProject={handleNewProject} 
          onProjectSelect={handleProjectSelect}
          onOpenSettings={handleOpenSettings}
          onSessionSelect={handleSessionSelect}
          currentSessionId={currentSessionId}
        />
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content - Mobile: Stack vertically, Desktop: Side by side */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Chat Interface - Hidden on mobile when preview is shown */}
        <div className={`
          ${showPreview ? 'hidden md:flex' : 'flex'} 
          flex-1 flex-col
        `}>
          <ChatInterface 
            onSendPrompt={handleSendPrompt} 
            messages={messages} 
            onSave={handleSaveProject}
            totalCost={totalCost}
            onOpenSettings={handleOpenSettings}
            activeModel={selectedModel}
            validatorEnabled={visualValidatorEnabled}
            validatorModel={visualValidatorModel}
          />
        </div>

        {/* Preview Panel - Full screen on mobile when shown */}
        <div className={`
          ${showPreview ? 'flex' : 'hidden md:flex'}
          flex-1 flex-col relative
        `}>
          {/* Mobile Back Button */}
          {showPreview && (
            <Button
              onClick={() => setShowPreview(false)}
              className="md:hidden absolute top-4 left-4 z-10 bg-gray-800 hover:bg-gray-700"
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