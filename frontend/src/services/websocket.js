/**
 * Resilient WebSocket manager for stateful mock interview coaching sessions.
 */
export class InterviewWebSocket {
  constructor(threadId, onMessage, onStatusChange) {
    this.threadId = threadId;
    this.onMessage = onMessage;
    this.onStatusChange = onStatusChange;
    this.socket = null;
    this.pingInterval = null;
    this.isManualClose = false;
  }

  connect() {
    this.isManualClose = false;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/interview/${this.threadId}`;

    if (this.onStatusChange) this.onStatusChange("connecting");

    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      if (this.onStatusChange) this.onStatusChange("connected");
      // Keepalive ping every 25 seconds
      this.pingInterval = setInterval(() => {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify({ type: "ping" }));
        }
      }, 25000);
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "pong") return;
        if (this.onMessage) this.onMessage(data);
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      if (this.onStatusChange) this.onStatusChange("error");
    };

    this.socket.onclose = () => {
      if (this.pingInterval) clearInterval(this.pingInterval);
      if (this.onStatusChange) {
        this.onStatusChange(this.isManualClose ? "disconnected" : "paused");
      }
    };
  }

  sendMessage(content) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: "message", content }));
      return true;
    }
    return false;
  }

  disconnect() {
    this.isManualClose = true;
    if (this.pingInterval) clearInterval(this.pingInterval);
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}
