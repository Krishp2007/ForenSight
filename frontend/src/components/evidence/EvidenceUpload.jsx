import { useState, useRef } from 'react'
import { FileUp } from 'lucide-react'
import { uploadEvidence } from '../../services/evidenceService'
import { Spinner } from '../ui'
import useRole from '../../hooks/useRole'

const ACCEPTED = '.pcap,.pcapng,.cap,.db,.sqlite,.sqlite3,.csv,.json,.md5,.sha1,.sha256,.sha512,.hash,.txt,.log'

const EvidenceUpload = ({ caseId, onUploaded }) => {
  const { canUpload } = useRole()
  const [dragging, setDragging] = useState(false)
  const [hovered, setHovered] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [currentFileName, setCurrentFileName] = useState('')
  const inputRef = useRef(null)

  if (!canUpload) return null

  const handleFiles = async (fileList) => {
    if (!fileList || fileList.length === 0) return
    const file = fileList[0]
    setUploading(true)
    setError(null)
    setCurrentFileName(file.name)
    setProgress(0)
    try {
      const evidence = await uploadEvidence(caseId, file, (e) => {
        if (e.total) setProgress(Math.round((e.loaded / e.total) * 100))
      })
      if (onUploaded) onUploaded(evidence)
    } catch (e) {
      setError(`Failed uploading "${file.name}": ${e.response?.data?.detail || 'Upload failed'}`)
    } finally {
      setUploading(false)
      setProgress(0)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        handleFiles(e.dataTransfer.files)
      }}
      onClick={() => !uploading && inputRef.current?.click()}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        cursor: uploading ? 'default' : 'pointer',
        border: `2px dashed ${dragging || hovered ? 'var(--forensic-primary, #2563eb)' : 'var(--forensic-border, #cbd5e1)'}`,
        borderRadius: '20px',
        padding: '38px 24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '14px',
        background: dragging || hovered
          ? 'rgba(99, 102, 241, 0.08)'
          : 'var(--forensic-card-bg, #ffffff)',
        boxShadow: hovered
          ? '0 12px 28px -6px rgba(37, 99, 235, 0.2), 0 2px 8px rgba(0, 0, 0, 0.04)'
          : '0 2px 8px rgba(0, 0, 0, 0.04)',
        transform: hovered && !uploading ? 'translateY(-2px)' : 'translateY(0)',
        transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        style={{ display: 'none' }}
        onChange={(e) => handleFiles(e.target.files)}
      />
      {uploading ? (
        <>
          <Spinner size="lg" />
          <p style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '13.5px', margin: 0, fontWeight: '700' }}>
            Uploading <span style={{ color: 'var(--forensic-primary, #2563eb)' }}>{currentFileName}</span> ({progress}%)
          </p>
          <div style={{ width: '260px', height: '6px', background: 'var(--forensic-panel-bg, #e2e8f0)', borderRadius: '99px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${progress}%`, background: 'linear-gradient(90deg, #2563eb, #06b6d4)', borderRadius: '99px', transition: 'width 0.3s' }} />
          </div>
        </>
      ) : (
        <>
          <div style={{
            width: '56px', height: '56px',
            background: 'rgba(99, 102, 241, 0.14)',
            border: `1px solid ${hovered ? 'var(--forensic-primary, #2563eb)' : 'rgba(99, 102, 241, 0.3)'}`,
            borderRadius: '16px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--forensic-primary, #2563eb)',
            transform: hovered ? 'scale(1.08)' : 'scale(1)',
            boxShadow: hovered ? '0 0 16px rgba(37, 99, 235, 0.3)' : 'none',
            transition: 'all 0.25s ease',
          }}>
            <FileUp size={24} />
          </div>
          <p style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '14.5px', fontWeight: '700', margin: 0, letterSpacing: '-0.3px' }}>
            Drop a file or click to browse
          </p>
          <p style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', fontWeight: '600', margin: 0 }}>
            PCAP · SQLite · CSV · JSON · MD5 · TXT · LOG
          </p>
        </>
      )}
      {error && <p style={{ color: '#dc2626', fontSize: '12px', margin: '4px 0 0 0', fontWeight: '600' }}>{error}</p>}
    </div>
  )
}

export default EvidenceUpload
