import { useState, useRef } from 'react'
import { FileUp } from 'lucide-react'
import { uploadEvidence } from '../../services/evidenceService'
import { Spinner } from '../ui'
import useRole from '../../hooks/useRole'

const ACCEPTED = '.evtx,.pcap,.pcapng,.cap,.db,.sqlite,.sqlite3,.csv,.json,.md5,.sha1,.sha256,.sha512,.hash,.txt,.log'

const EvidenceUpload = ({ caseId, onUploaded }) => {
  const { canUpload } = useRole()
  const [dragging, setDragging] = useState(false)
  const [hovered, setHovered] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  // Viewers see nothing — upload is investigator/admin only
  if (!canUpload) return null

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
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        cursor: uploading ? 'default' : 'pointer',
        border: `2px dashed ${dragging || hovered ? '#6366f1' : 'rgba(255, 255, 255, 0.12)'}`,
        borderRadius: '16px',
        padding: '36px 24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '14px',
        background: dragging || hovered 
          ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(15, 23, 42, 0.6))' 
          : 'rgba(30, 41, 59, 0.55)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        boxShadow: hovered 
          ? '0 12px 28px -6px rgba(99, 102, 241, 0.25), 0 0 20px rgba(99, 102, 241, 0.15)' 
          : '0 4px 14px rgba(0, 0, 0, 0.25)',
        transform: hovered && !uploading ? 'translateY(-2px)' : 'translateY(0)',
        transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
      }}
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
          <p style={{ color: '#cbd5e1', fontSize: '13px', margin: 0, fontWeight: '500' }}>Uploading… {progress}%</p>
          <div style={{ width: '220px', height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '99px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${progress}%`, background: 'linear-gradient(90deg, #6366f1, #06b6d4)', borderRadius: '99px', transition: 'width 0.3s' }} />
          </div>
        </>
      ) : (
        <>
          <div style={{
            width: '56px', height: '56px',
            background: hovered ? 'rgba(99, 102, 241, 0.25)' : 'rgba(99, 102, 241, 0.15)',
            border: `1px solid ${hovered ? 'rgba(99, 102, 241, 0.5)' : 'rgba(99, 102, 241, 0.3)'}`,
            borderRadius: '16px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: hovered ? '#ffffff' : '#818cf8',
            transform: hovered ? 'scale(1.08)' : 'scale(1)',
            boxShadow: hovered ? '0 0 16px rgba(99, 102, 241, 0.35)' : 'none',
            transition: 'all 0.3s ease',
          }}>
            <FileUp size={24} />
          </div>
          <p style={{ color: '#ffffff', fontSize: '14px', fontWeight: '600', margin: 0 }}>
            Drop a file or click to browse
          </p>
          <p style={{ color: '#94a3b8', fontSize: '11.5px', margin: 0 }}>
            EVTX · PCAP · SQLite · CSV · JSON · MD5 · TXT · LOG
          </p>
        </>
      )}
      {error && <p style={{ color: '#fca5a5', fontSize: '12px', margin: '4px 0 0 0' }}>{error}</p>}
    </div>
  )
}

export default EvidenceUpload
