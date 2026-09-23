import type { CSSProperties } from 'react'

export const colors = {
  bg: '#1e2318', bgDeep: '#181d14', border: '#2a3d2b', moss: '#3d5a3e', mossLight: '#7a9e6a',
  mossDim: '#5c7a50', text: '#e8e0d0', textSoft: '#c8c0a8', textMuted: '#8a8070', plum: '#3a1e38',
  danger: '#b25a4a',
}
export const label: CSSProperties = { fontSize: '0.8rem', letterSpacing: '0.3em', textTransform: 'uppercase', color: colors.mossDim, marginBottom: '0.75rem' }
export const heading: CSSProperties = { fontSize: 'clamp(2rem, 5vw, 3rem)', color: colors.textSoft, margin: '0 0 1.5rem' }
export const card: CSSProperties = { border: `1px solid ${colors.border}`, padding: '1.5rem', background: colors.bg }
export const button: CSSProperties = { border: `1px solid ${colors.moss}`, color: colors.mossLight, background: 'transparent', padding: '0.65rem 1.5rem', letterSpacing: '0.12em', fontSize: '0.9rem', cursor: 'pointer', fontFamily: 'inherit' }
export const buttonPrimary: CSSProperties = { ...button, background: colors.moss, color: colors.text }
export const input: CSSProperties = { width: '100%', background: '#141810', border: `1px solid ${colors.border}`, color: colors.text, padding: '0.6rem 0.8rem', fontFamily: 'inherit', fontSize: '1rem' }
