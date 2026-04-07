import type { WsEvent } from "../types/api";

type MessageHandler = (event: WsEvent) => void;

type SocketOptions = {
  onMessage: MessageHandler;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (event: Event) => void;
};

export class MajSocket {
  private ws: WebSocket | null = null;
  private heartbeatTimer: number | null = null;
  private reconnectTimer: number | null = null;
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;

  constructor(private readonly options: SocketOptions) {}

  connect(token: string): void {
    if (!token || this.ws) return;

    const rawBase = import.meta.env.VITE_WS_BASE_URL || window.location.origin;
    const wsBase = rawBase.replace(/^http/, "ws").replace(/^https/, "wss");
    const url = `${wsBase}/api/v1/ws?token=${encodeURIComponent(token)}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.options.onOpen?.();
    };

    this.ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as WsEvent;
        this.options.onMessage(parsed);
      } catch {
        // Ignore non-json messages.
      }
    };

    this.ws.onerror = (event) => {
      this.options.onError?.(event);
    };

    this.ws.onclose = () => {
      this.cleanup();
      this.options.onClose?.();
      this.tryReconnect(token);
    };
  }

  send(payload: unknown): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    this.ws.send(JSON.stringify(payload));
  }

  disconnect(): void {
    this.clearTimers();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send("ping");
      }
    }, 20000);
  }

  private tryReconnect(token: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;

    this.reconnectAttempts += 1;
    const delay = Math.min(1000 * this.reconnectAttempts, 5000);

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect(token);
    }, delay);
  }

  private cleanup(): void {
    this.clearTimers();
    this.ws = null;
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      window.clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private clearTimers(): void {
    this.clearHeartbeat();
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
