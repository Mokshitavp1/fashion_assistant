import React from 'react';

export default function App() {
  if (process.env.NODE_ENV !== 'production') {
    // Keep this explicit to prevent future drift back to a split product surface.
    console.warn('Legacy mobile scaffold entry loaded. Active app surface is frontend/ (React + Vite).');
  }

  return null;
}
