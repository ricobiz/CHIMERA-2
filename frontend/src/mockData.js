// Mock data for development
export const mockProjects = [
  {
    id: 'proj-1',
    name: 'New Prototype',
    description: 'studio-1027596611',
    lastAccessed: '7 hours ago',
    icon: '🚀'
  },
  {
    id: 'proj-2',
    name: 'AICW',
    description: 'aicw-05300840',
    lastAccessed: '7 hours ago',
    icon: '✨'
  }
];

// Platform features and capabilities
export const platformFeatures = [
  {
    id: 'code-generation',
    title: '⚡ AI Code Generation',
    category: 'Development',
    description: 'Generate full-stack applications using advanced AI models (Grok, GPT-5, Claude). Create React + FastAPI + MongoDB apps with automatic code generation, live preview, and export options.',
    howItWorks: 'Describe your app idea in natural language, and Chimera will generate complete, production-ready code with proper structure, styling, and functionality.'
  },
  {
    id: 'design-first',
    title: '🎨 Design-First Workflow',
    category: 'UI/UX',
    description: 'AI-powered visual design generation before coding. Uses Gemini Nano Banana for cost-effective, high-quality interface design with automatic visual validation.',
    howItWorks: 'Chimera first creates a detailed design specification based on your requirements, validates it visually, then generates code that matches the approved design.'
  },
  {
    id: 'browser-automation',
    title: '🤖 Browser Automation',
    category: 'Automation',
    description: 'Intelligent browser automation using Playwright + AI vision models. Automate web tasks with natural language commands - no selectors needed.',
    howItWorks: 'Describe the task (e.g., "Navigate to Google and search for AI"), and the system plans steps, executes them using vision-based element detection, and validates results.'
  },
  {
    id: 'document-verification',
    title: '📄 Document Verification',
    category: 'Security',
    description: 'Triple-model AI verification system (GPT-5 + Claude 4.5 + Gemini Vision) for detecting document fraud, AI generation, and authenticity validation.',
    howItWorks: 'Upload a document image, and three top AI models independently analyze it for signs of fraud, forgery, or AI generation, then provide a consensus verdict with confidence scores.'
  },
  {
    id: 'self-improvement',
    title: '🧠 Self-Improvement System',
    category: 'Optimization',
    description: 'AI analyzes and optimizes its own codebase. Automatically selects best models for each task based on cost/quality ratio, detects code issues, and suggests improvements.',
    howItWorks: 'The system reviews its own code, identifies bottlenecks, security issues, and optimization opportunities, then can automatically apply fixes and reload services.'
  },
  {
    id: 'research-planner',
    title: '🔍 Research Planner',
    category: 'Intelligence',
    description: 'Pre-computation research agent that analyzes requirements, researches best practices, and plans implementation strategy before code generation.',
    howItWorks: 'Before generating code, the planner researches relevant technologies, frameworks, and patterns to ensure optimal architecture and implementation choices.'
  },
  {
    id: 'visual-validator',
    title: '✅ Visual Validator',
    category: 'Quality Assurance',
    description: 'AI-powered screenshot analysis for validating generated UIs. Ensures the generated interface matches design specifications and identifies visual issues.',
    howItWorks: 'Takes screenshots of generated apps and uses vision AI to verify correct implementation of design elements, colors, spacing, and layout.'
  },
  {
    id: 'context-management',
    title: '🔄 Smart Context Management',
    category: 'Performance',
    description: 'Dynamic context window management with automatic session switching, context compression, and token usage optimization across different AI models.',
    howItWorks: 'Monitors token usage, automatically compresses conversation history when needed, and creates new sessions with compressed context to maintain long conversations efficiently.'
  },
  {
    id: 'multi-model',
    title: '🎯 Multi-Model Support',
    category: 'AI Models',
    description: 'Access to 200+ AI models via OpenRouter including GPT-5, Claude 4.5, Gemini, Grok, and more. Real-time model switching and cost tracking.',
    howItWorks: 'Choose the best model for each task - use fast models for simple tasks, powerful models for complex reasoning, and specialized models for vision or code.'
  },
  {
    id: 'session-management',
    title: '💾 Session Management',
    category: 'Productivity',
    description: 'Automatic session creation, persistence, and recovery. Never lose your work - all conversations and generated code are saved and can be resumed anytime.',
    howItWorks: 'Each interaction creates or updates a session stored in MongoDB. Load previous sessions, continue conversations, and manage multiple projects simultaneously.'
  }
];

export const samplePrompts = [
  'Build a task management app with drag-and-drop',
  'Create a recipe finder with meal planning',
  'Design a fitness tracker with workout logs',
  'Make a budget manager with charts'
];

export const mockGeneratedCode = `import React, { useState } from 'react';
import { Card } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';

function App() {
  const [tasks, setTasks] = useState([]);
  const [input, setInput] = useState('');

  const addTask = () => {
    if (input.trim()) {
      setTasks([...tasks, { id: Date.now(), text: input, done: false }]);
      setInput('');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8">Task Manager</h1>
        <Card className="p-6 bg-slate-800/50 border-slate-700">
          <div className="flex gap-2 mb-6">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addTask()}
              placeholder="Add a new task..."
              className="bg-slate-900/50 border-slate-600 text-white"
            />
            <Button onClick={addTask} className="bg-blue-600 hover:bg-blue-700">
              Add
            </Button>
          </div>
          <div className="space-y-2">
            {tasks.map(task => (
              <div key={task.id} className="p-3 bg-slate-900/30 rounded-lg text-white">
                {task.text}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

export default App;`;