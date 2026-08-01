import { useState, useRef } from 'react'
import { FileUp } from 'lucide-react'
import { uploadEvidence } from '../../services/evidenceService'
import Spinner from '../ui/Spinner'

const ACCEPTED = '.evtx,.pcap,.pcapng,.db,.sqlite,.csv,.json'

const EvidenceUpload = ({ caseId, onUploaded }) => {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  const handleFile = async (file) => {
    if (!file) return
    setUploading(true)
    setError(null)
    setProgress(0)
    try {
      const evidence = await uploadEvidence(caseId, file, (e) => {
        setProgress(Math.round((e.loaded / e.total) * 100))
      })
      onUploaded(evidence)
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }}
      onClick={() => !uploading && inputRef.current?.click()}
      style={{
        cursor: uploading ? 'default' : 'pointer',
        border: `2px dashed ${dragging ? '#4a7fe8' : '#3d4f6a'}`,
        borderRadius: '12px',
        padding: '32px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '12px',
        background: dragging ? 'rgba(74,127,232,0.08)' : '#2a3347',
        transition: 'border-color 0.2s, background 0.2s',
      }}
      onMouseEnter={e => { if (!uploading && !dragging) { e.currentTarget.style.borderColor = '#4a7fe8'; e.currentTarget.style.background = 'rgba(74,127,232,0.05)' } }}
      onMouseLeave={e => { if (!dragging) { e.currentTarget.style.borderColor = '#3d4f6a'; e.currentTarget.style.background = '#2a3347' } }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        style={{ display: 'none' }}
        onChange={(e) => handleFile(e.target.files[0])}
      />
      {uploading ? (
        <>
          <Spinner size="lg" />
          <p style={{ color: '#9aa8c0', fontSize: '13px', margin: 0 }}>Uploading… {progress}%</p>
          <div style={{ width: '192px', height: '6px', background: '#3d4f6a', borderRadius: '99px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${progress}%`, background: '#4a7fe8', borderRadius: '99px', transition: 'width 0.3s' }} />
          </div>
        </>
      ) : (
        <>
          <div style={{
            width: '52px', height: '52px',
            background: 'rgba(74,127,232,0.15)',
            borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <FileUp size={22} color="#60a5fa" />
          </div>
          <p style={{ color: '#ffffff', fontSize: '13px', fontWeight: '500', margin: 0 }}>
            Drop a file or click to browse
          </p>
          <p style={{ color: '#6b7fa3', fontSize: '11px', margin: 0 }}>
            EVTX · PCAP · SQLite · CSV · JSON
          </p>
        </>
      )}
      {error && <p style={{ color: '#fca5a5', fontSize: '12px', margin: '4px 0 0 0' }}>{error}</p>}
    </div>
  )
}

export default EvidenceUpload
