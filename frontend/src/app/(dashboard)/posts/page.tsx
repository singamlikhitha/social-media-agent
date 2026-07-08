'use client';

import { useEffect, useState, useRef } from 'react';
import { apiFetch } from '@/lib/api';
import PhotoEditor from '@/components/PhotoEditor';
import MusicSelector from '@/components/MusicSelector';

interface Post {
  id: number;
  platform: string;
  post_type: string;
  content_text: string;
  media_urls: string[] | null;
  scheduled_time: string;
  status: string;
  error_message: string | null;
  platform_post_id: string | null;
  created_at: string;
  updated_at: string | null;
}

interface UploadedFile {
  url: string;
  filename: string;
  size: number;
  content_type: string;
}

interface MusicTrack {
  id: string;
  name: string;
  artist: string;
  category: string;
  file?: File;
  isCustom?: boolean;
}

const STATUS_TABS = [
  { key: 'all', label: 'All' },
  { key: 'scheduled', label: 'Scheduled' },
  { key: 'publishing', label: 'In Progress' },
  { key: 'published', label: 'Published' },
  { key: 'failed', label: 'Failed' },
  { key: 'draft', label: 'Drafts' },
];

export default function PostsPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [manualUrl, setManualUrl] = useState('');
  const [form, setForm] = useState({ platform: 'instagram', post_type: 'image', content_text: '', scheduled_time: '' });
  const [selectedMusic, setSelectedMusic] = useState<MusicTrack | null>(null);
  const [editingImageIndex, setEditingImageIndex] = useState<number | null>(null);
  const [showAIGenerator, setShowAIGenerator] = useState(false);
  const [showAIVideoGenerator, setShowAIVideoGenerator] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiStyle, setAiStyle] = useState('photorealistic');
  const [generatingImage, setGeneratingImage] = useState(false);
  const [aiVideoPrompt, setAiVideoPrompt] = useState('');
  const [aiVideoStyle, setAiVideoStyle] = useState('cinematic');
  const [aiVideoDuration, setAiVideoDuration] = useState(5);
  const [generatingVideo, setGeneratingVideo] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [expandedPost, setExpandedPost] = useState<number | null>(null);
  const [connectedPlatforms, setConnectedPlatforms] = useState<string[]>([]);
  const [successMessage, setSuccessMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchPosts = () => {
    apiFetch('/api/posts')
      .then(setPosts)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const fetchConnectedAccounts = () => {
    apiFetch('/api/oauth/accounts')
      .then((accounts: any[]) => {
        setConnectedPlatforms(accounts.map((a) => a.platform));
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetchPosts();
    fetchConnectedAccounts();
    // Poll every 15 seconds for status updates
    const interval = setInterval(fetchPosts, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    try {
      for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i]);

        const token = localStorage.getItem('access_token') || '';
        const res = await fetch('/api/media/upload', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
          alert(`Failed to upload ${files[i].name}: ${err.detail}`);
          continue;
        }

        const data: UploadedFile = await res.json();
        setUploadedFiles((prev) => [...prev, data]);
      }
    } catch (err: any) {
      alert(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleEditedImageSave = async (blob: Blob, filterName: string) => {
    if (editingImageIndex === null) return;

    const formData = new FormData();
    formData.append('file', blob, `edited-${filterName.toLowerCase()}.jpg`);

    const token = localStorage.getItem('access_token') || '';
    const res = await fetch('/api/media/upload', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData,
    });

    if (res.ok) {
      const data: UploadedFile = await res.json();
      setUploadedFiles((prev) => {
        const updated = [...prev];
        updated[editingImageIndex] = data;
        return updated;
      });
    }
    setEditingImageIndex(null);
  };

  const generateAIImage = async () => {
    if (!aiPrompt.trim()) return;
    setGeneratingImage(true);
    try {
      const data = await apiFetch('/api/content/generate-image', {
        method: 'POST',
        body: JSON.stringify({ prompt: aiPrompt, style: aiStyle }),
      });
      if (data.url) {
        setUploadedFiles((prev) => [...prev, {
          url: data.url,
          filename: data.filename || 'ai-generated.png',
          size: data.size || 0,
          content_type: 'image/png',
        }]);
        setShowAIGenerator(false);
        setAiPrompt('');
      }
    } catch (err: any) {
      alert(err.message || 'Image generation failed');
    } finally {
      setGeneratingImage(false);
    }
  };

  const generateAIVideo = async () => {
    if (!aiVideoPrompt.trim()) return;
    setGeneratingVideo(true);
    try {
      const data = await apiFetch('/api/content/generate-video', {
        method: 'POST',
        body: JSON.stringify({ prompt: aiVideoPrompt, style: aiVideoStyle, duration: aiVideoDuration }),
      });
      if (data.url) {
        setUploadedFiles((prev) => [...prev, {
          url: data.url,
          filename: data.filename || 'ai-generated.mp4',
          size: data.size || 0,
          content_type: 'video/mp4',
        }]);
        setShowAIVideoGenerator(false);
        setAiVideoPrompt('');
      }
    } catch (err: any) {
      alert(err.message || 'Video generation failed');
    } finally {
      setGeneratingVideo(false);
    }
  };

  const addManualUrl = () => {
    if (!manualUrl.trim()) return;
    setUploadedFiles((prev) => [...prev, { url: manualUrl.trim(), filename: manualUrl.trim(), size: 0, content_type: '' }]);
    setManualUrl('');
  };

  const removeFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return 'URL';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const createPost = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const mediaUrls = uploadedFiles.map((f) => f.url);
      const metadata: Record<string, any> = {};
      if (selectedMusic) {
        metadata.music = { id: selectedMusic.id, name: selectedMusic.name, artist: selectedMusic.artist };
      }
      const body = {
        ...form,
        media_urls: mediaUrls.length > 0 ? mediaUrls : null,
        scheduled_time: new Date(form.scheduled_time).toISOString(),
        metadata: Object.keys(metadata).length > 0 ? metadata : null,
      };
      await apiFetch('/api/posts', { method: 'POST', body: JSON.stringify(body) });
      showSuccess(`Your ${form.post_type} has been scheduled for ${form.platform}! It will be automatically published at the set time.`);
      setShowCreate(false);
      setUploadedFiles([]);
      setManualUrl('');
      setSelectedMusic(null);
      fetchPosts();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const showSuccess = (msg: string) => {
    setSuccessMessage(msg);
    setTimeout(() => setSuccessMessage(''), 5000);
  };

  const publishNow = async (postId: number) => {
    try {
      const result = await apiFetch(`/api/posts/${postId}/publish-now`, { method: 'POST' });
      const postType = result.post_type || 'post';
      const platform = result.platform || '';
      showSuccess(`Your ${postType} has been successfully published to ${platform}!`);
      fetchPosts();
    } catch (err: any) {
      alert(err.message || 'Failed to publish');
    }
  };

  const retryPost = async (postId: number) => {
    try {
      await apiFetch(`/api/posts/${postId}`, {
        method: 'PUT',
        body: JSON.stringify({ status: 'scheduled' }),
      });
      await apiFetch(`/api/posts/${postId}/publish-now`, { method: 'POST' });
      fetchPosts();
    } catch (err: any) {
      alert(err.message || 'Failed to retry');
    }
  };

  const deletePost = async (postId: number) => {
    if (!confirm('Are you sure you want to delete this post?')) return;
    try {
      await apiFetch(`/api/posts/${postId}`, { method: 'DELETE' });
      fetchPosts();
    } catch (err: any) {
      alert(err.message || 'Failed to delete');
    }
  };

  const filteredPosts = statusFilter === 'all' ? posts : posts.filter((p) => p.status === statusFilter);

  const statusCounts = posts.reduce((acc, p) => {
    acc[p.status] = (acc[p.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const statusColors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-800',
    scheduled: 'bg-yellow-100 text-yellow-800',
    publishing: 'bg-blue-100 text-blue-800',
    published: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  const postTypesByPlatform: Record<string, string[]> = {
    instagram: ['image', 'carousel', 'reel', 'story'],
    youtube: ['video', 'short'],
    facebook: ['text', 'image', 'video', 'link'],
    twitter: ['tweet', 'thread'],
    linkedin: ['text', 'image', 'article'],
  };

  const isImageFile = (file: UploadedFile) => {
    return file.content_type?.startsWith('image') || /\.(jpg|jpeg|png|gif|webp)$/i.test(file.filename);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Posts</h1>
          <p className="text-gray-500">Create and manage your scheduled posts</p>
        </div>
        <button onClick={() => { setShowCreate(!showCreate); if (showCreate) { setUploadedFiles([]); setManualUrl(''); setSelectedMusic(null); } }} className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 font-medium text-sm">
          {showCreate ? 'Cancel' : 'Create Post'}
        </button>
      </div>

      {/* Success Message Toast */}
      {successMessage && (
        <div className="mb-6 flex items-center gap-3 px-5 py-4 bg-green-50 border border-green-200 rounded-xl animate-in fade-in">
          <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
          </div>
          <p className="text-sm font-medium text-green-800">{successMessage}</p>
          <button onClick={() => setSuccessMessage('')} className="ml-auto text-green-600 hover:text-green-800">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      )}

      {showCreate && (
        <form onSubmit={createPost} className="bg-white rounded-xl border border-gray-200 p-6 mb-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Platform</label>
              <select value={form.platform} onChange={(e) => setForm({ ...form, platform: e.target.value, post_type: postTypesByPlatform[e.target.value]?.[0] || 'image' })} className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                <option value="instagram">Instagram</option>
                <option value="youtube">YouTube</option>
                <option value="facebook">Facebook</option>
                <option value="twitter">Twitter</option>
                <option value="linkedin">LinkedIn</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Post Type</label>
              <select value={form.post_type} onChange={(e) => setForm({ ...form, post_type: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                {(postTypesByPlatform[form.platform] || ['image']).map((type) => (
                  <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Connected account warning */}
          {!connectedPlatforms.includes(form.platform) && (
            <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-sm">
              <svg className="w-5 h-5 text-amber-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
              <div>
                <p className="font-medium text-amber-800">No {form.platform} account connected</p>
                <p className="text-amber-600">Go to <a href="/accounts" className="underline font-medium">Accounts</a> to connect your {form.platform} account before scheduling.</p>
              </div>
            </div>
          )}

          {connectedPlatforms.includes(form.platform) && (
            <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg text-sm">
              <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
              <span className="text-green-700">Your {form.platform} account is connected and ready to post</span>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
            <textarea value={form.content_text} onChange={(e) => setForm({ ...form, content_text: e.target.value })} rows={4} className="w-full px-3 py-2 border border-gray-300 rounded-lg" placeholder="Write your caption..." required />
          </div>

          {/* Media Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Media</label>
            {form.platform === 'youtube' && (
              <p className="text-sm text-amber-600 mb-2">YouTube requires a video file (MP4, MOV, AVI, etc.). Image files are not supported.</p>
            )}

            {/* Uploaded files with edit buttons */}
            {uploadedFiles.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-3">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="relative group border border-gray-200 rounded-lg overflow-hidden">
                    {isImageFile(file) ? (
                      <img src={file.url} alt={file.filename} className="w-full h-32 object-cover" />
                    ) : (
                      <div className="w-full h-32 bg-gray-100 flex flex-col items-center justify-center">
                        <span className="text-2xl mb-1">{file.content_type?.startsWith('video') ? '🎬' : file.content_type?.startsWith('audio') ? '🎵' : '📄'}</span>
                        <span className="text-xs text-gray-500 truncate px-2 max-w-full">{file.filename}</span>
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
                      {isImageFile(file) && (
                        <button
                          type="button"
                          onClick={() => setEditingImageIndex(index)}
                          className="bg-white text-gray-800 px-2.5 py-1.5 rounded-lg text-xs font-medium hover:bg-gray-100"
                        >
                          Edit
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="bg-red-500 text-white px-2.5 py-1.5 rounded-lg text-xs font-medium hover:bg-red-600"
                      >
                        Remove
                      </button>
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs px-2 py-1 truncate">
                      {formatFileSize(file.size)}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Action buttons */}
            <div className="flex flex-wrap gap-2">
              <div>
                <input ref={fileInputRef} type="file" multiple accept={form.platform === 'youtube' ? 'video/*' : 'image/*,video/*,audio/*'} onChange={handleFileUpload} className="hidden" id="file-upload" />
                <label htmlFor="file-upload" className={`inline-flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 text-sm ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
                  <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                  {uploading ? 'Uploading...' : 'Upload Files'}
                </label>
              </div>

              <button
                type="button"
                onClick={() => setShowAIGenerator(!showAIGenerator)}
                className="inline-flex items-center gap-2 px-3 py-2 border border-purple-300 text-purple-700 rounded-lg hover:bg-purple-50 text-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                AI Generate Image
              </button>
              <button
                type="button"
                onClick={() => setShowAIVideoGenerator(!showAIVideoGenerator)}
                className="inline-flex items-center gap-2 px-3 py-2 border border-indigo-300 text-indigo-700 rounded-lg hover:bg-indigo-50 text-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                AI Generate Video
              </button>
            </div>

            {/* AI Image Generator */}
            {showAIGenerator && (
              <div className="mt-3 p-4 border border-purple-200 rounded-lg bg-purple-50/50">
                <h4 className="font-medium text-sm text-purple-800 mb-3">Generate Image with AI</h4>
                <div className="space-y-3">
                  <textarea
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    placeholder="Describe the image you want... (e.g., 'A cozy coffee shop with warm lighting and latte art, trending aesthetic')"
                    rows={2}
                    className="w-full px-3 py-2 border border-purple-200 rounded-lg text-sm bg-white"
                  />
                  <div className="flex gap-2 items-end">
                    <div className="flex-1">
                      <label className="block text-xs text-purple-600 mb-1">Style</label>
                      <select value={aiStyle} onChange={(e) => setAiStyle(e.target.value)} className="w-full px-3 py-2 border border-purple-200 rounded-lg text-sm bg-white">
                        <option value="photorealistic">Photorealistic</option>
                        <option value="cartoon">Cartoon / Illustration</option>
                        <option value="watercolor">Watercolor</option>
                        <option value="minimalist">Minimalist</option>
                        <option value="3d-render">3D Render</option>
                        <option value="anime">Anime</option>
                        <option value="oil-painting">Oil Painting</option>
                        <option value="digital-art">Digital Art</option>
                        <option value="trending-aesthetic">Trending Aesthetic</option>
                        <option value="flat-design">Flat Design</option>
                      </select>
                    </div>
                    <button
                      type="button"
                      onClick={generateAIImage}
                      disabled={generatingImage || !aiPrompt.trim()}
                      className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 text-sm font-medium"
                    >
                      {generatingImage ? 'Generating...' : 'Generate'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* AI Video Generator */}
            {showAIVideoGenerator && (
              <div className="mt-3 p-4 border border-indigo-200 rounded-lg bg-indigo-50/50">
                <h4 className="font-medium text-sm text-indigo-800 mb-3">Generate Video with AI</h4>
                <div className="space-y-3">
                  <textarea
                    value={aiVideoPrompt}
                    onChange={(e) => setAiVideoPrompt(e.target.value)}
                    placeholder="Describe the video you want... (e.g., 'A drone flying over a sunset beach with waves crashing')"
                    rows={2}
                    className="w-full px-3 py-2 border border-indigo-200 rounded-lg text-sm bg-white"
                  />
                  <div className="flex gap-2 items-end">
                    <div className="flex-1">
                      <label className="block text-xs text-indigo-600 mb-1">Style</label>
                      <select value={aiVideoStyle} onChange={(e) => setAiVideoStyle(e.target.value)} className="w-full px-3 py-2 border border-indigo-200 rounded-lg text-sm bg-white">
                        <option value="cinematic">Cinematic</option>
                        <option value="realistic">Realistic</option>
                        <option value="animated">Animated</option>
                        <option value="slow-motion">Slow Motion</option>
                        <option value="timelapse">Timelapse</option>
                        <option value="vlog">Vlog Style</option>
                        <option value="music-video">Music Video</option>
                        <option value="product-showcase">Product Showcase</option>
                        <option value="tutorial">Tutorial</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-indigo-600 mb-1">Duration</label>
                      <select value={aiVideoDuration} onChange={(e) => setAiVideoDuration(Number(e.target.value))} className="w-full px-3 py-2 border border-indigo-200 rounded-lg text-sm bg-white">
                        <option value={5}>5 sec</option>
                        <option value={8}>8 sec</option>
                        <option value={10}>10 sec</option>
                      </select>
                    </div>
                    <button
                      type="button"
                      onClick={generateAIVideo}
                      disabled={generatingVideo || !aiVideoPrompt.trim()}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 text-sm font-medium whitespace-nowrap"
                    >
                      {generatingVideo ? 'Generating...' : 'Generate Video'}
                    </button>
                  </div>
                  {generatingVideo && (
                    <div className="flex items-center gap-2 text-xs text-indigo-600">
                      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>
                      Video generation can take 1-5 minutes. Please wait...
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Manual URL */}
            <div className="flex gap-2 mt-3">
              <input type="url" value={manualUrl} onChange={(e) => setManualUrl(e.target.value)} className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm" placeholder="Or paste a media URL..." onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addManualUrl(); } }} />
              <button type="button" onClick={addManualUrl} className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium">Add URL</button>
            </div>

            <p className="text-xs text-gray-400 mt-1.5">Supports images (JPG, PNG, GIF, WebP), videos (MP4, MOV, WebM), and audio. Max 100MB per file.</p>
          </div>

          {/* Music Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Music</label>
            <MusicSelector onSelect={setSelectedMusic} selectedTrack={selectedMusic} />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Scheduled Time</label>
            <input type="datetime-local" value={form.scheduled_time} onChange={(e) => setForm({ ...form, scheduled_time: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg" required />
          </div>

          <button type="submit" className="bg-primary-600 text-white px-6 py-2.5 rounded-lg hover:bg-primary-700 font-medium text-sm">Schedule Post</button>
        </form>
      )}

      {/* Photo Editor Modal */}
      {editingImageIndex !== null && uploadedFiles[editingImageIndex] && (
        <PhotoEditor
          imageUrl={uploadedFiles[editingImageIndex].url}
          onSave={handleEditedImageSave}
          onCancel={() => setEditingImageIndex(null)}
        />
      )}

      {/* Status Overview */}
      {!loading && posts.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
          {[
            { key: 'scheduled', label: 'Scheduled', icon: '🕐', color: 'bg-yellow-50 border-yellow-200 text-yellow-800' },
            { key: 'publishing', label: 'In Progress', icon: '⏳', color: 'bg-blue-50 border-blue-200 text-blue-800' },
            { key: 'published', label: 'Published', icon: '✅', color: 'bg-green-50 border-green-200 text-green-800' },
            { key: 'failed', label: 'Failed', icon: '❌', color: 'bg-red-50 border-red-200 text-red-800' },
            { key: 'draft', label: 'Drafts', icon: '📝', color: 'bg-gray-50 border-gray-200 text-gray-800' },
          ].map((s) => (
            <button
              key={s.key}
              onClick={() => setStatusFilter(statusFilter === s.key ? 'all' : s.key)}
              className={`p-3 rounded-xl border text-center transition-all ${statusFilter === s.key ? s.color + ' ring-2 ring-offset-1 ring-current' : 'bg-white border-gray-200 hover:bg-gray-50'}`}
            >
              <div className="text-xl mb-1">{s.icon}</div>
              <div className="text-2xl font-bold">{statusCounts[s.key] || 0}</div>
              <div className="text-xs font-medium">{s.label}</div>
            </button>
          ))}
        </div>
      )}

      {/* Filter Tabs */}
      {!loading && posts.length > 0 && (
        <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1 w-fit">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                statusFilter === tab.key ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
              {tab.key !== 'all' && statusCounts[tab.key] ? ` (${statusCounts[tab.key]})` : tab.key === 'all' ? ` (${posts.length})` : ''}
            </button>
          ))}
        </div>
      )}

      {/* Posts List */}
      <div className="bg-white rounded-xl border border-gray-200">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading posts...</div>
        ) : posts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No posts yet. Create your first one!</div>
        ) : filteredPosts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No {statusFilter} posts found.</div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredPosts.map((post) => (
              <div key={post.id} className="hover:bg-gray-50 transition-colors">
                <div
                  className="p-4 flex items-start gap-4 cursor-pointer"
                  onClick={() => setExpandedPost(expandedPost === post.id ? null : post.id)}
                >
                  {/* Thumbnail */}
                  {post.media_urls && post.media_urls.length > 0 && (
                    <div className="w-16 h-16 rounded-lg overflow-hidden flex-shrink-0 bg-gray-100">
                      <img src={post.media_urls[0]} alt="" className="w-full h-full object-cover" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                    </div>
                  )}

                  {/* Status icon */}
                  <div className="flex-shrink-0 mt-1">
                    {post.status === 'published' && (
                      <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                        <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                      </div>
                    )}
                    {post.status === 'scheduled' && (
                      <div className="w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center">
                        <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      </div>
                    )}
                    {post.status === 'publishing' && (
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center animate-pulse">
                        <svg className="w-4 h-4 text-blue-600 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                      </div>
                    )}
                    {post.status === 'failed' && (
                      <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                        <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                      </div>
                    )}
                    {post.status === 'draft' && (
                      <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                        <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium px-2 py-0.5 bg-gray-100 rounded capitalize">{post.platform}</span>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${statusColors[post.status] || ''}`}>
                        {post.status === 'publishing' ? 'In Progress' : post.status}
                      </span>
                      <span className="text-xs text-gray-400">{post.post_type}</span>
                      {post.media_urls && post.media_urls.length > 0 && (
                        <span className="text-xs text-gray-400">{post.media_urls.length} media</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-800 line-clamp-2">{post.content_text}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <p className="text-xs text-gray-400">
                        {post.status === 'published' ? 'Published' : 'Scheduled'}: {new Date(post.scheduled_time).toLocaleString()}
                      </p>
                      {post.status === 'published' && post.platform_post_id && (
                        <span className="text-xs text-green-600 font-medium">ID: {post.platform_post_id}</span>
                      )}
                    </div>

                    {/* Error message inline for failed posts */}
                    {post.status === 'failed' && post.error_message && (
                      <div className="mt-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-xs text-red-700 font-medium">Error: {post.error_message}</p>
                      </div>
                    )}
                  </div>

                  {/* Expand arrow */}
                  <svg className={`w-5 h-5 text-gray-400 flex-shrink-0 transition-transform ${expandedPost === post.id ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>

                {/* Expanded details */}
                {expandedPost === post.id && (
                  <div className="px-4 pb-4 border-t border-gray-100">
                    <div className="pt-3 grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500 text-xs">Created</span>
                        <p className="text-gray-800">{new Date(post.created_at).toLocaleString()}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 text-xs">Last Updated</span>
                        <p className="text-gray-800">{post.updated_at ? new Date(post.updated_at).toLocaleString() : 'Never'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 text-xs">Scheduled For</span>
                        <p className="text-gray-800">{new Date(post.scheduled_time).toLocaleString()}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 text-xs">Status</span>
                        <div className="flex items-center gap-1.5">
                          <span className={`inline-block w-2 h-2 rounded-full ${
                            post.status === 'published' ? 'bg-green-500' :
                            post.status === 'scheduled' ? 'bg-yellow-500' :
                            post.status === 'publishing' ? 'bg-blue-500 animate-pulse' :
                            post.status === 'failed' ? 'bg-red-500' : 'bg-gray-400'
                          }`} />
                          <p className="text-gray-800 capitalize">{post.status === 'publishing' ? 'In Progress' : post.status}</p>
                        </div>
                      </div>
                      {post.platform_post_id && (
                        <div className="col-span-2">
                          <span className="text-gray-500 text-xs">Platform Post ID</span>
                          <p className="text-gray-800 font-mono text-xs">{post.platform_post_id}</p>
                        </div>
                      )}
                      {post.error_message && (
                        <div className="col-span-2">
                          <span className="text-gray-500 text-xs">Error Details</span>
                          <p className="text-red-700 bg-red-50 px-3 py-2 rounded-lg text-xs mt-1">{post.error_message}</p>
                        </div>
                      )}
                    </div>

                    {/* Action buttons */}
                    <div className="flex gap-2 mt-4 pt-3 border-t border-gray-100">
                      {post.status === 'scheduled' && (
                        <button
                          onClick={(e) => { e.stopPropagation(); publishNow(post.id); }}
                          className="px-3 py-1.5 bg-primary-600 text-white rounded-lg text-xs font-medium hover:bg-primary-700"
                        >
                          Publish Now
                        </button>
                      )}
                      {post.status === 'failed' && (
                        <button
                          onClick={(e) => { e.stopPropagation(); retryPost(post.id); }}
                          className="px-3 py-1.5 bg-orange-500 text-white rounded-lg text-xs font-medium hover:bg-orange-600"
                        >
                          Retry
                        </button>
                      )}
                      {(post.status === 'draft' || post.status === 'scheduled') && (
                        <button
                          onClick={(e) => { e.stopPropagation(); deletePost(post.id); }}
                          className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg text-xs font-medium hover:bg-red-200"
                        >
                          Delete
                        </button>
                      )}
                      <button
                        onClick={(e) => { e.stopPropagation(); fetchPosts(); }}
                        className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-xs font-medium hover:bg-gray-200"
                      >
                        Refresh Status
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
