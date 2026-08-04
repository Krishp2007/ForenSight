/**
 * parseTimerStore — persists parse start timestamps across navigation.
 *
 * When an evidence item enters "parsing" status, we record Date.now() here.
 * Because this store lives outside any component, unmounting EvidenceList
 * does NOT reset the timers — they keep running correctly when you come back.
 */
import { create } from 'zustand'

const useParseTimerStore = create((set, get) => ({
  // { [evidenceId]: startMs }
  startTimes: {},

  /**
   * Call when status becomes "parsing".
   * Uses the server's parsing_started_at if available and recent (< 10 min ago),
   * otherwise falls back to Date.now() so the counter always starts from ~0.
   */
  markStarted: (evidenceId, serverStartedAt) => {
    const existing = get().startTimes[evidenceId]
    if (existing) return

    const parseUtc = (d) => {
      if (!d) return null
      const str = String(d).trim()
      const isoStr = (str.includes('Z') || str.includes('+') || (str.length > 10 && str.lastIndexOf('-') > 10)) ? str : str + 'Z'
      const ms = new Date(isoStr).getTime()
      return isNaN(ms) ? null : ms
    }

    const serverMs = serverStartedAt ? parseUtc(serverStartedAt) : null
    const now = Date.now()
    const startMs = (serverMs && Math.abs(now - serverMs) < 10 * 60 * 1000) ? serverMs : now

    set(state => ({
      startTimes: { ...state.startTimes, [evidenceId]: startMs },
    }))
  },

  /** Force reset timer for re-processing */
  resetTimer: (evidenceId, startMs = Date.now()) => {
    set(state => ({
      startTimes: { ...state.startTimes, [evidenceId]: startMs },
    }))
  },

  /** Call when status reaches a terminal state (parsed / failed). */
  markDone: (evidenceId) => {
    set(state => {
      const next = { ...state.startTimes }
      delete next[evidenceId]
      return { startTimes: next }
    })
  },

  getStartMs: (evidenceId) => get().startTimes[evidenceId] ?? null,
}))

export default useParseTimerStore
