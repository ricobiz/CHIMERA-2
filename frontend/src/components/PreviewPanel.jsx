import React, { useState, useEffect } from 'react';
import { Eye, Code, RefreshCw, Download, Github } from 'lucide-react';
import { Button } from './ui/button';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';
import { exportProject } from '../services/api';
import { toast } from '../hooks/use-toast';

const PreviewPanel = ({ generatedCode, isGenerating, onExport }) => {
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
      const projectName = `lovable-app-${Date.now()}`;
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

  // Create a blob URL for the preview
  const createPreviewHTML = () => {
    if (!generatedCode) return '';
    
    // Clean the code - remove any export default statements for iframe
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
    body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    const { useState, useEffect, useMemo, useCallback } = React;
    
    ${cleanCode}
    
    // Find the main component (function or const)
    const componentMatch = \`${cleanCode}\`.match(/(?:function|const)\\s+(\\w+)\\s*(?:=|\\()/);
    const ComponentName = componentMatch ? componentMatch[1] : 'App';
    
    // Render the component
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
    <div className="flex-1 bg-[#1a1a1b] border-l border-gray-800 flex flex-col h-screen">
      {/* Header */}
      <div className="border-b border-gray-800 p-4">
        <div className="flex items-center justify-between">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-auto">
            <TabsList className="bg-gray-800">
              <TabsTrigger value="preview" className="gap-2">
                <Eye className="w-4 h-4" />
                Preview
              </TabsTrigger>
              <TabsTrigger value="code" className="gap-2">
                <Code className="w-4 h-4" />
                Code
              </TabsTrigger>
            </TabsList>
          </Tabs>
          <div className="flex items-center gap-2">
            <Button
              onClick={refreshPreview}
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
            <Button
              onClick={handleExport}
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white"
              disabled={!generatedCode}
            >
              <Download className="w-4 h-4" />
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
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent mb-4"></div>
                  <p className="text-gray-400">Generating your app...</p>
                </div>
              </div>
            ) : generatedCode ? (
              <iframe
                key={previewKey}
                srcDoc={createPreviewHTML()}
                className="w-full h-full border-0"
                title="Preview"
                sandbox="allow-scripts allow-same-origin"
              />
            ) : (
              <div className="flex items-center justify-center h-full bg-gray-900">
                <div className="text-center max-w-md">
                  <Eye className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">
                    No Preview Yet
                  </h3>
                  <p className="text-gray-400">
                    Start by describing your app idea in the chat, and the live preview will appear here.
                  </p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="w-full h-full overflow-auto bg-[#0f0f10] p-6">
            {generatedCode ? (
              <pre className="text-sm text-gray-300 font-mono">
                <code>{generatedCode}</code>
              </pre>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-md">
                  <Code className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">
                    No Code Generated
                  </h3>
                  <p className="text-gray-400">
                    Generated code will appear here once the AI creates your app.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PreviewPanel;