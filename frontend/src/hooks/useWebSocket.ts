import { useState, useEffect, useCallback, useRef } from 'react'

interface WebSocketMessage {
  type: string
  thread_id?: string
  status?: string
  state?: any
  data?: any
  approval_type?: string
}

interface UseWebSocketOptions {
  threadId?: string
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export function useWebSocket({
  threadId,
  onMessage,
  onConnect,
  onDisconnect,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    if (!threadId) return

    // Determine WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/ws/${threadId}`

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        setIsConnected(true)
        reconnectAttemptsRef.current = 0
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        onDisconnect?.()

        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++
            connect()
          }, reconnectInterval)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }, [threadId, onMessage, onConnect, onDisconnect, reconnectInterval, maxReconnectAttempts])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  const ping = useCallback(() => {
    sendMessage({ type: 'ping' })
  }, [sendMessage])

  const requestState = useCallback(() => {
    sendMessage({ type: 'get_state' })
  }, [sendMessage])

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  // Periodic ping to keep connection alive
  useEffect(() => {
    if (!isConnected) return

    const interval = setInterval(() => {
      ping()
    }, 25000) // Ping every 25 seconds

    return () => clearInterval(interval)
  }, [isConnected, ping])

  return {
    isConnected,
    lastMessage,
    sendMessage,
    requestState,
    disconnect,
    reconnect: connect,
  }
}

// Hook for subscribing to all approval notifications
export function useApprovalNotifications(
  onNewApproval?: (threadId: string, approvalType: string) => void
) {
  const [approvals, setApprovals] = useState<Array<{
    threadId: string
    approvalType: string
    timestamp: Date
  }>>([])

  // This would connect to a global WebSocket endpoint
  // For now, we'll use polling via the existing API

  useEffect(() => {
    // Could implement a global WebSocket connection here
    // For MVP, the Approvals page already polls for updates
  }, [])

  return { approvals }
}
