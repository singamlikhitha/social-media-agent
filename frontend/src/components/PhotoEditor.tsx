'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

interface PhotoEditorProps {
  imageUrl: string;
  onSave: (editedImageBlob: Blob, filterName: string) => void;
  onCancel: () => void;
}

const FILTERS = [
  { name: 'Original', css: 'none', values: {} },
  { name: 'Clarendon', css: 'contrast(1.2) saturate(1.35)', values: { contrast: 120, saturate: 135 } },
  { name: 'Gingham', css: 'brightness(1.05) hue-rotate(-10deg)', values: { brightness: 105 } },
  { name: 'Moon', css: 'grayscale(1) contrast(1.1) brightness(1.1)', values: { grayscale: 100, contrast: 110, brightness: 110 } },
  { name: 'Lark', css: 'contrast(0.9) brightness(1.15) saturate(0.85)', values: { contrast: 90, brightness: 115, saturate: 85 } },
  { name: 'Reyes', css: 'sepia(0.22) brightness(1.1) contrast(0.85) saturate(0.75)', values: { sepia: 22, brightness: 110, contrast: 85, saturate: 75 } },
  { name: 'Juno', css: 'contrast(1.15) saturate(1.8) sepia(0.08)', values: { contrast: 115, saturate: 180, sepia: 8 } },
  { name: 'Slumber', css: 'saturate(0.66) brightness(1.05) sepia(0.15)', values: { saturate: 66, brightness: 105, sepia: 15 } },
  { name: 'Crema', css: 'sepia(0.5) contrast(0.9) brightness(1.1) saturate(0.8)', values: { sepia: 50, contrast: 90, brightness: 110, saturate: 80 } },
  { name: 'Ludwig', css: 'contrast(1.05) saturate(1.3) brightness(0.95)', values: { contrast: 105, saturate: 130, brightness: 95 } },
  { name: 'Aden', css: 'hue-rotate(-20deg) contrast(0.9) saturate(0.85) brightness(1.2)', values: { contrast: 90, saturate: 85, brightness: 120 } },
  { name: 'Perpetua', css: 'contrast(1.1) brightness(1.05) saturate(1.1)', values: { contrast: 110, brightness: 105, saturate: 110 } },
  { name: 'Vintage', css: 'sepia(0.4) contrast(1.1) brightness(0.9) saturate(0.8)', values: { sepia: 40, contrast: 110, brightness: 90, saturate: 80 } },
  { name: 'Dramatic', css: 'contrast(1.5) brightness(0.85) saturate(0.6)', values: { contrast: 150, brightness: 85, saturate: 60 } },
  { name: 'Warm', css: 'sepia(0.15) saturate(1.4) brightness(1.05)', values: { sepia: 15, saturate: 140, brightness: 105 } },
  { name: 'Cool', css: 'saturate(0.8) brightness(1.1) hue-rotate(10deg)', values: { saturate: 80, brightness: 110 } },
];

export default function PhotoEditor({ imageUrl, onSave, onCancel }: PhotoEditorProps) {
  const [selectedFilter, setSelectedFilter] = useState(0);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [saturate, setSaturate] = useState(100);
  const [blur, setBlur] = useState(0);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState<'filters' | 'adjust'>('filters');
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  const getFilterCSS = useCallback(() => {
    if (tab === 'adjust' || selectedFilter === 0) {
      return `brightness(${brightness / 100}) contrast(${contrast / 100}) saturate(${saturate / 100}) blur(${blur}px)`;
    }
    return FILTERS[selectedFilter].css + (blur > 0 ? ` blur(${blur}px)` : '');
  }, [selectedFilter, brightness, contrast, saturate, blur, tab]);

  const handleSave = async () => {
    setSaving(true);
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img) return;

    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.filter = getFilterCSS();
    ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);

    canvas.toBlob((blob) => {
      if (blob) {
        onSave(blob, FILTERS[selectedFilter].name);
      }
      setSaving(false);
    }, 'image/jpeg', 0.92);
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <button onClick={onCancel} className="text-gray-500 hover:text-gray-700 font-medium text-sm">Cancel</button>
          <h2 className="font-semibold">Edit Photo</h2>
          <button onClick={handleSave} disabled={saving} className="text-primary-600 hover:text-primary-700 font-semibold text-sm disabled:opacity-50">
            {saving ? 'Saving...' : 'Apply'}
          </button>
        </div>

        {/* Image Preview */}
        <div className="flex-1 flex items-center justify-center bg-gray-900 p-4 min-h-0">
          <img
            ref={imgRef}
            src={imageUrl}
            alt="Edit preview"
            crossOrigin="anonymous"
            className="max-w-full max-h-[50vh] object-contain"
            style={{ filter: getFilterCSS() }}
          />
          <canvas ref={canvasRef} className="hidden" />
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => setTab('filters')}
            className={`flex-1 py-3 text-sm font-medium ${tab === 'filters' ? 'text-primary-600 border-b-2 border-primary-600' : 'text-gray-500'}`}
          >
            Filters
          </button>
          <button
            onClick={() => setTab('adjust')}
            className={`flex-1 py-3 text-sm font-medium ${tab === 'adjust' ? 'text-primary-600 border-b-2 border-primary-600' : 'text-gray-500'}`}
          >
            Adjust
          </button>
        </div>

        {/* Controls */}
        <div className="p-4 overflow-x-auto">
          {tab === 'filters' ? (
            <div className="flex gap-3 pb-2">
              {FILTERS.map((filter, i) => (
                <button
                  key={filter.name}
                  onClick={() => { setSelectedFilter(i); setBrightness(100); setContrast(100); setSaturate(100); }}
                  className={`flex-shrink-0 text-center ${selectedFilter === i ? 'ring-2 ring-primary-500 rounded-lg' : ''}`}
                >
                  <div className="w-16 h-16 rounded-lg overflow-hidden mb-1 bg-gray-200">
                    <img
                      src={imageUrl}
                      alt={filter.name}
                      className="w-full h-full object-cover"
                      style={{ filter: filter.css }}
                    />
                  </div>
                  <span className={`text-xs ${selectedFilter === i ? 'text-primary-600 font-semibold' : 'text-gray-500'}`}>{filter.name}</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="space-y-4 max-w-md mx-auto">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Brightness</span>
                  <span className="text-gray-400">{brightness}%</span>
                </div>
                <input type="range" min="20" max="200" value={brightness} onChange={(e) => setBrightness(Number(e.target.value))} className="w-full accent-primary-600" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Contrast</span>
                  <span className="text-gray-400">{contrast}%</span>
                </div>
                <input type="range" min="20" max="200" value={contrast} onChange={(e) => setContrast(Number(e.target.value))} className="w-full accent-primary-600" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Saturation</span>
                  <span className="text-gray-400">{saturate}%</span>
                </div>
                <input type="range" min="0" max="200" value={saturate} onChange={(e) => setSaturate(Number(e.target.value))} className="w-full accent-primary-600" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Blur</span>
                  <span className="text-gray-400">{blur}px</span>
                </div>
                <input type="range" min="0" max="20" value={blur} onChange={(e) => setBlur(Number(e.target.value))} className="w-full accent-primary-600" />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
