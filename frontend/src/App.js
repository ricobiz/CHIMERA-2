import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { Menu, X } from 'lucide-react';
import { Button } from './components/ui/button';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import PreviewPanel from './components/PreviewPanel';
import Settings from './components/Settings';
import AutomationPage from './components/automation/AutomationPage.tsx';
import DocumentVerification from './components/DocumentVerification';
import SelfImprovement from './components/SelfImprovement';
import AIEntryPoint from './components/AIEntryPoint';
import TaskProgress from './components/TaskProgress';
import { generateCode, saveProject, createSession, updateSession, getSession, getOpenRouterBalance, generateDesign, generateMockup, classifyTask } from './services/api';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';
import AnnotatorModal from './components/AnnotatorModal.jsx';

function App() {
  const [messages, setMessages] = useState([]);
  const [generatedCode, setGeneratedCode] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  // Separate models: code vs chat
  const [selectedModel, setSelectedModel] = useState(
    localStorage.getItem('selectedModel') || 'x-ai/grok-code-fast-1'  // Code Generation: Grok Code Fast 1 by default
  );
  const [chatModel, setChatModel] = useState(
    localStorage.getItem('chatModel') || 'openai/gpt-5' // Chat: GPT-5 by default via OpenRouter
  );
  const [totalCost, setTotalCost] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showAutomation, setShowAutomation] = useState(false);
  const [showDocVerification, setShowDocVerification] = useState(false);
  const [showSelfImprovement, setShowSelfImprovement] = useState(false);
  const [showAIEntry, setShowAIEntry] = useState(false);
  const [apiBalance, setApiBalance] = useState(null); // OpenRouter balance
  
  const [visualValidatorEnabled, setVisualValidatorEnabled] = useState(
    localStorage.getItem('visualValidatorEnabled') !== 'false'  // Enabled by default
  );
  const [visualValidatorModel, setVisualValidatorModel] = useState(
    localStorage.getItem('visualValidatorModel') || 'google/gemini-2.5-flash-image-preview'  // Nano Banana for design
  );
  
  const [researchPlannerEnabled, setResearchPlannerEnabled] = useState(
    localStorage.getItem('researchPlannerEnabled') !== 'false'  // Enabled by default
  );
  const [researchPlannerModel, setResearchPlannerModel] = useState(
    localStorage.getItem('researchPlannerModel') || 'openai/gpt-5'  // GPT-5 for planning
  );

  const [currentSessionId, setCurrentSessionId] = useState(
    localStorage.getItem('currentSessionId') || null
  );
  const [generationStatus, setGenerationStatus] = useState('idle'); // 'idle', 'generating', 'success', 'error'
  const [chatMode, setChatMode] = useState(
    localStorage.getItem('chatMode') || 'chat'
  ); // 'chat' or 'agent'
  
  // Design approval workflow
  // Design mockup annotator
  const [showAnnotator, setShowAnnotator] = useState(false);
  const [annotateImageUrl, setAnnotateImageUrl] = useState(null);

  const [pendingDesign, setPendingDesign] = useState(null);
  const [pendingPrompt, setPendingPrompt] = useState('');
  const [awaitingDesignApproval, setAwaitingDesignApproval] = useState(false);
  
  // Refs to store interval IDs for proper cleanup
  const revisionIntervalRef = useRef(null);
  const progressIntervalRef = useRef(null);
  const balanceIntervalRef = useRef(null);
  
  // Load current session on mount
  useEffect(() => {
    const loadCurrentSession = async () => {
      // Check URL for session parameter
      const urlParams = new URLSearchParams(window.location.search);
      const urlSessionId = urlParams.get('session');
      
      let sessionId = urlSessionId || localStorage.getItem('currentSessionId');
      
      if (sessionId) {
        try {
          // Try to load from localStorage first (faster)
          const cachedMessages = localStorage.getItem(`session_${sessionId}_messages`);
          if (cachedMessages) {
            try {
              const parsedMessages = JSON.parse(cachedMessages);
              setMessages(parsedMessages);
              console.log(`✅ Loaded ${parsedMessages.length} messages from cache`);
            } catch (e) {
              console.error('Failed to parse cached messages:', e);
            }
          }
          
          // Then try to load from server (will override cache if available)
          const session = await getSession(sessionId);
          setMessages(session.messages || []);
          setGeneratedCode(session.generated_code || '');
          setTotalCost(session.total_cost || 0);
          setCurrentSessionId(sessionId);
          
          // Clear URL parameter after loading
          if (urlSessionId) {
            window.history.replaceState({}, '', '/');
          }
        } catch (error) {
          console.error('Failed to load session:', error);
          localStorage.removeItem('currentSessionId');
          // Create new session if loading failed
          sessionId = null;
        }
      }
      
      // If no session exists, create a new one
      if (!sessionId) {
        try {
          // Create session in database
          const newSession = await createSession({
            name: "New Session",
            messages: [],
            generated_code: "",
            total_cost: 0.0
          });
          setCurrentSessionId(newSession.id);
          console.log(`🆕 Created new session: ${newSession.id}`);
        } catch (error) {
          console.error('Failed to create session:', error);
          // Fallback to local ID if API fails
          const fallbackId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
          setCurrentSessionId(fallbackId);
          console.log(`⚠️ Using fallback session ID: ${fallbackId}`);
        }
      }
    };
    
    loadCurrentSession();
  }, []);
  
  // Save session ID to localStorage when it changes
  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem('currentSessionId', currentSessionId);
    } else {
      localStorage.removeItem('currentSessionId');
    }
  }, [currentSessionId]);
  
  // Save chat mode to localStorage
  useEffect(() => {
    localStorage.setItem('chatMode', chatMode);
  }, [chatMode]);
  
  // Auto-save messages to localStorage
  useEffect(() => {
    if (messages.length > 0) {
      const sessionKey = currentSessionId || 'default_session';
      localStorage.setItem(`session_${sessionKey}_messages`, JSON.stringify(messages));
      console.log(`💾 Auto-saved ${messages.length} messages for ${sessionKey}`);
    }
  }, [messages, currentSessionId]);
  
  // Load OpenRouter balance
  useEffect(() => {
    const loadBalance = async () => {
      try {
        const balance = await getOpenRouterBalance();
        setApiBalance(balance);
      } catch (error) {
        console.error('Failed to load API balance:', error);
      }
    };
    loadBalance();
    // Refresh balance every 30 seconds
    balanceIntervalRef.current = setInterval(loadBalance, 30000);
    return () => {
      if (balanceIntervalRef.current) {
        clearInterval(balanceIntervalRef.current);
      }
    };
  }, []);
  
  const [developmentPlan, setDevelopmentPlan] = useState([]);
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0);
  const [showApprovalButtons, setShowApprovalButtons] = useState(false);
  const [isValidatingVisually, setIsValidatingVisually] = useState(false);
  const [revisionPlan, setRevisionPlan] = useState([]);

  // Cleanup all intervals on unmount
  useEffect(() => {
    return () => {
      if (revisionIntervalRef.current) {
        clearInterval(revisionIntervalRef.current);
      }
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
      if (balanceIntervalRef.current) {
        clearInterval(balanceIntervalRef.current);
      }
    };
  }, []);

  const handleStopGeneration = () => {
    // TODO: Implement stop generation logic
    setIsGenerating(false);
    setGenerationStatus('idle');
    toast({
      title: "Generation Stopped",
      description: "Code generation has been stopped.",
    });
  };

  const handleApprove = () => {
    setShowApprovalButtons(false);
    setGenerationStatus('idle');
    setDevelopmentPlan([]);
    
    toast({
      title: "Project Approved!",
      description: "Your application is ready to use.",
    });
  };

  const handleRevise = () => {
    // Clear any existing revision interval
    if (revisionIntervalRef.current) {
      clearInterval(revisionIntervalRef.current);
    }
    
    setShowApprovalButtons(false);
    
    // Create revision plan
    const revisions = [
      { name: 'Analyze Feedback', description: 'Understanding required changes', status: 'in-progress' },
      { name: 'Visual Adjustments', description: 'UI/UX improvements', status: 'pending' },
      { name: 'Functional Fixes', description: 'Logic and behavior corrections', status: 'pending' },
      { name: 'Re-validation', description: 'Final verification', status: 'pending' }
    ];
    
    setRevisionPlan(revisions);
    setDevelopmentPlan(revisions);
    setCurrentTaskIndex(0);
    
    toast({
      title: "Revision Mode",
      description: "Creating plan for improvements...",
    });
    
    // Simulate revision workflow
    let taskIdx = 0;
    revisionIntervalRef.current = setInterval(() => {
      if (taskIdx < revisions.length - 1) {
        setDevelopmentPlan(prev => {
          const updated = [...prev];
          updated[taskIdx] = { ...updated[taskIdx], status: 'validating' };
          return updated;
        });
        
        setTimeout(() => {
          setDevelopmentPlan(prev => {
            const updated = [...prev];
            updated[taskIdx] = { ...updated[taskIdx], status: 'completed' };
            if (taskIdx < revisions.length - 1) {
              updated[taskIdx + 1] = { ...updated[taskIdx + 1], status: 'in-progress' };
            }
            return updated;
          });
          taskIdx++;
          setCurrentTaskIndex(taskIdx);
        }, 2000);
      } else {
        if (revisionIntervalRef.current) {
          clearInterval(revisionIntervalRef.current);
          revisionIntervalRef.current = null;
        }
        // Show approval buttons again after revisions
        setTimeout(() => {
          setShowApprovalButtons(true);
        }, 2000);
      }
    }, 4000);
  };

  const handleSendPrompt = async (prompt) => {
    // STEP 1: Classify task type using AI
    console.log('[CHIMERA] 🔍 Classifying task type...');
    const classificationResult = await classifyTask(prompt, selectedModel);
    const taskType = classificationResult?.classification?.task_type || 'code_generation';
    const confidence = classificationResult?.classification?.confidence || 0.5;
    
    console.log(`[CHIMERA] ✅ Task classified as: ${taskType} (confidence: ${confidence})`);
    
    // STEP 2: Route to appropriate handler based on task type
    if (taskType === 'browser_automation' && confidence > 0.6) {
      // Handle browser automation in chat
      console.log('[CHIMERA] 🤖 Routing to browser automation...');
      await handleBrowserAutomationTask(prompt);
      return;
    }
    
    // For code_generation, document_verification, or general_chat, continue with normal flow
    const userMessage = { role: 'user', content: prompt };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    
    setIsGenerating(true);
    setGenerationStatus('generating');
    
    // CHAT MODE - just conversation, no code generation
    if (chatMode === 'chat') {
      try {
        // Simple chat response without code generation
        
        // Clean history - keep only role and content
        const cleanHistory = messages.map(m => ({
          role: m.role,
          content: m.content
        }));
        
        console.log('📤 Sending to chat API:', {
          message: prompt,
          historyLength: cleanHistory.length,
          model: chatModel
        });
        
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: prompt,
            history: cleanHistory, // Send clean history
            model: chatModel,
            session_id: currentSessionId // Include session ID for context management
          })
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`API error ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        
        console.log('✅ Chat API response:', data);
        console.log('Message field:', data.message);
        console.log('Response field:', data.response);
        
        // Handle context warnings and session transitions
        if (data.context_warning) {
          console.log('📊 Context:', data.context_warning);
          // Could show toast notification here
        }
        
        if (data.new_session_id) {
          // Model switched or context limit reached - new session created
          console.log('🔄 New session created:', data.new_session_id);
          setCurrentSessionId(data.new_session_id);
        }
        
        const aiMessage = { 
          role: 'assistant', 
          content: data.message || data.response,
          cost: data.cost,
          context_info: data.context_usage // Store context usage info
        };
        const updatedMessages = [...newMessages, aiMessage];
        setMessages(updatedMessages);
        
        let newTotalCost = totalCost;
        if (data.cost) {
          newTotalCost = totalCost + data.cost.total_cost;
          setTotalCost(newTotalCost);
        }
        
        // СОХРАНЯЕМ В БАЗУ!
        if (currentSessionId) {
          await updateSession(currentSessionId, {
            messages: updatedMessages,
            total_cost: newTotalCost
          });
          console.log('✅ Session updated in database');
        } else {
          // Создаем новую сессию если её нет
          const session = await createSession({
            name: prompt.substring(0, 50),
            messages: updatedMessages,
            total_cost: newTotalCost
          });
          setCurrentSessionId(session.id);
          console.log('🆕 New session created:', session.id);
        }
        
        setGenerationStatus('success');
        setTimeout(() => setGenerationStatus('idle'), 3000);
        
      } catch (error) {
        console.error('❌ Chat error:', error);
        console.error('Error details:', error.message);
        console.error('Error stack:', error.stack);
        
        // Fallback to simple response
        const aiMessage = { 
          role: 'assistant', 
          content: `[Error: ${error.message}] I understand! In Chat mode, I can help you plan and discuss your app idea. When you're ready to generate code, switch to Agent mode using the toggle below.`
        };
        setMessages([...newMessages, aiMessage]);
        setGenerationStatus('idle');
      } finally {
        setIsGenerating(false);
      }
      return;
    }
    
    // AGENT MODE - code generation with development plan
    if (chatMode === 'agent') {
      // Clear any existing progress interval
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
      
      const plan = [
        { name: 'Planning', description: 'Creating project structure', status: 'in-progress' },
        { name: 'Design Specification', description: 'Generating UI/UX design', status: 'pending' },
        { name: 'UI Components', description: 'Building interface components', status: 'pending' },
        { name: 'Logic & State', description: 'Implementing functionality', status: 'pending' },
        { name: 'Validation', description: 'Testing and validation', status: 'pending' },
        { name: 'Finalization', description: 'Final review and polish', status: 'pending' }
      ];
      setDevelopmentPlan(plan);
      setCurrentTaskIndex(0);
      
      // Simulate task progression
      let taskIdx = 0;
      progressIntervalRef.current = setInterval(() => {
        if (taskIdx < plan.length - 1) {
          // Mark current as validating
          setDevelopmentPlan(prev => {
            const updated = [...prev];
            updated[taskIdx] = { ...updated[taskIdx], status: 'validating' };
            return updated;
          });
          
          // After validation, mark as completed and move to next
          setTimeout(() => {
            setDevelopmentPlan(prev => {
              const updated = [...prev];
              updated[taskIdx] = { ...updated[taskIdx], status: 'completed' };
              if (taskIdx < plan.length - 1) {
                updated[taskIdx + 1] = { ...updated[taskIdx + 1], status: 'in-progress' };
              }
              return updated;
            });
            taskIdx++;
            setCurrentTaskIndex(taskIdx);
          }, 2000);
        } else {
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current);
            progressIntervalRef.current = null;
          }
        }
      }, 4000);
    }
    
    try {
      // DESIGN-FIRST WORKFLOW: Generate design specification first
      let designSpec = '';
      let mockupUrls = [];
      
      if (chatMode === 'agent') {
        try {
          console.log('🎨 Step 1: Generating design specification...');
          // Use a text-only model for design specification (not image generation model)
          const designResponse = await generateDesign(prompt, 'google/gemini-2.5-flash-image');
          designSpec = designResponse.design_spec;
          
          console.log('✅ Design spec generated');
          
          // STEP 2: Generate visual mockup (IMAGE)
          console.log('🖼️ Step 2: Generating visual mockup...');
          // Use image generation model for visual mockup
          const mockupResponse = await generateMockup(designSpec, prompt, 'google/gemini-2.5-flash-image-preview');
          
          if (mockupResponse.mockup_data) {
            // mockup_data может быть URL или base64
            mockupUrls = Array.isArray(mockupResponse.mockup_data) 
              ? mockupResponse.mockup_data 
              : [mockupResponse.mockup_data];
            
            console.log('✅ Mockup generated:', mockupUrls.length, 'images');
            
            // Show mockup to user
            const mockupMessage = {
              role: 'assistant',
              content: `## 🎨 Design Mockup\n\nHere's how your app will look:\n\n**Do you approve this design?**\n- Type "yes" or "approve" to proceed with code generation\n- Type "change [details]" to revise the design`,
              image: mockupUrls[0],  // Add image field for proper rendering
              type: 'mockup',  // Add type for special handling
              isDesign: true,
              mockupUrls: mockupUrls
            };
            
            newMessages.push(mockupMessage);
            setMessages([...newMessages]);
            
            // Save pending data for approval callback
            setPendingPrompt(prompt);
            setPendingDesign(designSpec);
            
            // WAIT FOR USER APPROVAL
            setAwaitingDesignApproval(true);
            setIsGenerating(false);
            
            // Stop here - wait for user to approve/reject
            console.log('⏸️ Waiting for design approval...');
            return;
          }
        } catch (designError) {
          console.error('Design/Mockup generation failed:', designError);
          // Continue without design if it fails
        }
      }
      
      // Generate code (with design spec if available)
      const enhancedPrompt = designSpec 
        ? `${prompt}\n\n**Design Specification to Follow:**\n${designSpec}`
        : prompt;
      
      console.log('🚀 Starting code generation with model:', selectedModel);
      const response = await generateCode(enhancedPrompt, newMessages, selectedModel);
      console.log('✅ Code generation response received:', {
        hasCode: !!response.code,
        codeLength: response.code?.length || 0,
        message: response.message?.substring(0, 50)
      });
      
      const aiMessage = { 
        role: 'assistant', 
        content: response.message,
        cost: response.cost 
      };
      const updatedMessages = [...newMessages, aiMessage];
      setMessages(updatedMessages);
      
      console.log('📝 Setting generated code, length:', response.code?.length);
      setGeneratedCode(response.code);
      console.log('✅ Generated code set in state');
      
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
      
      setGenerationStatus('success');
      
      toast({
        title: "Code Generated",
        description: "Your app is ready.",
      });
      
      // Automatic visual validation for Agent mode
      if (chatMode === 'agent' && visualValidatorEnabled) {
        setIsValidatingVisually(true);
        
        // Add visual validation task
        setDevelopmentPlan(prev => {
          if (prev.length > 0) {
            const updated = [...prev];
            updated.push({ 
              name: 'Visual Validation', 
              description: 'Checking UI compliance', 
              status: 'in-progress' 
            });
            return updated;
          }
          return prev;
        });
        
        // Simulate visual validation (in production, this would call the vision model)
        setTimeout(() => {
          setDevelopmentPlan(prev => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            if (lastIdx >= 0) {
              updated[lastIdx] = { ...updated[lastIdx], status: 'validating' };
            }
            return updated;
          });
          
          // After validation, show approval buttons
          setTimeout(() => {
            setDevelopmentPlan(prev => {
              const updated = [...prev];
              const lastIdx = updated.length - 1;
              if (lastIdx >= 0) {
                updated[lastIdx] = { ...updated[lastIdx], status: 'completed' };
              }
              return updated;
            });
            
            setIsValidatingVisually(false);
            setShowApprovalButtons(true);
            
            toast({
              title: "Visual Validation Complete",
              description: "UI passes all checks. Ready for your approval.",
            });
          }, 2000);
        }, 2000);
      } else {
        // Reset to idle after 3 seconds
        setTimeout(() => {
          setGenerationStatus('idle');
          setIsGenerating(false);
        }, 3000);
      }
      
    } catch (error) {
      console.error('Error:', error);
      setGenerationStatus('error');
      
      toast({
        title: "Error",
        description: "Failed to generate code.",
        variant: "destructive"
      });
      
      // Reset to idle after 5 seconds
      setTimeout(() => setGenerationStatus('idle'), 5000);
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

  const handleDeleteMessage = (index) => {
    console.log(`🗑️ Deleting message at index ${index} and all after it`);
    console.log('Before delete - messages count:', messages.length);
    
    // Delete message at index and all messages after it
    const newMessages = messages.slice(0, index);
    setMessages(newMessages);
    
    console.log('After delete - messages count:', newMessages.length);
    
    // If we deleted code generation messages, clear generated code
    const hasCodeGeneration = newMessages.some(m => 
      m.role === 'assistant' && m.content.includes('```')
    );
    
    if (!hasCodeGeneration) {
      setGeneratedCode('');
      setShowPreview(false);
      console.log('🧹 Cleared generated code and preview');
    }
  };

  const handleEditMessage = (index, newContent) => {
    console.log(`✏️ Editing message at index ${index}`);
    
    // Update message content
    setMessages(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], content: newContent };
      console.log('Updated message:', updated[index]);
      return updated;
    });
    
    // Delete all messages after the edited one (will regenerate)
    setTimeout(() => {
      const newMessages = messages.slice(0, index + 1);
      newMessages[index] = { ...newMessages[index], content: newContent };
      setMessages(newMessages);
      console.log('After edit - kept messages up to index:', index);
    }, 100);
  };

  const handleRegenerateFromMessage = async (index) => {
    console.log(`🔄 Regenerating from message index ${index}`);
    console.log('Current messages:', messages);
    
    // Keep messages up to and including index
    const contextMessages = messages.slice(0, index + 1);
    console.log('Context messages after slice:', contextMessages);
    
    setMessages(contextMessages);
    
    // Get the last user message as the prompt
    const lastUserMessage = contextMessages.filter(m => m.role === 'user').pop();
    console.log('Last user message:', lastUserMessage);
    
    if (lastUserMessage) {
      // Small delay to ensure state is updated
      setTimeout(async () => {
        console.log('🚀 Starting regeneration with prompt:', lastUserMessage.content);
        await handleSendPrompt(lastUserMessage.content);
      }, 100);
    } else {
      console.warn('⚠️ No user message found to regenerate from');
    }
  };

  const handleBrowserAutomationTask = async (goal) => {
    console.log('[CHIMERA] 🤖 Starting browser automation from chat:', goal);
    
    // Add user message
    const userMessage = { role: 'user', content: goal };
    setMessages(prev => [...prev, userMessage]);
    
    // Add system message indicating automation started
    const systemMessage = {
      role: 'system',
      content: `🤖 **Browser Automation Started**\n\nGoal: ${goal}\n\n*Initializing automation agent...*`
    };
    setMessages(prev => [...prev, systemMessage]);
    
    // Switch to automation mode with the goal pre-filled
    setShowAutomation(true);
    // TODO: Pass the goal to AutomationPage so it auto-starts
    // For now, user will see automation page with empty input
  };

  // ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ В ЧАТЕ
  const handleGenerateImage = async (prompt) => {
    console.log('[CHIMERA] 🎨 Generating image:', prompt);
    
    // Add user message
    const userMessage = { role: 'user', content: `🎨 ${prompt}` };
    setMessages(prev => [...prev, userMessage]);
    
    setIsGenerating(true);
    
    try {
      // Call backend image generation endpoint
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/generate-image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt,
          model: visualValidatorModel // Используем Visual Validator (Gemini Nano Banana)
        })
      });
      
      if (!response.ok) {
        throw new Error('Image generation failed');
      }
      
      const data = await response.json();
      
      // Add AI message with image
      const imageMessage = {
        role: 'assistant',
        content: data.image_url ? `![Generated Image](${data.image_url})` : data.error || 'Image generation failed',
        isImage: true,
        imageUrl: data.image_url
      };
      
      setMessages(prev => [...prev, imageMessage]);
      
      // Update session
      const updatedMessages = [...messages, userMessage, imageMessage];
      
      if (currentSessionId) {
        await updateSession(currentSessionId, {
          messages: updatedMessages,
          total_cost: totalCost + (data.cost?.total_cost || 0)
        });
      }
      
      setTotalCost(totalCost + (data.cost?.total_cost || 0));
      
      console.log('✅ Image generated successfully');
    } catch (error) {
      console.error('❌ Image generation error:', error);
      
      const errorMessage = {
        role: 'assistant',
        content: `⚠️ Failed to generate image: ${error.message}`
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsGenerating(false);
    }
  };

  // УМНАЯ ФУНКЦИЯ PREVIEW - зависит от chatMode
  const handleOpenPreview = () => {
    console.log('[CHIMERA] Opening Preview in mode:', chatMode);
    
    if (chatMode === 'automation') {
      // AUTOMATION MODE → открываем AutomationPage
      console.log('[CHIMERA] Opening AutomationPage...');
      setShowAutomation(true);
    } else if (chatMode === 'agent') {
      // CODE MODE → открываем PreviewPanel с кодом
      console.log('[CHIMERA] Opening Code Preview...');
      setShowPreview(true);
    } else {
      // CHAT MODE → открываем артефакты (пока что просто preview)
      console.log('[CHIMERA] Opening Artifacts Preview...');
      setShowPreview(true);
    }
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

  // Wire annotator callbacks for ChatInterface
  useEffect(() => {
    window.onAnnotateMockup = (img) => {
      setAnnotateImageUrl(img);
      setShowAnnotator(true);
    };
    window.onApproveDesign = async () => {
      setAwaitingDesignApproval(false);
      toast({ title: 'Design Approved', description: 'Proceeding to code generation.' });
      // Auto-continue to code generation using saved prompt and design spec
      const prompt = pendingPrompt;
      const designSpec = pendingDesign;
      if (!prompt || !designSpec) return;
      try {
        setIsGenerating(true);
        setGenerationStatus('generating');
        const enhancedPrompt = `${pendingPrompt}\n\n**Design Specification to Follow:**\n${pendingDesign}`;
        const response = await generateCode(enhancedPrompt, messages, selectedModel);
        const aiMessage = { role: 'assistant', content: response.message, cost: response.cost };
        const updatedMessages = [...messages, aiMessage];
        setMessages(updatedMessages);
        setGeneratedCode(response.code);
        let newTotalCost = totalCost;
        if (response.cost) {
          newTotalCost = totalCost + response.cost.total_cost;
          setTotalCost(newTotalCost);
        }
        if (currentSessionId) {
          await updateSession(currentSessionId, { messages: updatedMessages, generated_code: response.code, total_cost: newTotalCost });
        } else {
          const session = await createSession({ name: prompt.substring(0, 50), messages: updatedMessages, generated_code: response.code, total_cost: newTotalCost });
          setCurrentSessionId(session.id);
        }
        if (window.innerWidth < 768) setShowPreview(true);
        setGenerationStatus('success');
        setTimeout(() => setGenerationStatus('idle'), 3000);
      } catch (e) {
        console.error('Code gen after approval failed:', e);
        setGenerationStatus('error');
        toast({ title: 'Error', description: 'Failed to generate code after approval.', variant: 'destructive' });
        setTimeout(() => setGenerationStatus('idle'), 5000);
      } finally {
        setIsGenerating(false);
      }
    };
    return () => {
      window.onAnnotateMockup = null;
      window.onApproveDesign = null;
    };
  }, []);

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

  if (showAutomation) {
    return <AutomationPage onClose={() => setShowAutomation(false)} />;
  }

  if (showAIEntry) {
    return <AIEntryPoint onClose={() => setShowAIEntry(false)} />;
  }

  if (showDocVerification) {
    return <DocumentVerification onClose={() => setShowDocVerification(false)} />;
  }

  if (showSelfImprovement) {
    return <SelfImprovement onClose={() => setShowSelfImprovement(false)} />;
  }

  if (showSettings) {
    return (
      <div className="flex overflow-hidden bg-[#0f0f10]" style={{ height: '100dvh' }}>
        <Settings 
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          chatModel={chatModel}
          onChatModelChange={setChatModel}
          onOpenDocVerification={() => setShowDocVerification(true)}
          onClose={() => setShowSettings(false)}
          visualValidatorEnabled={visualValidatorEnabled}
          onVisualValidatorToggle={setVisualValidatorEnabled}
          visualValidatorModel={visualValidatorModel}
          onVisualValidatorModelChange={setVisualValidatorModel}
          researchPlannerEnabled={researchPlannerEnabled}
          onResearchPlannerToggle={setResearchPlannerEnabled}
          researchPlannerModel={researchPlannerModel}
          onResearchPlannerModelChange={setResearchPlannerModel}
        />
        <Toaster />
      </div>
    );
  }

  return (
    <div className="flex overflow-hidden bg-[#0f0f10]" style={{ height: '100dvh' }}>
      {/* Sidebar - только на мобильных устройствах показываем через кнопку */}
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
        {/* Chat Interface - SHOWN BY DEFAULT on mobile */}
        <div className={`${showPreview ? 'hidden' : 'flex'} md:flex flex-1 flex-col overflow-hidden`}>
          <ChatInterface 
            onSendPrompt={handleSendPrompt} 
            messages={messages} 
            onSave={handleSaveProject}
            totalCost={totalCost}
            apiBalance={apiBalance}
            activeModel={selectedModel}
            chatModel={chatModel}
            validatorEnabled={visualValidatorEnabled}
            validatorModel={visualValidatorModel}
            generationStatus={generationStatus}
            onOpenSettings={handleOpenSettings}
            onOpenAutomation={() => setShowAutomation(true)}
            onOpenDocVerification={() => setShowDocVerification(true)}
            onOpenSelfImprovement={() => setShowSelfImprovement(true)}
            onOpenAIEntry={() => setShowAIEntry(true)}
            onOpenPreview={handleOpenPreview}
            onNewProject={handleNewProject}
            onSessionSelect={handleSessionSelect}
            onGenerateImage={handleGenerateImage}
            currentSessionId={currentSessionId}
            isGenerating={isGenerating}
            onStopGeneration={handleStopGeneration}
            chatMode={chatMode}
            onChatModeChange={setChatMode}
            developmentPlan={developmentPlan}
            currentTaskIndex={currentTaskIndex}
            showApprovalButtons={showApprovalButtons}
            onApprove={handleApprove}
            onRevise={handleRevise}
            onDeleteMessage={handleDeleteMessage}
            onEditMessage={handleEditMessage}
            onRegenerateFromMessage={handleRegenerateFromMessage}
          />
        </div>

        {/* Preview Panel - HIDDEN BY DEFAULT on mobile */}
        <div className={`${showPreview ? 'flex' : 'hidden'} md:flex flex-1 flex-col overflow-hidden relative`}>
          <PreviewPanel 
            generatedCode={generatedCode} 
            isGenerating={isGenerating}
            chatMode={chatMode}
          />
        </div>

        {/* Floating Preview Toggle Button (only on mobile, only when chat is visible) */}
        {!showPreview && !showSettings && !showAutomation && !showDocVerification && !showSelfImprovement && !showAIEntry && (
          <button
            onClick={() => setShowPreview(true)}
            className="md:hidden fixed right-0 top-1/2 -translate-y-1/2 z-50 bg-transparent border-l-2 border-t-2 border-b-2 border-gray-700 hover:border-gray-500 hover:bg-gray-900/50 text-gray-400 hover:text-gray-300 px-2 py-4 rounded-l-lg backdrop-blur-sm transform transition-all duration-300"
            style={{ 
              writingMode: 'vertical-rl',
              textOrientation: 'mixed'
            }}
          >
            <span className="text-xs font-medium tracking-wider">
              PREVIEW
            </span>
          </button>
        )}

        {/* Close Preview Button (only on mobile, only when preview is visible) */}
        {showPreview && !showSettings && !showAutomation && !showDocVerification && !showSelfImprovement && !showAIEntry && (
          <button
            onClick={() => setShowPreview(false)}
            className="md:hidden fixed right-0 top-1/2 -translate-y-1/2 z-50 bg-transparent border-l-2 border-t-2 border-b-2 border-gray-700 hover:border-gray-500 hover:bg-gray-900/50 text-gray-400 hover:text-gray-300 px-2 py-4 rounded-l-lg backdrop-blur-sm transform transition-all duration-300"
            style={{ 
              writingMode: 'vertical-rl',
              textOrientation: 'mixed'
            }}
          >
            <span className="text-xs font-medium tracking-wider">
              CHAT
            </span>
          </button>
        )}
      </div>

      {showAnnotator && (
        <AnnotatorModal
          imageUrl={annotateImageUrl}
          onClose={() => setShowAnnotator(false)}
          onSubmit={async ({ annotations, summary, annotatedImageDataUrl }) => {
            setShowAnnotator(false);
            // Store feedback as a message and trigger design revision
            const feedbackMsg = { role: 'user', content: `Design feedback:\n${summary}`, image: annotatedImageDataUrl };
            setMessages(prev => [...prev, feedbackMsg]);

            try {
              const { reviseDesign } = await import('./services/api');
              // Find last design spec in messages
              const lastDesign = messages.slice().reverse().find(m => m.isDesign);
              const currentDesignSpec = lastDesign ? lastDesign.content : '';
              const revision = await reviseDesign(currentDesignSpec, summary, visualValidatorModel);
              const revisedSpec = revision?.design_spec || '';
              setMessages(prev => [...prev, { role: 'assistant', content: `🛠️ Revised Design Spec:\n\n${revisedSpec.substring(0, 800)}...` }]);
              setAwaitingDesignApproval(true);
            } catch (e) {
              console.error('Design revision failed:', e);
              toast({ title: 'Revision failed', description: 'Could not revise design.', variant: 'destructive' });
            }
          }}
        />
      )}

      <Toaster />
    </div>
  );
}

export default App;