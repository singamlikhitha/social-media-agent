'use client';

import { useState, useEffect } from 'react';
import { apiFetch } from '@/lib/api';

interface ConnectedAccount {
  id: number;
  platform: string;
  platform_username: string | null;
}

const platforms = [
  {
    key: 'instagram',
    name: 'Instagram',
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
      </svg>
    ),
    color: 'from-purple-500 via-pink-500 to-orange-400',
    description: 'Share photos, reels & stories',
    path: '/api/oauth/meta/authorize',
  },
  {
    key: 'youtube',
    name: 'YouTube',
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
        <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
      </svg>
    ),
    color: 'from-red-600 to-red-500',
    description: 'Upload videos & shorts',
    path: '/api/oauth/google/authorize',
  },
  {
    key: 'facebook',
    name: 'Facebook',
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
      </svg>
    ),
    color: 'from-blue-600 to-blue-500',
    description: 'Post to pages & groups',
    path: '/api/oauth/meta/authorize',
  },
  {
    key: 'twitter',
    name: 'Twitter / X',
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    ),
    color: 'from-gray-900 to-gray-700',
    description: 'Post tweets & threads',
    path: '/api/oauth/twitter/authorize',
  },
  {
    key: 'linkedin',
    name: 'LinkedIn',
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
      </svg>
    ),
    color: 'from-blue-700 to-blue-600',
    description: 'Share professional content',
    path: '/api/oauth/linkedin/authorize',
  },
];

interface Props {
  onClose: () => void;
  onAccountConnected: () => void;
}

export default function ConnectAccountsModal({ onClose, onAccountConnected }: Props) {
  const [connectedAccounts, setConnectedAccounts] = useState<ConnectedAccount[]>([]);
  const [connecting, setConnecting] = useState<string | null>(null);

  const fetchAccounts = async () => {
    try {
      const data = await apiFetch('/api/oauth/accounts');
      setConnectedAccounts(Array.isArray(data) ? data : []);
    } catch {
      try {
        const data = await apiFetch('/api/accounts/');
        setConnectedAccounts(data.accounts || []);
      } catch {}
    }
  };

  useEffect(() => {
    fetchAccounts();

    const handleMessage = (event: MessageEvent) => {
      if (event.data === 'oauth_complete') {
        fetchAccounts();
        onAccountConnected();
        setConnecting(null);
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  const connectPlatform = (platform: typeof platforms[0]) => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Please log in first');
      return;
    }
    // Redirect in same tab to platform login
    window.location.href = `${platform.path}?token=${encodeURIComponent(token)}`;
  };

  const connectedKeys = new Set(connectedAccounts.map((a) => a.platform));
  const connectedCount = connectedKeys.size;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 pb-0">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Connect Your Accounts</h2>
              <p className="text-gray-500 mt-1">Link your social media accounts to start scheduling and publishing posts</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Progress */}
          <div className="flex items-center gap-3 mt-4 mb-6">
            <div className="flex-1 bg-gray-100 rounded-full h-2">
              <div
                className="bg-primary-600 rounded-full h-2 transition-all duration-500"
                style={{ width: `${Math.min((connectedCount / 3) * 100, 100)}%` }}
              />
            </div>
            <span className="text-sm text-gray-500 whitespace-nowrap">{connectedCount} connected</span>
          </div>
        </div>

        {/* Platforms */}
        <div className="px-6 pb-6 space-y-3">
          {platforms.map((platform) => {
            const isConnected = connectedKeys.has(platform.key);
            const account = connectedAccounts.find((a) => a.platform === platform.key);
            const isConnecting = connecting === platform.key;

            return (
              <div
                key={platform.key}
                className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${
                  isConnected
                    ? 'border-green-200 bg-green-50/50'
                    : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                }`}
              >
                {/* Icon */}
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${platform.color} text-white flex items-center justify-center flex-shrink-0`}>
                  {platform.icon}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{platform.name}</h3>
                    {isConnected && (
                      <span className="flex items-center gap-1 text-xs font-medium text-green-600 bg-green-100 px-2 py-0.5 rounded-full">
                        <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                        Connected
                      </span>
                    )}
                  </div>
                  {isConnected && account?.platform_username ? (
                    <p className="text-sm text-gray-600 mt-0.5">@{account.platform_username}</p>
                  ) : (
                    <p className="text-sm text-gray-400 mt-0.5">{platform.description}</p>
                  )}
                </div>

                {/* Action */}
                <button
                  onClick={() => connectPlatform(platform)}
                  disabled={isConnecting}
                  className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all flex-shrink-0 ${
                    isConnected
                      ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      : isConnecting
                      ? 'bg-gray-100 text-gray-400 cursor-wait'
                      : 'bg-primary-600 text-white hover:bg-primary-700 shadow-sm'
                  }`}
                >
                  {isConnecting ? (
                    <span className="flex items-center gap-2">
                      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Connecting...
                    </span>
                  ) : isConnected ? (
                    'Reconnect'
                  ) : (
                    'Connect'
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl border-t border-gray-100 flex items-center justify-between">
          <p className="text-xs text-gray-400">You can always connect more accounts later from the Accounts page</p>
          <button
            onClick={onClose}
            className="px-5 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
          >
            {connectedCount > 0 ? 'Done' : 'Skip for now'}
          </button>
        </div>
      </div>
    </div>
  );
}
