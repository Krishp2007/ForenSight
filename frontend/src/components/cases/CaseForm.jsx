import { useState } from 'react'
import { CASE_STATUSES } from '../../utils/constants'
import { humanize } from '../../utils/formatters'
import Spinner from '../ui/Spinner'

const CaseForm = ({ initial = {}, onSubmit, onCancel, loading }) => {
  const [title, setTitle] = useState(initial.title || '')
  const [description, setDescription] = useState(initial.description || '')
  const [status, setStatus] = useState(initial.status || 'open')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({ title, description, status })
  }

  const inputCls = 'w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:border-blue-500'
  const labelCls = 'block text-xs text-gray-400 mb-1 font-medium'

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div>
        <label className={labelCls}>Title *</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required minLength={3} maxLength={150}
          className={inputCls}
          placeholder="e.g. APT29 Phishing Investigation"
        />
      </div>
      <div>
        <label className={labelCls}>Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className={`${inputCls} resize-none`}
          placeholder="Optional case scope or incident details…"
        />
      </div>
      {initial.id && (
        <div>
          <label className={labelCls}>Status</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className={inputCls}
          >
            {CASE_STATUSES.map((s) => (
              <option key={s} value={s}>{humanize(s)}</option>
            ))}
          </select>
        </div>
      )}
      <div className="flex gap-3 justify-end pt-2">
        <button
          type="button" onClick={onCancel}
          className="px-4 py-2 text-sm rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700"
        >
          Cancel
        </button>
        <button
          type="submit" disabled={loading}
          className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          {loading && <Spinner size="sm" />}
          {initial.id ? 'Update Case' : 'Create Case'}
        </button>
      </div>
    </form>
  )
}

export default CaseForm
