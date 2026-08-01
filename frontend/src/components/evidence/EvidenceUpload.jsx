import { useState, useRef } from 'react'
import { Upload, FileUp } from 'lucide-react'
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
      className={`cursor-pointer border-2 border-dashed rounded-xl p-8 flex flex-col items-center gap-3 transition-colors
        ${dragging ? 'border-blue-500 bg-blue-500/10' : 'border-gray-600 hover:border-blue-500 hover:bg-gray-700/30'}`}
    >
      <input
        ref={inputRef} type="file" accept={ACCEPTED} className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />
      {uploading ? (
        <>
          <Spinner size="lg" />
          <p className="text-sm text-gray-400">Uploading… {progress}%</p>
          <div className="w-48 h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 transition-all" style={{ width: `${progress}%` }} />
          </div>
        </>
      ) : (
        <>
          <div className="p-3 bg-blue-600/20 rounded-full">
            <FileUp size={24} className="text-blue-400" />
          </div>
          <p className="text-sm text-gray-300 font-medium">Drop a file or click to browse</p>
          <p className="text-xs text-gray-500">EVTX · PCAP · SQLite · CSV · JSON</p>
        </>
      )}
      {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
    </div>
  )
}

export default EvidenceUpload
