'use client';

import { useState } from 'react';
import { apiFetch } from '@/lib/api';

interface ContentIdea {
  id: number;
  platform: string;
  topic: string;
  content_type: string;
  content_suggestion: string;
  hashtags: string;
  used: boolean;
}

interface CreatedContent {
  title: string;
  caption: string;
  hashtags: string[];
  hook: string;
  cta: string;
  media_suggestion: string;
  posting_tip: string;
}

interface ModifiedContent {
  modified_content: string;
  hashtags: string[];
  changes_made: string[];
  engagement_score: number;
}

export default function ContentPage() {
  const [ideas, setIdeas] = useState<ContentIdea[]>([]);
  const [loading, setLoading] = useState(false);
  const [platform, setPlatform] = useState('instagram');
  const [niche, setNiche] = useState('');
  const [optimizeText, setOptimizeText] = useState('');
  const [optimizedResult, setOptimizedResult] = useState<{ optimized: string; improvements: string[] } | null>(null);

  // Content Creator state
  const [contentTopic, setContentTopic] = useState('');
  const [contentType, setContentType] = useState('post');
  const [contentTone, setContentTone] = useState('engaging');
  const [createdContent, setCreatedContent] = useState<CreatedContent | null>(null);
  const [contentLoading, setContentLoading] = useState(false);

  // Content Modifier state
  const [originalContent, setOriginalContent] = useState('');
  const [modifyInstruction, setModifyInstruction] = useState('improve engagement');
  const [modifiedContent, setModifiedContent] = useState<ModifiedContent | null>(null);
  const [modifyLoading, setModifyLoading] = useState(false);

  // Schedule & Publish state
  const [scheduleTime, setScheduleTime] = useState('');
  const [schedulePlatforms, setSchedulePlatforms] = useState<string[]>([]);
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [scheduleSuccess, setScheduleSuccess] = useState('');

  // Active tab
  const [activeTab, setActiveTab] = useState<'create' | 'modify' | 'ideas' | 'optimize'>('create');

  const generateIdeas = async () => {
    if (!niche) return;
    setLoading(true);
    try {
      const data = await apiFetch('/api/content/generate-ideas', {
        method: 'POST',
        body: JSON.stringify({ platform, niche, count: 5 }),
      });
      setIdeas(data);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const optimizeCaption = async () => {
    if (!optimizeText) return;
    setLoading(true);
    try {
      const data = await apiFetch('/api/content/optimize-caption', {
        method: 'POST',
        body: JSON.stringify({ platform, draft_caption: optimizeText }),
      });
      setOptimizedResult(data);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const createContent = async () => {
    if (!contentTopic) return;
    setContentLoading(true);
    setCreatedContent(null);
    try {
      const data = await apiFetch('/api/content/create-content', {
        method: 'POST',
        body: JSON.stringify({
          platform,
          topic: contentTopic,
          content_type: contentType,
          tone: contentTone,
        }),
      });
      setCreatedContent(data);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setContentLoading(false);
    }
  };

  const modifyContent = async () => {
    if (!originalContent) return;
    setModifyLoading(true);
    setModifiedContent(null);
    try {
      const data = await apiFetch('/api/content/modify-content', {
        method: 'POST',
        body: JSON.stringify({
          platform,
          original_content: originalContent,
          instruction: modifyInstruction,
        }),
      });
      setModifiedContent(data);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setModifyLoading(false);
    }
  };

  const toggleSchedulePlatform = (p: string) => {
    setSchedulePlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
    );
  };

  const scheduleAndPublish = async (contentText: string, hashtags: string[]) => {
    if (!scheduleTime || schedulePlatforms.length === 0) {
      alert('Please select at least one platform and set a schedule time.');
      return;
    }
    setScheduleLoading(true);
    setScheduleSuccess('');
    try {
      const results: string[] = [];
      for (const p of schedulePlatforms) {
        const data = await apiFetch('/api/posts', {
          method: 'POST',
          body: JSON.stringify({
            platform: p,
            post_type: contentType === 'post' ? 'image' : contentType,
            content_text: contentText,
            hashtags: hashtags,
            scheduled_time: new Date(scheduleTime).toISOString(),
          }),
        });
        results.push(`${p}: Post #${data.id} scheduled`);
      }
      setScheduleSuccess(results.join(' | '));
    } catch (err: any) {
      alert(err.message);
    } finally {
      setScheduleLoading(false);
    }
  };

  const platformOptions = ['instagram', 'youtube', 'facebook', 'twitter', 'linkedin'];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Content Studio</h1>
      <p className="text-gray-500 mb-6">AI-powered content creation, modification, and scheduling</p>

      {/* Platform selector (shared) */}
      <div className="mb-6 flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">Platform:</label>
        <select
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          <option value="instagram">Instagram</option>
          <option value="youtube">YouTube</option>
          <option value="facebook">Facebook</option>
          <option value="twitter">Twitter / X</option>
          <option value="linkedin">LinkedIn</option>
        </select>
      </div>

      {/* Tab navigation */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { key: 'create' as const, label: 'Create Content' },
          { key: 'modify' as const, label: 'Modify Content' },
          { key: 'ideas' as const, label: 'Generate Ideas' },
          { key: 'optimize' as const, label: 'Optimize Caption' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'bg-white text-primary-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab: Create Content */}
      {activeTab === 'create' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Create Content from Topic</h2>
            <p className="text-sm text-gray-500 mb-4">
              Enter a topic and AI will generate a complete, ready-to-publish post for your selected platform.
            </p>
            <div className="space-y-4">
              <input
                type="text"
                value={contentTopic}
                onChange={(e) => setContentTopic(e.target.value)}
                placeholder="Enter a topic (e.g., Benefits of morning meditation, Top 5 travel hacks)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Content Type</label>
                  <select
                    value={contentType}
                    onChange={(e) => setContentType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="post">Post</option>
                    <option value="reel">Reel / Short</option>
                    <option value="carousel">Carousel</option>
                    <option value="story">Story</option>
                    <option value="thread">Thread</option>
                    <option value="article">Article</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Tone</label>
                  <select
                    value={contentTone}
                    onChange={(e) => setContentTone(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="engaging">Engaging</option>
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="humorous">Humorous</option>
                    <option value="inspirational">Inspirational</option>
                    <option value="educational">Educational</option>
                    <option value="storytelling">Storytelling</option>
                  </select>
                </div>
              </div>
              <button
                onClick={createContent}
                disabled={contentLoading || !contentTopic}
                className="bg-primary-600 text-white px-6 py-2.5 rounded-lg hover:bg-primary-700 disabled:opacity-50 font-medium text-sm w-full"
              >
                {contentLoading ? 'Creating Content...' : 'Create Content'}
              </button>
            </div>
          </div>

          {/* Created Content Result */}
          {createdContent && (
            <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-green-700">{createdContent.title}</h3>
                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium">AI Generated</span>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs font-medium text-gray-500 mb-1">Hook</p>
                <p className="text-sm font-medium text-gray-800">{createdContent.hook}</p>
              </div>

              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Caption</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap bg-blue-50 p-4 rounded-lg">{createdContent.caption}</p>
              </div>

              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Hashtags</p>
                <div className="flex flex-wrap gap-1.5">
                  {createdContent.hashtags.map((tag, i) => (
                    <span key={i} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">#{tag}</span>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-amber-50 p-3 rounded-lg">
                  <p className="text-xs font-medium text-amber-700 mb-1">Media Suggestion</p>
                  <p className="text-sm text-amber-800">{createdContent.media_suggestion}</p>
                </div>
                <div className="bg-purple-50 p-3 rounded-lg">
                  <p className="text-xs font-medium text-purple-700 mb-1">Posting Tip</p>
                  <p className="text-sm text-purple-800">{createdContent.posting_tip}</p>
                </div>
              </div>

              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-xs font-medium text-gray-500 mb-1">Call to Action</p>
                <p className="text-sm text-gray-700">{createdContent.cta}</p>
              </div>

              {/* Schedule & Publish Section */}
              <div className="border-t pt-4 mt-4">
                <h4 className="text-md font-semibold mb-3">Schedule & Auto-Publish</h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Publish to Platforms</label>
                    <div className="flex flex-wrap gap-2">
                      {platformOptions.map((p) => (
                        <button
                          key={p}
                          onClick={() => toggleSchedulePlatform(p)}
                          className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                            schedulePlatforms.includes(p)
                              ? 'bg-primary-600 text-white border-primary-600'
                              : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
                          }`}
                        >
                          {p.charAt(0).toUpperCase() + p.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Schedule Date & Time</label>
                    <input
                      type="datetime-local"
                      value={scheduleTime}
                      onChange={(e) => setScheduleTime(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                  <button
                    onClick={() => scheduleAndPublish(createdContent.caption, createdContent.hashtags)}
                    disabled={scheduleLoading || !scheduleTime || schedulePlatforms.length === 0}
                    className="bg-green-600 text-white px-6 py-2.5 rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium text-sm w-full"
                  >
                    {scheduleLoading ? 'Scheduling...' : `Schedule to ${schedulePlatforms.length || 0} Platform(s)`}
                  </button>
                  {scheduleSuccess && (
                    <div className="bg-green-50 border border-green-200 text-green-700 p-3 rounded-lg text-sm">
                      {scheduleSuccess}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab: Modify Content */}
      {activeTab === 'modify' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Modify Your Content</h2>
            <p className="text-sm text-gray-500 mb-4">
              Paste your existing content and tell the AI how to improve it.
            </p>
            <div className="space-y-4">
              <textarea
                value={originalContent}
                onChange={(e) => setOriginalContent(e.target.value)}
                rows={5}
                placeholder="Paste your content here..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Modification Instruction</label>
                <select
                  value={modifyInstruction}
                  onChange={(e) => setModifyInstruction(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="improve engagement">Improve engagement</option>
                  <option value="make it more professional">Make it more professional</option>
                  <option value="make it shorter and punchier">Make it shorter and punchier</option>
                  <option value="add humor and personality">Add humor and personality</option>
                  <option value="make it more emotional and inspiring">Make it more emotional and inspiring</option>
                  <option value="optimize for SEO and discoverability">Optimize for SEO and discoverability</option>
                  <option value="rewrite for a different audience">Rewrite for a different audience</option>
                </select>
              </div>
              <button
                onClick={modifyContent}
                disabled={modifyLoading || !originalContent}
                className="bg-primary-600 text-white px-6 py-2.5 rounded-lg hover:bg-primary-700 disabled:opacity-50 font-medium text-sm w-full"
              >
                {modifyLoading ? 'Modifying...' : 'Modify Content'}
              </button>
            </div>
          </div>

          {/* Modified Content Result */}
          {modifiedContent && (
            <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Modified Content</h3>
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
                  Engagement Score: {modifiedContent.engagement_score}/10
                </span>
              </div>

              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Updated Content</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap bg-blue-50 p-4 rounded-lg">{modifiedContent.modified_content}</p>
              </div>

              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Hashtags</p>
                <div className="flex flex-wrap gap-1.5">
                  {modifiedContent.hashtags.map((tag, i) => (
                    <span key={i} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">#{tag}</span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Changes Made</p>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {modifiedContent.changes_made.map((change, i) => (
                    <li key={i}>{change}</li>
                  ))}
                </ul>
              </div>

              {/* Schedule & Publish Section */}
              <div className="border-t pt-4 mt-4">
                <h4 className="text-md font-semibold mb-3">Schedule & Auto-Publish</h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Publish to Platforms</label>
                    <div className="flex flex-wrap gap-2">
                      {platformOptions.map((p) => (
                        <button
                          key={p}
                          onClick={() => toggleSchedulePlatform(p)}
                          className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                            schedulePlatforms.includes(p)
                              ? 'bg-primary-600 text-white border-primary-600'
                              : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
                          }`}
                        >
                          {p.charAt(0).toUpperCase() + p.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Schedule Date & Time</label>
                    <input
                      type="datetime-local"
                      value={scheduleTime}
                      onChange={(e) => setScheduleTime(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                  <button
                    onClick={() => scheduleAndPublish(modifiedContent.modified_content, modifiedContent.hashtags)}
                    disabled={scheduleLoading || !scheduleTime || schedulePlatforms.length === 0}
                    className="bg-green-600 text-white px-6 py-2.5 rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium text-sm w-full"
                  >
                    {scheduleLoading ? 'Scheduling...' : `Schedule to ${schedulePlatforms.length || 0} Platform(s)`}
                  </button>
                  {scheduleSuccess && (
                    <div className="bg-green-50 border border-green-200 text-green-700 p-3 rounded-lg text-sm">
                      {scheduleSuccess}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab: Generate Ideas */}
      {activeTab === 'ideas' && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Generate Ideas</h2>
          <div className="space-y-4">
            <input
              type="text"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              placeholder="Enter niche (e.g., fitness, cooking)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
            <button
              onClick={generateIdeas}
              disabled={loading || !niche}
              className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50 font-medium text-sm w-full"
            >
              {loading ? 'Generating...' : 'Generate Ideas'}
            </button>
          </div>
          {ideas.length > 0 && (
            <div className="mt-4 space-y-3">
              {ideas.map((idea) => (
                <div key={idea.id} className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-sm">{idea.topic}</p>
                  <p className="text-xs text-gray-500 mt-1 line-clamp-3">{idea.content_suggestion}</p>
                  <span className="text-xs text-gray-400 capitalize">{idea.content_type}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab: Optimize Caption */}
      {activeTab === 'optimize' && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Optimize Caption</h2>
          <div className="space-y-4">
            <textarea
              value={optimizeText}
              onChange={(e) => setOptimizeText(e.target.value)}
              rows={4}
              placeholder="Paste your draft caption here..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
            <button
              onClick={optimizeCaption}
              disabled={loading || !optimizeText}
              className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50 font-medium text-sm w-full"
            >
              {loading ? 'Optimizing...' : 'Optimize Caption'}
            </button>
          </div>
          {optimizedResult && (
            <div className="mt-4 p-4 bg-green-50 rounded-lg">
              <p className="font-medium text-sm text-green-800 mb-2">Optimized Caption:</p>
              <p className="text-sm text-green-700 whitespace-pre-wrap">{optimizedResult.optimized}</p>
              {optimizedResult.improvements.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium text-green-800">Improvements:</p>
                  <ul className="list-disc list-inside text-xs text-green-700 mt-1">
                    {optimizedResult.improvements.map((imp, i) => (
                      <li key={i}>{imp}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
