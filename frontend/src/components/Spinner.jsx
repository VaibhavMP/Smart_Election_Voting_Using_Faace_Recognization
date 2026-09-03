export default function Spinner({ label = 'Loading...' }) {
  return (
    <div className="status status-pending" role="status">
      {label}
    </div>
  )
}