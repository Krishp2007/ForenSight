import Badge from '../ui/Badge'
import { statusColor, humanize } from '../../utils/formatters'

const CaseStatusBadge = ({ status }) => (
  <Badge label={humanize(status)} colorClass={statusColor(status)} />
)

export default CaseStatusBadge
