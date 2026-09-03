export function mask(value, keep = 4) {
  if (!value) return ''
  if (value.length <= keep) return value
  return value.slice(0, keep) + '*'.repeat(Math.max(value.length - keep, 4))
}