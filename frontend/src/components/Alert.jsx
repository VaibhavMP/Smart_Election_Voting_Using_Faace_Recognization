export default function Alert({ type = 'info', children }) {
  if (!children) return null
  return <div className={`alert alert-${type}`}>{children}</div>
}