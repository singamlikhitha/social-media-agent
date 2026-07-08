'use client';

import { useState } from 'react';
import { apiFetch } from '@/lib/api';

interface PlatformOverview {
  platform: string;
  total_posts: number;
  total_impressions: number;
  total_reach: number;
  total_likes: number;
  total_comments: number;
  avg_engagement_rate: number;
  period_days: number;
}

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<PlatformOverview | null>(null);
  const [platform, setPlatform] = useState('instagram');
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(false);

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const data = await apiFetch(`/api/analytics/${platform}/overview?days=${days}`);
      setOverview(data);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Analytics</h1>
      <p className="text-gray-500 mb-8">Track your social media performance</p>

      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-lg">
            <option value="instagram">Instagram</option>
            <option value="youtube">YouTube</option>
            <option value="facebook">Facebook</option>
            <option value="twitter">Twitter</option>
            <option value="linkedin">LinkedIn</option>
          </select>
          <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="px-3 py-2 border border-gray-300 rounded-lg">
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button onClick={fetchOverview} disabled={loading} className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50 font-medium text-sm">
            {loading ? 'Loading...' : 'Fetch Analytics'}
          </button>
        </div>
      </div>

      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs text-gray-500">Posts</p>
            <p className="text-2xl font-bold">{overview.total_posts}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs text-gray-500">Impressions</p>
            <p className="text-2xl font-bold">{overview.total_impressions.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs text-gray-500">Reach</p>
            <p className="text-2xl font-bold">{overview.total_reach.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs text-gray-500">Likes</p>
            <p className="text-2xl font-bold">{overview.total_likes.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs text-gray-500">Comments</p>
            <p className="text-2xl font-bold">{overview.total_comments.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs text-gray-500">Engagement Rate</p>
            <p className="text-2xl font-bold">{overview.avg_engagement_rate}%</p>
          </div>
        </div>
      )}
    </div>
  );
}
