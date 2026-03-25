export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-3xl mx-auto bg-white rounded-xl border border-gray-200 p-8">
        <h1 className="text-3xl font-bold mb-6">Privacy Policy</h1>
        <p className="text-gray-500 text-sm mb-8">Last updated: March 16, 2026</p>

        <div className="space-y-6 text-gray-700 leading-relaxed">
          <section>
            <h2 className="text-xl font-semibold mb-2">1. Introduction</h2>
            <p>Social Media Agent (&quot;we&quot;, &quot;our&quot;, &quot;us&quot;) is a social media management platform that helps users schedule and publish content across multiple social media platforms. This privacy policy explains how we collect, use, and protect your information.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-2">2. Information We Collect</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Account Information:</strong> Email address, display name, and password (hashed) when you register.</li>
              <li><strong>Social Media Tokens:</strong> When you connect platforms (YouTube, Instagram, Facebook, Twitter, LinkedIn), we store encrypted OAuth access tokens to post on your behalf.</li>
              <li><strong>Content:</strong> Posts, captions, media files, and scheduling information you create within the platform.</li>
              <li><strong>Usage Data:</strong> Basic analytics about how you use the platform to improve our service.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-2">3. How We Use Your Information</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>To publish and schedule posts to your connected social media accounts.</li>
              <li>To display your connected accounts and their status in the dashboard.</li>
              <li>To generate AI-powered content suggestions and media.</li>
              <li>To provide analytics about your post performance.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-2">4. YouTube API Services</h2>
            <p>Our application uses YouTube API Services. By using our service to connect your YouTube account, you agree to be bound by the <a href="https://www.youtube.com/t/terms" className="text-blue-600 underline" target="_blank" rel="noopener noreferrer">YouTube Terms of Service</a>.</p>
            <p className="mt-2">We access the following YouTube data:</p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li>Upload videos to your YouTube channel</li>
              <li>Read your channel information (name, subscriber count)</li>
              <li>Manage your YouTube videos (edit titles, descriptions)</li>
            </ul>
            <p className="mt-2">You can revoke our access at any time through <a href="https://security.google.com/settings/security/permissions" className="text-blue-600 underline" target="_blank" rel="noopener noreferrer">Google Security Settings</a>.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-2">5. Data Security</h2>
            <p>All OAuth tokens are encrypted using AES-256-GCM encryption before storage. Passwords are hashed using bcrypt. All data is transmitted over HTTPS.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-2">6. Data Sharing</h2>
            <p>We do not sell, trade, or share your personal information with third parties. Your data is only shared with the social media platforms you explicitly connect to for the purpose of publishing your content.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-2">7. Data Retention &amp; Deletion</h2>
            <p>You can disconnect any social media account at any time, which removes the stored tokens. You can request full account deletion by contacting us. Upon deletion, all your data including posts, tokens, and account information will be permanently removed.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-2">8. Contact</h2>
            <p>If you have questions about this privacy policy, please contact the developer of this application.</p>
          </section>
        </div>
      </div>
    </div>
  );
}
