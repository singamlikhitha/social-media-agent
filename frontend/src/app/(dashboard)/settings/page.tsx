'use client';

import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '@/lib/auth';
import { apiFetch } from '@/lib/api';

function getAllTimezones(): { value: string; label: string; offset: string }[] {
  const tzNames: string[] = [];
  try {
    // @ts-ignore - Intl.supportedValuesOf is available in modern browsers
    tzNames.push(...Intl.supportedValuesOf('timeZone'));
  } catch {
    // Fallback for older browsers
    const common = [
      'UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
      'America/Anchorage', 'Pacific/Honolulu', 'America/Sao_Paulo', 'America/Argentina/Buenos_Aires',
      'America/Mexico_City', 'America/Bogota', 'America/Halifax', 'America/Toronto',
      'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Rome', 'Europe/Madrid',
      'Europe/Amsterdam', 'Europe/Brussels', 'Europe/Zurich', 'Europe/Vienna', 'Europe/Warsaw',
      'Europe/Prague', 'Europe/Budapest', 'Europe/Bucharest', 'Europe/Athens', 'Europe/Helsinki',
      'Europe/Stockholm', 'Europe/Oslo', 'Europe/Copenhagen', 'Europe/Dublin', 'Europe/Lisbon',
      'Europe/Moscow', 'Europe/Istanbul', 'Europe/Kiev',
      'Asia/Dubai', 'Asia/Riyadh', 'Asia/Tehran', 'Asia/Karachi', 'Asia/Kolkata',
      'Asia/Kathmandu', 'Asia/Dhaka', 'Asia/Bangkok', 'Asia/Jakarta', 'Asia/Singapore',
      'Asia/Shanghai', 'Asia/Hong_Kong', 'Asia/Taipei', 'Asia/Tokyo', 'Asia/Seoul',
      'Asia/Manila', 'Asia/Kuala_Lumpur', 'Asia/Ho_Chi_Minh', 'Asia/Yangon',
      'Asia/Almaty', 'Asia/Tashkent', 'Asia/Tbilisi', 'Asia/Baku', 'Asia/Yerevan',
      'Asia/Beirut', 'Asia/Jerusalem', 'Asia/Baghdad', 'Asia/Kuwait', 'Asia/Muscat',
      'Africa/Cairo', 'Africa/Lagos', 'Africa/Johannesburg', 'Africa/Nairobi',
      'Africa/Casablanca', 'Africa/Accra', 'Africa/Addis_Ababa', 'Africa/Dar_es_Salaam',
      'Australia/Sydney', 'Australia/Melbourne', 'Australia/Brisbane', 'Australia/Perth',
      'Australia/Adelaide', 'Australia/Darwin', 'Australia/Hobart',
      'Pacific/Auckland', 'Pacific/Fiji', 'Pacific/Guam', 'Pacific/Noumea',
      'Indian/Maldives', 'Indian/Mauritius',
    ];
    tzNames.push(...common);
  }

  const now = new Date();
  return tzNames.map((tz) => {
    let offset = '';
    try {
      const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: tz,
        timeZoneName: 'shortOffset',
      });
      const parts = formatter.formatToParts(now);
      const tzPart = parts.find((p) => p.type === 'timeZoneName');
      offset = tzPart?.value || '';
    } catch {
      offset = '';
    }

    const city = tz.split('/').pop()?.replace(/_/g, ' ') || tz;
    const region = tz.split('/')[0];
    return {
      value: tz,
      label: `${city} (${offset || tz})`,
      offset,
      region,
      city,
    };
  }).sort((a, b) => {
    // Sort by offset first, then by city name
    const parseOffset = (o: string) => {
      const match = o.match(/GMT([+-]\d{1,2}(?::\d{2})?)/);
      if (!match) return 0;
      const [h, m] = match[1].split(':').map(Number);
      return (h || 0) * 60 + (m || 0);
    };
    const diff = parseOffset(a.offset) - parseOffset(b.offset);
    if (diff !== 0) return diff;
    return a.city.localeCompare(b.city);
  });
}

