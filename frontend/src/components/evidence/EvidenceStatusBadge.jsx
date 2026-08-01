import Badge from '../ui/Badge'
import { evidenceStatusColor, humanize } from '../../utils/formatters'

const EvidenceStatusBadge = ({ status }) => (
  <Badge label={humanize(status)} colorClass={evidenceStatusColor(status)} />
)

export default EvidenceStatusBadge
