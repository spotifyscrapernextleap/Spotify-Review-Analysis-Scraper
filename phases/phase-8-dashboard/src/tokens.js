// Design tokens, mirrored from build-and-design-docs/README.md (high fidelity).
export const C = {
  bg: '#0d1117',
  surface: '#161b22',
  surfaceDeep: '#0f1318',
  sidebar: '#090c10',
  border: '#21262d',
  borderSubtle: '#30363d',
  text: '#c9d1d9',
  textBright: '#e6edf3',
  white: '#fff',
  text2: '#8b949e',
  muted: '#484f58',
  ghost: '#3a4350',
  green: '#1DB954',
  red: '#f85149',
  amber: '#d29922',
  blue: '#58a6ff',
  purple: '#bc8cff',
};

export const fmt = (n) => (n == null ? '' : n.toLocaleString());
export const pct = (n) => `${n}%`;