const REGIONS = ['All', 'America', 'Europe', 'Asia', 'Africa', 'Australia', 'Pacific', 'Indian', 'Atlantic', 'Arctic'];

export default function SettingsPage() {
  const { user } = useAuth();
  const [displayName, setDisplayName] = useState('');
  const [timezone, setTimezone] = useState('UTC');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');
  const [searchTz, setSearchTz] = useState('');
  const [region, setRegion] = useState('All');

  const allTimezones = useMemo(() => getAllTimezones(), []);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || '');
      setTimezone(user.timezone || 'UTC');
    }
  }, [user]);

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSaved(false);
    try {
      await apiFetch('/api/auth/me', {
        method: 'PUT',
        body: JSON.stringify({ display_name: displayName, timezone }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const filteredTimezones = allTimezones.filter((tz) => {
    const matchesRegion = region === 'All' || tz.value.startsWith(region);
    const matchesSearch = !searchTz ||
      tz.value.toLowerCase().includes(searchTz.toLowerCase()) ||
      tz.label.toLowerCase().includes(searchTz.toLowerCase());
    return matchesRegion && matchesSearch;
  });

  const detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const selectedTzInfo = allTimezones.find((tz) => tz.value === timezone);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Settings</h1>
      <p className="text-gray-500 mb-8">Manage your account settings</p>

      <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-2xl">
        <h2 className="text-lg font-semibold mb-4">Profile</h2>

        {error && <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>}
        {saved && <div className="bg-green-50 text-green-600 px-4 py-3 rounded-lg mb-4 text-sm">Settings saved successfully!</div>}

        <div className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input type="email" value={user?.email || ''} disabled className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              placeholder="Your display name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Timezone</label>

            {/* Current selection */}
            <div className="flex items-center gap-2 mb-3 p-3 bg-primary-50 border border-primary-200 rounded-lg">
              <svg className="w-5 h-5 text-primary-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-primary-800">{selectedTzInfo?.label || timezone}</p>
                <p className="text-xs text-primary-600">{timezone}</p>
              </div>
              {detectedTimezone !== timezone && (
                <button
                  type="button"
                  onClick={() => setTimezone(detectedTimezone)}
                  className="text-xs bg-primary-600 text-white px-3 py-1.5 rounded-lg hover:bg-primary-700 font-medium"
                >
                  Use detected ({detectedTimezone.split('/').pop()?.replace(/_/g, ' ')})
                </button>
              )}
            </div>

            {/* Search */}
            <input
              type="text"
              value={searchTz}
              onChange={(e) => setSearchTz(e.target.value)}
              placeholder="Search city, country, or timezone..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-sm mb-2"
            />

            {/* Region filters */}
            <div className="flex flex-wrap gap-1.5 mb-2">
              {REGIONS.map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRegion(r)}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                    region === r
                      ? 'bg-primary-100 text-primary-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            {/* Timezone list */}
            <div className="border border-gray-300 rounded-lg max-h-64 overflow-y-auto">
              {filteredTimezones.length === 0 ? (
                <div className="p-4 text-center text-gray-400 text-sm">No timezones found</div>
              ) : (
                filteredTimezones.map((tz) => (
                  <button
                    key={tz.value}
                    type="button"
                    onClick={() => { setTimezone(tz.value); setSearchTz(''); }}
                    className={`w-full text-left px-3 py-2 text-sm border-b border-gray-100 last:border-0 hover:bg-gray-50 flex items-center justify-between ${
                      timezone === tz.value ? 'bg-primary-50 text-primary-700 font-medium' : ''
                    }`}
                  >
                    <span>{tz.value.replace(/_/g, ' ')}</span>
                    <span className="text-xs text-gray-400 ml-2">{tz.offset}</span>
                  </button>
                ))
              )}
            </div>
            <p className="text-xs text-gray-400 mt-1.5">{filteredTimezones.length} timezones available</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
            <input type="text" value={user?.plan_tier || 'free'} disabled className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 capitalize" />
          </div>

          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-primary-600 text-white px-6 py-2.5 rounded-lg hover:bg-primary-700 disabled:opacity-50 font-medium text-sm transition-colors"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
