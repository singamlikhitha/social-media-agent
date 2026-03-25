'use client';

import { Suspense, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

function OAuthSuccessContent() {
  const searchParams = useSearchParams();
  const platform = searchParams.get('platform') || 'account';

  useEffect(() => {
    if (window.opener) {
      window.opener.postMessage('oauth_complete', '*');
      setTimeout(() => window.close(), 1500);
    } else {
      setTimeout(() => {
        window.location.href = '/accounts';
      }, 2000);
    }
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center max-w-sm">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="text-xl font-bold mb-2">Connected!</h1>
        <p className="text-gray-500 text-sm">
          Your <span className="capitalize font-medium">{platform}</span> account has been connected successfully.
        </p>
        <p className="text-gray-400 text-xs mt-3">Redirecting to your accounts...</p>
      </div>
    </div>
  );
}

export default function OAuthSuccessPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <OAuthSuccessContent />
    </Suspense>
  );
}
