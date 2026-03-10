// app/(marketing)/layout.tsx
// Marketing routes layout. Server component.
// Transparent wrapper for landing page — no auth, no nav chrome.

export default function MarketingLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <>{children}</>;
}
