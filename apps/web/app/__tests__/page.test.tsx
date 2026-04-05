import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import HomePage from '../page';

describe('HomePage', () => {
  it('renders the Atlas heading', () => {
    render(<HomePage />);
    const heading = screen.getByRole('heading', { name: 'Atlas' });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveClass('text-4xl', 'font-bold');
  });

  it('renders the description text', () => {
    render(<HomePage />);
    const description = screen.getByText(/Knowledge compiler/i);
    expect(description).toBeInTheDocument();
  });

  it('renders in a main element with flex layout', () => {
    const { container } = render(<HomePage />);
    const main = container.querySelector('main');
    expect(main).toBeInTheDocument();
    expect(main).toHaveClass('flex', 'min-h-screen');
  });
});
