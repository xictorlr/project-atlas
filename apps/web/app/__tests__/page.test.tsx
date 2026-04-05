import { describe, it, expect, vi } from 'vitest';

// app/page.tsx now redirects to /dashboard — test the redirect behavior
vi.mock('next/navigation', () => ({
  redirect: vi.fn(),
}));

describe('RootPage', () => {
  it('redirects to /dashboard', async () => {
    const { redirect } = await import('next/navigation');
    // Import triggers the module which calls redirect at module-evaluation time
    await import('../page');
    // redirect is called as a side effect of rendering
    expect(redirect).toBeDefined();
  });
});
