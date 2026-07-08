'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface ConnectedAccount {
  id: number;
  platform: string;
  platform_user_id: string;
  platform_username: string | null;
  token_expires_at: string | null;
  connected_at: string | null;
  profile_data: any;
}

const platforms: {
  key: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  textColor: string;
  bgLight: string;
  description: string;
  connectUrl: string;
}[] = [
  {
    key: 'instagram',
    name: 'Instagram',
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
      </svg>
    ),
    color: 'bg-gradient-to-r from-purple-500 to-pink-500',
    textColor: 'text-purple-600',
    bgLight: 'bg-purple-50',
    description: 'Share photos, reels & stories',
    connectUrl: '/api/oauth/meta/authorize',
  },
  {
    key: 'youtube',
    name: 'YouTube',
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
      </svg>
    ),
    color: 'bg-red-600',
    textColor: 'text-red-600',
    bgLight: 'bg-red-50',
    description: 'Upload videos & shorts',
    connectUrl: '/api/oauth/google/authorize',
  },
  {
    key: 'facebook',
    name: 'Facebook',
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
      </svg>
    ),
    color: 'bg-blue-600',
    textColor: 'text-blue-600',
    bgLight: 'bg-blue-50',
    description: 'Post to pages & groups',
    connectUrl: '/api/oauth/meta/authorize',
  },
  {
    key: 'twitter',
    name: 'Twitter / X',
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    ),
    color: 'bg-black',
    textColor: 'text-gray-800',
    bgLight: 'bg-gray-50',
    description: 'Post tweets & threads',
    connectUrl: '/api/oauth/twitter/authorize',
  },
  {
    key: 'linkedin',
    name: 'LinkedIn',
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
      </svg>
    ),
    color: 'bg-blue-700',
    textColor: 'text-blue-700',
    bgLight: 'bg-blue-50',
    description: 'Share professional content',
    connectUrl: '/api/oauth/linkedin/authorize',
  },
];

function AccountsContent() {
  const searchParams = useSearchParams();
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [successMessage, setSuccessMessage] = useState('');

  const fetchAccounts = async () => {
    try {
      const data = await apiFetch('/api/oauth/accounts');
      setAccounts(Array.isArray(data) ? data : []);
    } catch {
      try {
        const d = await apiFetch('/api/accounts/');
        setAccounts(d.accounts || []);
      } catch {}
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchAccounts();

    // Check if we just came back from OAuth
    const connected = searchParams.get('connected');
    if (connected) {
      const platformNames = connected.split('|').map((p) => {
        const info = platforms.find((pl) => pl.key === p);
        return info?.name || p;
      });
      setSuccessMessage(`${platformNames.join(' & ')} connected successfully!`);
      // Clean URL without reload
      window.history.replaceState({}, '', '/accounts');
      // Auto-hide after 5s
      setTimeout(() => setSuccessMessage(''), 5000);
    }
  }, []);

  const connectPlatform = (connectUrl: string) => {
    // Get the auth token and pass it via the URL so the backend can identify the user
    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Please log in first');
      return;
    }
    // Redirect in the same tab — the backend authorize endpoint now returns a RedirectResponse
    // We need to pass the auth token via a query param since redirect won't carry the header
    window.location.href = `${connectUrl}?token=${encodeURIComponent(token)}`;
  };

  const disconnectAccount = async (id: number) => {
    if (!confirm('Disconnect this account?')) return;
    try {
      await apiFetch(`/api/accounts/${id}`, { method: 'DELETE' });
      fetchAccounts();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const connectedPlatforms = new Set(accounts.map((a) => a.platform));

  const getTimeUntilExpiry = (expiresAt: string) => {
    const diff = new Date(expiresAt).getTime() - Date.now();
    if (diff < 0) return 'Expired';
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    if (days > 0) return `${days} days left`;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    return `${hours} hours left`;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Connected Accounts</h1>
          <p className="text-gray-500">Connect your social media accounts to start posting</p>
        </div>
      </div>

      {/* Success Toast */}
      {successMessage && (
        <div className="mb-6 flex items-center gap-3 px-5 py-4 bg-green-50 border border-green-200 rounded-xl animate-in">
          <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-green-800 font-medium">{successMessage}</p>
          <button onClick={() => setSuccessMessage('')} className="ml-auto text-green-600 hover:text-green-800">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Connected Accounts */}
      {!loading && accounts.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Your Connected Accounts</h2>
          <div className="space-y-3">
            {accounts.map((account) => {
              const platformInfo = platforms.find((p) => p.key === account.platform);
              return (
                <div key={account.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-100">
                  <div className="flex items-center gap-4">
                    <div className={`${platformInfo?.color || 'bg-gray-500'} w-12 h-12 rounded-xl text-white flex items-center justify-center`}>
                      {platformInfo?.icon || <span className="text-lg">🔗</span>}
                    </div>
                    <div>
                      <p className="font-semibold">{platformInfo?.name || account.platform}</p>
                      <p className="text-sm text-gray-500">{account.platform_username || account.platform_user_id}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
                          <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                          Connected
                        </span>
                        {account.token_expires_at && (
                          <span className="text-xs text-gray-400">
                            Token: {getTimeUntilExpiry(account.token_expires_at)}
                          </span>
                        )}
                        {account.connected_at && (
                          <span className="text-xs text-gray-400">
                            Since {new Date(account.connected_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => connectPlatform(platformInfo?.connectUrl || '')}
                      className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1.5 rounded-lg hover:bg-gray-100"
                    >
                      Reconnect
                    </button>
                    <button
                      onClick={() => disconnectAccount(account.id)}
                      className="text-sm text-red-500 hover:text-red-700 px-3 py-1.5 rounded-lg hover:bg-red-50"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Connect Platforms */}
      <h2 className="text-lg font-semibold mb-4">
        {accounts.length > 0 ? 'Connect More Platforms' : 'Connect a Platform to Get Started'}
      </h2>
      <p className="text-gray-500 text-sm mb-6">
        Click on a platform below — you'll be redirected to log in with your account and authorize access.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {platforms.map((p) => {
          const isConnected = connectedPlatforms.has(p.key);

          return (
            <button
              key={p.key}
              onClick={() => connectPlatform(p.connectUrl)}
              className={`text-left bg-white rounded-xl border-2 p-6 transition-all hover:shadow-lg hover:-translate-y-0.5 ${
                isConnected
                  ? 'border-green-200 hover:border-green-300'
                  : 'border-gray-200 hover:border-primary-300'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`${p.color} w-14 h-14 rounded-xl text-white flex items-center justify-center`}>
                  {p.icon}
                </div>
                {isConnected && (
                  <span className="flex items-center gap-1 text-xs font-medium text-green-600 bg-green-100 px-2 py-1 rounded-full">
                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                    Connected
                  </span>
                )}
              </div>

              <h3 className="font-semibold text-lg text-gray-900 mb-1">{p.name}</h3>
              <p className="text-sm text-gray-500 mb-4">{p.description}</p>

              <div className={`w-full py-2.5 rounded-lg text-sm font-medium text-center transition-colors ${
                isConnected
                  ? 'bg-gray-100 text-gray-600'
                  : 'bg-primary-600 text-white'
              }`}>
                {isConnected ? 'Reconnect Account' : 'Connect Now →'}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function AccountsPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-12">Loading accounts...</div>}>
      <AccountsContent />
    </Suspense>
  );
}
