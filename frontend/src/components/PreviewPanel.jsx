import React, { useState, useEffect } from 'react';
import { Eye, Code, RefreshCw, Download } from 'lucide-react';
import { Button } from './ui/button';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';
import { exportProject } from '../services/api';
import { toast } from '../hooks/use-toast';

const PreviewPanel = ({ generatedCode, isGenerating }) => {
  const [activeTab, setActiveTab] = useState('preview');
  const [previewKey, setPreviewKey] = useState(0);
  const [iframeContent, setIframeContent] = useState('');

  useEffect(() => {
    if (generatedCode) {
      setIframeContent(createPreviewHTML());
    }
  }, [generatedCode]);

  const refreshPreview = () => {
    setPreviewKey(prev => prev + 1);
    setIframeContent(createPreviewHTML());
  };

  const handleExport = async () => {
    if (!generatedCode) {
      toast({
        title: "Nothing to export",
        description: "Generate some code first.",
        variant: "destructive"
      });
      return;
    }

    try {
      const projectName = `app-${Date.now()}`;
      await exportProject(generatedCode, projectName);
      
      toast({
        title: "Success!",
        description: "Project exported successfully.",
      });
    } catch (error) {
      console.error('Export error:', error);
      toast({
        title: "Export failed",
        description: "Failed to export project.",
        variant: "destructive"
      });
    }
  };

  const createPreviewHTML = () => {
    if (!generatedCode) return '';
    
    let cleanCode = generatedCode
      .replace(/export\s+default\s+\w+;?/g, '')
      .replace(/export\s+{[^}]*};?/g, '');
    
    return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Preview</title>
  <script crossorigin src="https://unpkg.com/react@19/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@19/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    const { useState, useEffect, useMemo, useCallback } = React;
    
    ${cleanCode}
    
    const componentMatch = \`${cleanCode}\`.match(/(?:function|const)\\s+(\\w+)\\s*(?:=|\\()/)
    const ComponentName = componentMatch ? componentMatch[1] : 'App';
    
    try {
      const component = eval(ComponentName);
      const root = ReactDOM.createRoot(document.getElementById('root'));
      root.render(React.createElement(component));
    } catch (error) {
      document.getElementById('root').innerHTML = \`
        <div style="padding: 20px; color: #ef4444; font-family: monospace;">
          <h3>Preview Error</h3>
          <pre style="background: #1f2937; padding: 15px; border-radius: 8px; overflow-x: auto;">\${error.message}</pre>
        </div>
      \`;
      console.error('Preview error:', error);
    }
  </script>
</body>
</html>`;
  };

  return (
    <div className="flex-1 bg-[#1a1a1b] flex flex-col h-screen border-2 border-transparent animated-gradient-border-preview">
      {/* Header */}
      <div className="border-b border-gray-800 p-3 md:p-4">
        <div className="flex items-center justify-between">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-auto">
            <TabsList className="bg-gray-800">
              <TabsTrigger value="preview" className="gap-1 md:gap-2 text-xs md:text-sm">
                <Eye className="w-3 h-3 md:w-4 md:h-4" />
                <span className="hidden sm:inline">Preview</span>
              </TabsTrigger>
              <TabsTrigger value="code" className="gap-1 md:gap-2 text-xs md:text-sm">
                <Code className="w-3 h-3 md:w-4 md:h-4" />
                <span className="hidden sm:inline">Code</span>
              </TabsTrigger>
            </TabsList>
          </Tabs>
          <div className="flex items-center gap-1 md:gap-2">
            <Button
              onClick={refreshPreview}
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white"
            >
              <RefreshCw className="w-3 h-3 md:w-4 md:h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'preview' ? (
          <div className="w-full h-full bg-white">
            {isGenerating ? (
              <div className="flex items-center justify-center h-full bg-gray-900">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 md:h-12 md:w-12 border-4 border-purple-500 border-t-transparent mb-4"></div>
                  <p className="text-sm md:text-base text-gray-400">Generating your app...</p>
                </div>
              </div>
            ) : generatedCode ? (
              <iframe
                key={previewKey}
                srcDoc={iframeContent}
                className="w-full h-full border-0"
                title="Preview"
                sandbox="allow-scripts allow-same-origin"
              />
            ) : (
              <div className="flex items-center justify-center h-full bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
                <div className="text-center max-w-md px-4">
                  {/* Animated Icon */}
                  <div className="relative mb-6">
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-20 h-20 md:w-24 md:h-24 rounded-full border-4 border-purple-500/20 animate-ping"></div>
                    </div>
                    <div className="relative flex items-center justify-center">
                      <Eye className="w-12 h-12 md:w-16 md:h-16 text-purple-500 animate-pulse" />
                    </div>
                  </div>
                  
                  <h3 className="text-lg md:text-xl font-semibold text-white mb-2">
                    No Preview Yet
                  </h3>
                  <p className="text-sm md:text-base text-gray-400 mb-4">
                    Start by describing your app idea in the chat.
                  </p>
                  <p className="text-xs text-gray-600">
                    Your app will come to life here ✨
                  </p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="w-full h-full overflow-auto bg-[#0f0f10] p-3 md:p-6">
            {generatedCode ? (
              <pre className="text-xs md:text-sm text-gray-300 font-mono">
                <code>{generatedCode}</code>
              </pre>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-md px-4">
                  <Code className="w-12 h-12 md:w-16 md:h-16 text-gray-600 mx-auto mb-4" />
                  <h3 className="text-lg md:text-xl font-semibold text-white mb-2">
                    No Code Generated
                  </h3>
                  <p className="text-sm md:text-base text-gray-400">
                    Generated code will appear here.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Animated gradient border */}
      <style jsx>{`
        .animated-gradient-border-preview {
          position: relative;
          border: 2px solid transparent;
          background: linear-gradient(#1a1a1b, #1a1a1b) padding-box,
                      linear-gradient(90deg, 
                        rgba(16, 185, 129, 0.3),
                        rgba(59, 130, 246, 0.3),
                        rgba(236, 72, 153, 0.3),
                        rgba(59, 130, 246, 0.3),
                        rgba(16, 185, 129, 0.3)
                      ) border-box;
          background-size: 200% 100%;
          animation: gradientShiftPreview 3s ease infinite;
        }
        
        @keyframes gradientShiftPreview {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
      `}</style>
    </div>
  );
};

export default PreviewPanel;