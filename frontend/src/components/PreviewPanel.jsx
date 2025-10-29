import React, { useState, useEffect } from 'react';
import { Eye, Code, RefreshCw, Download } from 'lucide-react';
import { Button } from './ui/button';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';
import { exportProject, getSessions } from '../services/api';
import { toast } from '../hooks/use-toast';
import AutomationPage from './automation/AutomationPage.tsx';

const PreviewPanel = ({ generatedCode, isGenerating, chatMode = 'chat', messages = [] }) => {
  const [activeTab, setActiveTab] = useState('preview');
  const [previewKey, setPreviewKey] = useState(0);
  const [iframeContent, setIframeContent] = useState('');
  const [allArtifacts, setAllArtifacts] = useState([]);

  useEffect(() => {
    if (generatedCode) {
      setIframeContent(createPreviewHTML());
    }
  }, [generatedCode]);

  // Load all artifacts from all sessions
  useEffect(() => {
    const loadAllArtifacts = async () => {
      try {
        const sessions = await getSessions();
        const artifacts = [];
        
        // Collect artifacts from all sessions
        sessions.forEach(session => {
          // Add generated code from session
          if (session.generated_code) {
            artifacts.push({
              type: 'code',
              code: session.generated_code,
              sessionId: session.id,
              sessionName: session.name,
              timestamp: session.created_at || session.last_updated,
              content: `App from: ${session.name}`
            });
          }
          
          // Parse messages if available
          if (session.messages && Array.isArray(session.messages)) {
            session.messages.forEach((msg, idx) => {
              // Images from msg.image field
              if (msg.image && (msg.image.startsWith('data:image') || msg.image.startsWith('http'))) {
                artifacts.push({
                  type: 'image',
                  url: msg.image,
                  sessionId: session.id,
                  sessionName: session.name,
                  timestamp: msg.timestamp || session.last_updated,
                  content: msg.content || 'Generated image'
                });
              }
              
              // Images from msg.imageUrl
              if (msg.imageUrl) {
                artifacts.push({
                  type: 'image',
                  url: msg.imageUrl,
                  sessionId: session.id,
                  sessionName: session.name,
                  timestamp: msg.timestamp || session.last_updated,
                  content: msg.content || 'Generated image'
                });
              }
            });
          }
        });
        
        // Sort by timestamp (newest first)
        artifacts.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        setAllArtifacts(artifacts);
        console.log('📦 Loaded artifacts from all sessions:', artifacts.length);
      } catch (error) {
        console.error('Failed to load artifacts:', error);
      }
    };
    
    if (chatMode === 'chat') {
      loadAllArtifacts();
    }
  }, [chatMode, messages]); // Reload when messages change

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
    
    // Extract and convert <style jsx> blocks
    let extractedStyles = '';
    cleanCode = cleanCode.replace(
      /<style\s+jsx(?:\s+global)?>\{`([^`]*)`\}<\/style>/g,
      (match, styleContent) => {
        extractedStyles += styleContent;
        return ''; // Remove the jsx style block
      }
    );
    
    // Convert template literals to string concatenation to avoid Babel parsing errors
    // Handles multiple ${} expressions in one template literal
    const convertTemplateLiteral = (match) => {
      // Extract content between backticks
      const content = match.slice(match.indexOf('`') + 1, match.lastIndexOf('`'));
      
      // Split by ${...} and convert to concatenation
      const parts = [];
      let currentText = '';
      let depth = 0;
      let isInExpression = false;
      let expression = '';
      
      for (let i = 0; i < content.length; i++) {
        const char = content[i];
        const nextChar = content[i + 1];
        
        if (char === '$' && nextChar === '{' && !isInExpression) {
          if (currentText) {
            parts.push(`"${currentText}"`);
            currentText = '';
          }
          isInExpression = true;
          depth = 1;
          i++; // skip {
        } else if (isInExpression) {
          if (char === '{') depth++;
          if (char === '}') {
            depth--;
            if (depth === 0) {
              parts.push(expression);
              expression = '';
              isInExpression = false;
            } else {
              expression += char;
            }
          } else {
            expression += char;
          }
        } else {
          currentText += char;
        }
      }
      
      if (currentText) {
        parts.push(`"${currentText}"`);
      }
      
      const joined = parts.join(' + ');
      const attr = match.match(/^(\w+)=/)?.[1] || 'attr';
      return `${attr}={${joined}}`;
    };
    
    // Apply template literal conversion to all attributes
    cleanCode = cleanCode.replace(
      /(\w+)=\{`[^`]*`\}/g,
      convertTemplateLiteral
    );
    
    return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Preview</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    * { box-sizing: border-box; }
    html, body { 
      margin: 0; 
      padding: 0; 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; 
      background-color: #0f0f10;
      color: #e5e7eb;
      min-height: 100vh;
    }
    #root {
      min-height: 100vh;
      background-color: #0f0f10;
    }
    ${extractedStyles ? `/* Extracted JSX Styles */\n${extractedStyles}` : ''}
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
        <div style="padding: 20px; color: #ef4444; font-family: monospace; background: #0f0f10; min-height: 100vh;">
          <h3 style="color: #f87171;">Preview Error</h3>
          <pre style="background: #1f2937; color: #e5e7eb; padding: 15px; border-radius: 8px; overflow-x: auto; border: 2px solid #374151;">\${error.message}</pre>
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
        {/* AUTOMATION MODE: Show AutomationPage */}
        {chatMode === 'automation' ? (
          <AutomationPage onClose={() => {}} embedded={true} />
        
        /* CHAT MODE: Show Artifacts Gallery */
        ) : chatMode === 'chat' ? (
          <div className="w-full h-full overflow-auto bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
            <div className="max-w-6xl mx-auto">
              <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                <span className="text-3xl">🎨</span>
                Artifacts
              </h2>
              
              {/* Extract and display all artifacts from all sessions */}
              {(() => {
                // Use artifacts from all sessions
                const artifacts = allArtifacts;
                
                if (artifacts.length === 0) {
                  return (
                    <div className="flex flex-col items-center justify-center h-96 text-center">
                      <div className="text-6xl mb-4">📦</div>
                      <h3 className="text-xl font-semibold text-white mb-2">No Artifacts Yet</h3>
                      <p className="text-gray-400 max-w-md">
                        Generate images using the 🖼️ button or create apps in Code mode.
                        All your creations will appear here!
                      </p>
                    </div>
                  );
                }
                
                return (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {artifacts.map((artifact, idx) => (
                      <div
                        key={`${artifact.sessionId}-${idx}`}
                        className="bg-gray-800 rounded-lg overflow-hidden shadow-lg hover:shadow-2xl transition-shadow cursor-pointer group"
                        onClick={() => {
                          // Open artifact in full view
                          if (artifact.type === 'image') {
                            window.open(artifact.url, '_blank');
                          } else if (artifact.type === 'code') {
                            // Show code preview
                            toast({
                              title: "Code Preview",
                              description: `Viewing code from: ${artifact.sessionName}`,
                            });
                          }
                        }}
                      >
                        {artifact.type === 'image' ? (
                          <>
                            <div className="aspect-video bg-gray-900 overflow-hidden">
                              <img
                                src={artifact.url}
                                alt="Generated artifact"
                                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                              />
                            </div>
                            <div className="p-4">
                              <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
                                <span className="text-lg">🖼️</span>
                                <span>Image</span>
                              </div>
                              <p className="text-sm text-gray-300 line-clamp-2">
                                {artifact.content?.substring(0, 100) || 'Generated image'}
                              </p>
                              <p className="text-xs text-gray-500 mt-1">
                                From: {artifact.sessionName}
                              </p>
                            </div>
                          </>
                        ) : artifact.type === 'code' ? (
                          <>
                            <div className="aspect-video bg-gray-900 overflow-hidden flex items-center justify-center">
                              <div className="text-6xl">💻</div>
                            </div>
                            <div className="p-4">
                              <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
                                <span className="text-lg">💻</span>
                                <span>App</span>
                              </div>
                              <p className="text-sm text-gray-300 line-clamp-2">
                                {artifact.content || 'Generated application'}
                              </p>
                              <p className="text-xs text-gray-500 mt-1">
                                From: {artifact.sessionName}
                              </p>
                            </div>
                          </>
                        ) : null}
                      </div>
                    ))}
                  </div>
                );
              })()}
                              </p>
                            </div>
                          </>
                        ) : null}
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>
          </div>
        
        /* CODE MODE: Show code preview/iframe */
        ) : activeTab === 'preview' ? (
          <div className="w-full h-full bg-[#0f0f10]">
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