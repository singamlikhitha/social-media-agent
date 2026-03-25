'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import { apiFetch } from '@/lib/api';
import ConnectAccountsModal from '@/components/ConnectAccountsModal';

interface AccountInfo {
  id: number;
  platform: string;
  platform_username: string | null;
  platform_user_id: string;
  token_expires_at: string | null;
}

interface PostInfo {
  id: number;
  platform: string;
  status: string;
  content_text: string;
  scheduled_time: string;
}

const platformMeta: Record<string, { name: string; color: string; gradient: string; icon: string }> = {
  instagram: { name: 'Instagram', color: 'text-pink-600', gradient: 'from-purple-500 to-pink-500', icon: '📸' },
  youtube: { name: 'YouTube', color: 'text-red-600', gradient: 'from-red-600 to-red-500', icon: '🎬' },
  facebook: { name: 'Facebook', color: 'text-blue-600', gradient: 'from-blue-600 to-blue-500', icon: '👤' },
  twitter: { name: 'Twitter / X', color: 'text-gray-800', gradient: 'from-gray-800 to-gray-600', icon: '🐦' },
  linkedin: { name: 'LinkedIn', color: 'text-blue-700', gradient: 'from-blue-700 to-blue-600', icon: '💼' },
};

const quickConnectPlatforms = [
  { key: 'instagram', path: '/api/oauth/meta/authorize' },
  { key: 'youtube', path: '/api/oauth/google/authorize' },
  { key: 'facebook', path: '/api/oauth/meta/authorize' },
  { key: 'twitter', path: '/api/oauth/twitter/authorize' },
  { key: 'linkedin', path: '/api/oauth/linkedin/authorize' },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<AccountInfo[]>([]);
  const [recentPosts, setRecentPosts] = useState<PostInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [hasSeenOnboarding, setHasSeenOnboarding] = useState(false);

  const fetchData = async () => {
    try {
      const [accountsData, postsData] = await Promise.all([
        apiFetch('/api/oauth/accounts').catch(() => apiFetch('/api/accounts/').then((d) => d.accounts || []).catch(() => [])),
        apiFetch('/api/posts?limit=5').catch(() => []),
      ]);
      const accts = Array.isArray(accountsData) ? accountsData : [];
      setAccounts(accts);
      setRecentPosts(Array.isArray(postsData) ? postsData : []);

      // Show onboarding modal if no accounts connected and haven't seen it yet
      if (accts.length === 0 && !hasSeenOnboarding) {
        const seen = localStorage.getItem('onboarding_seen');
        if (!seen) {
          setShowConnectModal(true);
          setHasSeenOnboarding(true);
        }
      }
    } catch {}
    setLoading(false);
  };

  useEffect(() => {
    fetchData();

    // Listen for OAuth popup completions
    const handleMessage = (event: MessageEvent) => {
      if (event.data === 'oauth_complete') {
        fetchData();
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  const handleCloseModal = () => {
    setShowConnectModal(false);
    localStorage.setItem('onboarding_seen', 'true');
  };

  const connectPlatform = (path: string) => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Please log in first');
      return;
    }
    // Redirect in same tab to platform login
    window.location.href = `${path}?token=${encodeURIComponent(token)}`;
  };

  const connectedPlatformKeys = new Set(accounts.map((a) => a.platform));
  const unconnectedPlatforms = quickConnectPlatforms.filter((p) => !connectedPlatformKeys.has(p.key));

  const statusColors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-700',
    scheduled: 'bg-yellow-100 text-yellow-800',
    publishing: 'bg-blue-100 text-blue-800',
    published: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <div>
      {/* Connect Accounts Modal */}
      {showConnectModal && (
        <ConnectAccountsModal
          onClose={handleCloseModal}
          onAccountConnected={fetchData}
        />
      )}

      <h1 className="text-2xl font-bold mb-1">Dashboard</h1>
      <p className="text-gray-500 mb-8">Welcome back, {user?.display_name || user?.email}</p>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-sm text-gray-500">Connected Accounts</p>
          <p className="text-3xl font-bold mt-1">{accounts.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-sm text-gray-500">Scheduled Posts</p>
          <p className="text-3xl font-bold mt-1">{recentPosts.filter((p) => p.status === 'scheduled').length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-sm text-gray-500">Published</p>
          <p className="text-3xl font-bold mt-1 text-green-600">{recentPosts.filter((p) => p.status === 'published').length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-sm text-gray-500">Plan</p>
          <p className="text-3xl font-bold mt-1 capitalize">{user?.plan_tier}</p>
        </div>
      </div>

      {/* No accounts connected - prominent CTA */}
      {!loading && accounts.length === 0 && (
        <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-2xl border border-primary-200 p-8 mb-8">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center flex-shrink-0">
              <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <div className="flex-1 text-center md:text-left">
              <h2 className="text-xl font-bold text-gray-900 mb-1">Get Started - Connect Your Accounts</h2>
              <p className="text-gray-600">Connect your social media accounts to start scheduling and publishing posts automatically.</p>
            </div>
            <button
              onClick={() => setShowConnectModal(true)}
              className="bg-primary-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-primary-700 shadow-sm flex-shrink-0 text-sm"
            >
              Connect Accounts
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connected Accounts */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Connected Accounts</h2>
            <button
              onClick={() => setShowConnectModal(true)}
              className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add
            </button>
          </div>

          {loading ? (
            <p className="text-gray-500 py-4 text-center">Loading...</p>
          ) : accounts.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-gray-400 text-sm mb-4">No accounts connected yet</p>
              <div className="flex flex-wrap justify-center gap-2">
                {quickConnectPlatforms.map((p) => {
                  const meta = platformMeta[p.key];
                  return (
                    <button
                      key={p.key}
                      onClick={() => connectPlatform(p.path)}
                      className={`flex items-center gap-1.5 px-3 py-2 rounded-lg bg-gradient-to-r ${meta.gradient} text-white text-xs font-medium hover:opacity-90 transition-opacity`}
                    >
                      <span>{meta.icon}</span>
                      {meta.name}
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {accounts.map((account) => {
                const meta = platformMeta[account.platform] || { name: account.platform, color: 'text-gray-600', gradient: 'from-gray-500 to-gray-400', icon: '🔗' };
                return (
                  <div key={account.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${meta.gradient} text-white flex items-center justify-center text-lg`}>
                      {meta.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm">{meta.name}</p>
                      <p className="text-xs text-gray-500 truncate">
                        {account.platform_username || account.platform_user_id}
                      </p>
                    </div>
                    <span className="flex items-center gap-1 text-xs text-green-600">
                      <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                      Active
                    </span>
                  </div>
                );
              })}

              {/* Quick connect unconnected platforms */}
              {unconnectedPlatforms.length > 0 && (
                <div className="pt-3 border-t border-gray-100 mt-3">
                  <p className="text-xs text-gray-400 mb-2">Connect more platforms</p>
                  <div className="flex flex-wrap gap-1.5">
                    {unconnectedPlatforms.map((p) => {
                      const meta = platformMeta[p.key];
                      return (
                        <button
                          key={p.key}
                          onClick={() => connectPlatform(p.path)}
                          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-gray-200 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
                        >
                          <span>{meta.icon}</span>
                          {meta.name}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Recent Posts */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Recent Posts</h2>
            <a href="/posts" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
              View all
            </a>
          </div>

          {loading ? (
            <p className="text-gray-500 py-4 text-center">Loading...</p>
          ) : recentPosts.length === 0 ? (
            <div className="text-center py-6">
              <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </div>
              <p className="text-gray-400 text-sm mb-3">No posts yet</p>
              <a href="/posts" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
                Create your first post
              </a>
            </div>
          ) : (
            <div className="space-y-2">
              {recentPosts.map((post) => {
                const meta = platformMeta[post.platform] || { name: post.platform, icon: '📄' };
                return (
                  <a key={post.id} href="/posts" className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="text-lg">{meta.icon}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 truncate">{post.content_text || 'No content'}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {new Date(post.scheduled_time).toLocaleString()}
                      </p>
                    </div>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${statusColors[post.status] || 'bg-gray-100'}`}>
                      {post.status === 'publishing' ? 'In Progress' : post.status}
                    </span>
                  </a>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
