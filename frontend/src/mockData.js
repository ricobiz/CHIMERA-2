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

export const samplePrompts = [
  'An app that helps me plan my day',
  'A recipe finder with meal planning',
  'A fitness tracker with workout logs',
  'A budget manager with expense tracking'
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