import React, { useState, useEffect } from 'react';
import { Eye, Code, RefreshCw, Maximize2 } from 'lucide-react';
import { Button } from './ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';

const PreviewPanel = ({ generatedCode, isGenerating }) => {
  const [activeTab, setActiveTab] = useState('preview');
  const [previewKey, setPreviewKey] = useState(0);

  const refreshPreview = () => {
    setPreviewKey(prev => prev + 1);
  };

  // Create a blob URL for the preview
  const createPreviewHTML = () => {
    if (!generatedCode) return '';
    
    return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Preview</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { margin: 0; padding: 0; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="module">
    ${generatedCode}
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
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white"
            >
              <Maximize2 className="w-4 h-4" />
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