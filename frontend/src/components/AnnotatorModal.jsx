import React, { useRef, useState, useEffect } from 'react';
import { X, Circle, MousePointer, Undo2, Send } from 'lucide-react';
import { Button } from './ui/button';

// Simple image annotator: draw circles by click-drag, add text notes per circle
const AnnotatorModal = ({ imageUrl, onClose, onSubmit }) => {
  const canvasRef = useRef(null);
  const imgRef = useRef(null);
  const containerRef = useRef(null);
  const [drawing, setDrawing] = useState(false);
  const [startPos, setStartPos] = useState(null);
  const [shapes, setShapes] = useState([]); // {x, y, r, note}
  const [activeTool] = useState('circle');
  const [noteInput, setNoteInput] = useState('');
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      imgRef.current = img;
      draw();
      // Fit to container width
      const cont = containerRef.current;
      if (cont) {
        const ratio = cont.clientWidth / img.width;
        setScale(ratio);
      }
    };

    img.src = imageUrl;
  }, [imageUrl]);

  useEffect(() => {
    draw();
  }, [shapes, scale]);

  const getCanvas = () => canvasRef.current;

  const draw = () => {
    const canvas = getCanvas();
    if (!canvas || !imgRef.current) return;
    const ctx = canvas.getContext('2d');
    const w = imgRef.current.width * scale;
    const h = imgRef.current.height * scale;
    canvas.width = w;
    canvas.height = h;

    // background
    ctx.clearRect(0,0,w,h);
    ctx.drawImage(imgRef.current, 0, 0, w, h);

    // draw shapes
    for (const s of shapes) {
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(239, 68, 68, 0.9)'; // red
      ctx.lineWidth = 3;
      ctx.arc(s.x * scale, s.y * scale, s.r * scale, 0, Math.PI * 2);
      ctx.stroke();
      if (s.note) {
        ctx.fillStyle = 'rgba(0,0,0,0.6)';
        ctx.fillRect(s.x * scale + s.r * scale + 6, s.y * scale - 14, ctx.measureText(s.note).width + 10, 18);
        ctx.fillStyle = '#f5f5f5';
        ctx.font = '12px monospace';
        ctx.fillText(s.note, s.x * scale + s.r * scale + 10, s.y * scale);
      }
    }
  };

  const getPos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / scale;
    const y = (e.clientY - rect.top) / scale;
    return { x, y };
  };

  const handleMouseDown = (e) => {
    if (activeTool !== 'circle') return;
    setDrawing(true);
    setStartPos(getPos(e));
  };

  const handleMouseMove = (e) => {
    if (!drawing || !startPos) return;
    const current = getPos(e);
    const dx = current.x - startPos.x;
    const dy = current.y - startPos.y;
    const r = Math.sqrt(dx*dx + dy*dy);
    // preview by drawing temp
    const canvas = getCanvas();
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    draw();
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(239, 68, 68, 0.8)';
    ctx.lineWidth = 2;
    ctx.arc(startPos.x * scale, startPos.y * scale, r * scale, 0, Math.PI * 2);
    ctx.stroke();
  };

  const handleMouseUp = (e) => {
    if (!drawing || !startPos) return;
    setDrawing(false);
    const end = getPos(e);
    const dx = end.x - startPos.x;
    const dy = end.y - startPos.y;
    const r = Math.sqrt(dx*dx + dy*dy);
    setShapes(prev => [...prev, { x: startPos.x, y: startPos.y, r, note: noteInput.trim() }]);
    setNoteInput('');
  };

  const undo = () => {
    setShapes(prev => prev.slice(0, -1));
  };

  const handleSubmit = () => {
    // Provide both structured annotations and human text summary
    const summaryParts = shapes.map((s, i) => `#${i+1}: circle at (${Math.round(s.x)}, ${Math.round(s.y)}), r=${Math.round(s.r)} ${s.note ? '- note: ' + s.note : ''}`);
    const summary = `Annotations (user feedback):\n${summaryParts.join('\n')}`;
    onSubmit({ annotations: shapes, summary, annotatedImageDataUrl: canvasRef.current.toDataURL('image/png') });
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#0f0f10] border border-gray-800 rounded-lg w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-3 border-b border-gray-800">
          <div className="flex items-center gap-2 text-gray-300">
            <MousePointer className="w-4 h-4" />
            <span className="text-sm">Annotate Mockup</span>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div ref={containerRef} className="p-3 overflow-auto">
          <canvas
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            className="max-w-full rounded border border-gray-700 bg-black"
          />
        </div>
        <div className="p-3 border-t border-gray-800 flex flex-col md:flex-row gap-2 md:items-center md:justify-between">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Circle className="w-4 h-4 text-red-400" />
            <span>Tool: Circle (click & drag). Add note before drawing to attach.</span>
          </div>
          <div className="flex items-center gap-2">
            <input
              className="px-2 py-1 text-xs bg-gray-900 border border-gray-700 rounded text-gray-300 placeholder-gray-600"
              placeholder="Optional note for next circle..."
              value={noteInput}
              onChange={(e) => setNoteInput(e.target.value)}
            />
            <Button onClick={undo} className="bg-gray-700 hover:bg-gray-600 text-white h-8 px-3">
              <Undo2 className="w-4 h-4" />
            </Button>
            <Button onClick={handleSubmit} className="bg-purple-600 hover:bg-purple-500 text-white h-8 px-3 flex items-center gap-2">
              <Send className="w-4 h-4" />
              Send Feedback
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnnotatorModal;
