// app/sentry-example-page/page.tsx
// Test page for Sentry error tracking
// Visit /sentry-example-page and click the button to trigger a test error
'use client';

export default function SentryExamplePage() {
  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Sentry Test Page</h1>
      <p>Click the button below to trigger a test error.</p>
      <p>Then check your Sentry dashboard at: <a href="https://sentry.io" target="_blank">sentry.io</a></p>
      
      <button
        onClick={() => {
          throw new Error('Sentry Test Error - This is a test error to verify Sentry integration');
        }}
        style={{
          marginTop: '1rem',
          padding: '0.5rem 1rem',
          fontSize: '1rem',
          cursor: 'pointer',
          backgroundColor: '#e74c3c',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
        }}
      >
        Trigger Test Error
      </button>
      
      <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
        <h3>Instructions:</h3>
        <ol>
          <li>Start the dev server: <code>npm run dev</code></li>
          <li>Visit: <code>http://localhost:3000/sentry-example-page</code></li>
          <li>Click the &quot;Trigger Test Error&quot; button</li>
          <li>Check Sentry dashboard for the error</li>
          <li>Verify: Project = student-cjs/javascript-nextjs</li>
        </ol>
      </div>
    </div>
  );
}
