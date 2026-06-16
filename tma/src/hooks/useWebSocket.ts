import { useEffect, useRef, useCallback } from 'react'
import { useAppState } from '../contexts/AppContext'
import { getInitData } from '../services/tgApi'
import type { WsChunk, WsDone, WsError } from '../types'

let messageCounter = 0

export function useWebSocket(hubUrl: string) {
  const { state, dispatch } = useAppState()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()
  const currentTaskIdRef = useRef<string>('')

  const connect = useCallback(() => {
    dispatch({ type: 'SET_WS_STATUS', payload: 'connecting' })
    const initData = getInitData()

    const ws = new WebSocket(`${hubUrl}/ws?initData=${encodeURIComponent(initData)}`)
    wsRef.current = ws

    ws.onopen = () => {
      dispatch({ type: 'SET_WS_STATUS', payload: 'connected' })
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsChunk | WsDone | WsError
        switch (data.type) {
          case 'chunk': {
            const chunk = data as WsChunk
            if (chunk.kind === 'reasoning') {
              dispatch({ type: 'APPEND_STREAM_CHUNK', payload: { reasoning: chunk.token } })
            } else {
              dispatch({ type: 'APPEND_STREAM_CHUNK', payload: { answer: chunk.token } })
            }
            break
          }
          case 'done':
            dispatch({ type: 'FINALIZE_STREAM' })
            currentTaskIdRef.current = ''
            break
          case 'error':
            dispatch({ type: 'SET_MESSAGE_ERROR', payload: (data as WsError).message })
            currentTaskIdRef.current = ''
            break
        }
      } catch { /* ignore malformed messages */ }
    }

    ws.onclose = () => {
      dispatch({ type: 'SET_WS_STATUS', payload: 'reconnecting' })
      reconnectTimeoutRef.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [dispatch])

  const sendMessage = useCallback((agentId: string, text: string) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return

    const taskId = `task_${Date.now()}_${messageCounter++}`
    currentTaskIdRef.current = taskId

    dispatch({
      type: 'ADD_MESSAGE',
      payload: {
        id: taskId,
        text: '',
        reasoning: '',
        status: 'streaming',
        timestamp: Date.now(),
      },
    })

    ws.send(JSON.stringify({
      type: 'message',
      agent_id: agentId,
      text,
      task_id: taskId,
    }))
  }, [dispatch])

  const switchAgent = useCallback((agentId: string) => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'switch_agent', agent_id: agentId }))
    }
    dispatch({ type: 'SET_ACTIVE_AGENT', payload: agentId })
  }, [dispatch])

  const newSession = useCallback(() => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'new_session', agent_id: state.activeAgentId }))
    }
    dispatch({ type: 'CLEAR_MESSAGES' })
  }, [state.activeAgentId, dispatch])

  const cancel = useCallback(() => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'cancel', agent_id: state.activeAgentId }))
    }
  }, [state.activeAgentId])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimeoutRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { sendMessage, switchAgent, newSession, cancel, currentTaskId: currentTaskIdRef.current }
}
