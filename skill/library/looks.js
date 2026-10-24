/**
 * codefilm looks — 8 token sets for the scene kit.
 *
 *   <script src="../../library/looks.js"></script>
 *   CF.looks.apply(cardEl, 'dark-tech');   // sets --cfs-* variables on that element
 *   CF.looks.names                         // ['paper-ink', ...]
 *
 * A look is a system of invariants (ground, ink, accent, type, material), not a template.
 */
(function (root) {
  'use strict';
  const LOOKS = {
    'paper-ink': {
      label: 'Paper & Ink',
      colors: { paper: '#F2ECE1', ink: '#1B1A17', accent: '#D9552B', muted: '#8A8275', card: '#FFFDF8', line: '#D8CFC0' },
      type: { display: 'Georgia, "Times New Roman", serif', body: '"Segoe UI", system-ui, sans-serif' },
      motion: { enter: 'outCubic', move: 'inOutCubic', dur: .55 }
    },
    'dark-tech': {
      label: 'Dark Tech',
      colors: { paper: '#0B0B10', ink: '#F0ECE4', accent: '#4CC2A0', muted: '#8F8A80', card: '#15151C', line: '#2A2A33' },
      type: { display: 'Inter, "Segoe UI", sans-serif', body: 'Inter, "Segoe UI", sans-serif' },
      motion: { enter: 'outExpo', move: 'inOutCubic', dur: .4 }
    },
    'swiss': {
      label: 'Swiss',
      colors: { paper: '#F7F7F5', ink: '#111111', accent: '#E33B2E', muted: '#777777', card: '#FFFFFF', line: '#DADADA' },
      type: { display: '"Helvetica Neue", Arial, sans-serif', body: '"Helvetica Neue", Arial, sans-serif' },
      motion: { enter: 'outQuart', move: 'inOutQuart', dur: .45 }
    },
    'riso': {
      label: 'Risograph',
      colors: { paper: '#F6EFE4', ink: '#1E2A44', accent: '#FF4B3E', muted: '#6B6B6B', card: '#FFF8EC', line: '#D8C9B8' },
      type: { display: '"Arial Black", Impact, sans-serif', body: '"Segoe UI", sans-serif' },
      motion: { enter: 'backOut', move: 'inOutCubic', dur: .5 }
    },
    'pixel': {
      label: '16-bit Pixel',
      colors: { paper: '#0A1729', ink: '#EAF3FF', accent: '#FF8A5C', muted: '#8FA6C4', card: '#122A4C', line: '#35609A' },
      type: { display: '"Courier New", monospace', body: '"Courier New", monospace' },
      motion: { enter: 'linear', move: 'linear', dur: .25 }
    },
    'blueprint': {
      label: 'Blueprint',
      colors: { paper: '#0B2A4A', ink: '#E8F1FF', accent: '#FFD166', muted: '#8FB3D9', card: '#0E3358', line: '#2C5A85' },
      type: { display: '"Courier New", monospace', body: '"Segoe UI", sans-serif' },
      motion: { enter: 'outCubic', move: 'inOutSine', dur: .5 }
    },
    'hand-drawn': {
      label: 'Hand-drawn',
      colors: { paper: '#FBF7EE', ink: '#2B2B2B', accent: '#D9552B', muted: '#7A6F63', card: '#FFFDF8', line: '#D8CFC0' },
      type: { display: '"Segoe Print", "Comic Sans MS", cursive', body: '"Segoe Print", "Comic Sans MS", cursive' },
      motion: { enter: 'backOut', move: 'inOutSine', dur: .6 }
    },
    'vox-collage': {
      label: 'Vox Collage',
      colors: { paper: '#F2E6D0', ink: '#111111', accent: '#E23A2E', muted: '#6B5A48', card: '#FFF9EE', line: '#C9B79C' },
      type: { display: '"Arial Black", Impact, sans-serif', body: 'Georgia, serif' },
      motion: { enter: 'outQuart', move: 'inOutCubic', dur: .45 }
    }
  };

  const L = {
    names: Object.keys(LOOKS),
    all: LOOKS,
    get(name) { return LOOKS[name] || LOOKS['paper-ink']; },
    apply(el, name) {
      const look = L.get(name);
      if (!el) return look;
      const c = look.colors;
      el.style.setProperty('--cfs-paper', c.paper);
      el.style.setProperty('--cfs-ink', c.ink);
      el.style.setProperty('--cfs-accent', c.accent);
      el.style.setProperty('--cfs-muted', c.muted);
      el.style.setProperty('--cfs-card', c.card);
      el.style.setProperty('--cfs-line', c.line);
      el.style.setProperty('--cfs-display', look.type.display);
      el.style.setProperty('--cfs-body', look.type.body);
      el.dataset.look = name;
      return look;
    }
  };

  const CF = root.CF || (root.CF = {});
  CF.looks = L;
  if (typeof module !== 'undefined' && module.exports) module.exports = L;
})(typeof window !== 'undefined' ? window : globalThis);
