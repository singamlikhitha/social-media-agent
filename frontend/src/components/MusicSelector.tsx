'use client';

import { useState, useRef } from 'react';

interface MusicTrack {
  id: string;
  name: string;
  artist: string;
  category: string;
  url?: string;
  file?: File;
  isCustom?: boolean;
}

interface MusicSelectorProps {
  onSelect: (track: MusicTrack | null) => void;
  selectedTrack: MusicTrack | null;
}

const STOCK_MUSIC: MusicTrack[] = [
  { id: 'upbeat-1', name: 'Happy Vibes', artist: 'Stock Audio', category: 'Upbeat' },
  { id: 'upbeat-2', name: 'Good Morning', artist: 'Stock Audio', category: 'Upbeat' },
  { id: 'upbeat-3', name: 'Feel Good', artist: 'Stock Audio', category: 'Upbeat' },
  { id: 'chill-1', name: 'Lo-Fi Dreams', artist: 'Stock Audio', category: 'Chill' },
  { id: 'chill-2', name: 'Sunday Morning', artist: 'Stock Audio', category: 'Chill' },
  { id: 'chill-3', name: 'Sunset Drive', artist: 'Stock Audio', category: 'Chill' },
  { id: 'energetic-1', name: 'Power Up', artist: 'Stock Audio', category: 'Energetic' },
  { id: 'energetic-2', name: 'Unstoppable', artist: 'Stock Audio', category: 'Energetic' },
  { id: 'cinematic-1', name: 'Epic Moment', artist: 'Stock Audio', category: 'Cinematic' },
  { id: 'cinematic-2', name: 'Emotional Journey', artist: 'Stock Audio', category: 'Cinematic' },
  { id: 'trending-1', name: 'Viral Beat 2026', artist: 'Trending', category: 'Trending' },
  { id: 'trending-2', name: 'TikTok Hit', artist: 'Trending', category: 'Trending' },
  { id: 'trending-3', name: 'Reel Anthem', artist: 'Trending', category: 'Trending' },
];

const CATEGORIES = ['All', 'Trending', 'Upbeat', 'Chill', 'Energetic', 'Cinematic', 'My Music'];

export default function MusicSelector({ onSelect, selectedTrack }: MusicSelectorProps) {
  const [category, setCategory] = useState('All');
  const [search, setSearch] = useState('');
  const [customTracks, setCustomTracks] = useState<MusicTrack[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const track: MusicTrack = {
      id: `custom-${Date.now()}`,
      name: file.name.replace(/\.[^/.]+$/, ''),
      artist: 'My Music',
      category: 'My Music',
      file,
      isCustom: true,
    };
    setCustomTracks((prev) => [...prev, track]);
    onSelect(track);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const allTracks = [...STOCK_MUSIC, ...customTracks];
  const filteredTracks = allTracks.filter((t) => {
    const matchesCategory = category === 'All' || t.category === category;
    const matchesSearch = !search || t.name.toLowerCase().includes(search.toLowerCase()) || t.artist.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  if (!isOpen) {
    return (
      <div className="flex items-center gap-2">
        <div
          role="button"
          tabIndex={0}
          onClick={() => setIsOpen(true)}
          onKeyDown={(e) => { if (e.key === 'Enter') setIsOpen(true); }}
          className="flex-1 flex items-center gap-2 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm cursor-pointer"
        >
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
          </svg>
          {selectedTrack ? (
            <span className="flex-1 text-left">
              <span className="font-medium">{selectedTrack.name}</span>
              <span className="text-gray-400 ml-1">- {selectedTrack.artist}</span>
            </span>
          ) : (
            <span className="flex-1 text-left text-gray-500">Add Music</span>
          )}
        </div>
        {selectedTrack && (
          <button
            type="button"
            onClick={() => onSelect(null)}
            className="text-red-400 hover:text-red-600 text-xs font-medium px-2 py-1"
          >
            Remove
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b">
        <h3 className="font-medium text-sm">Select Music</h3>
        <button type="button" onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-gray-600 text-sm">Close</button>
      </div>

      {/* Search & Upload */}
      <div className="p-3 border-b space-y-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search music..."
          className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
        />
        <div>
          <input ref={fileInputRef} type="file" accept="audio/*" onChange={handleFileUpload} className="hidden" id="music-upload" />
          <label htmlFor="music-upload" className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-lg cursor-pointer hover:bg-gray-200 text-xs font-medium text-gray-600">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Upload Your Music
          </label>
        </div>
      </div>

      {/* Categories */}
      <div className="flex gap-1 px-3 py-2 overflow-x-auto border-b">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setCategory(cat)}
            className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${category === cat ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Track List */}
      <div className="max-h-48 overflow-y-auto">
        {filteredTracks.length === 0 ? (
          <div className="p-4 text-center text-gray-400 text-sm">No tracks found</div>
        ) : (
          filteredTracks.map((track) => (
            <button
              key={track.id}
              type="button"
              onClick={() => { onSelect(track); setIsOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 text-left ${selectedTrack?.id === track.id ? 'bg-primary-50' : ''}`}
            >
              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{track.name}</p>
                <p className="text-xs text-gray-400">{track.artist}</p>
              </div>
              <span className="text-xs text-gray-300 bg-gray-50 px-2 py-0.5 rounded">{track.category}</span>
              {selectedTrack?.id === track.id && (
                <svg className="w-4 h-4 text-primary-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))
        )}
      </div>
    </div>
  );
}
