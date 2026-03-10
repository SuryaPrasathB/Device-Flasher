import React, { createContext, useContext, useState, useEffect, useRef } from 'react';

const AppContext = createContext();

export const useAppContext = () => useContext(AppContext);

export const AppProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [isAuthenticated, setIsAuthenticated] = useState(!!token);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [state, setState] = useState({
    logs: [],
    port: null,
    tabs: {
      set_id: { old_id: 1, new_id: 2, status: 'Idle', log: '' },
      slave_tester: { status: 'Idle', log: '', results: {} },
      stress_tester: {
        is_running: false,
        from_id: 1,
        to_id: 10,
        reg: 0,
        delay_ms: 1000,
        data_type: 'Integer (16-bit)',
        total_hits: 0,
        success: 0,
        failure: 0,
        failure_percent: '0.00%',
        max_fail_id: '-'
      }
    }
  });

  const ws = useRef(null);

  const login = async (pin) => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin }),
      });
      if (response.ok) {
        const data = await response.json();
        setToken(data.token);
        localStorage.setItem('token', data.token);
        setIsAuthenticated(true);
        return true;
      }
      return false;
    } catch (e) {
      console.error("Login failed:", e);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    if (ws.current) {
      ws.current.close();
    }
  };

  const connectWebSocket = () => {
    if (!token) return;

    // Construct WebSocket URL handling http/https -> ws/wss
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws?token=${token}`;

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log("WebSocket connected");
      setConnectionStatus('connected');
      // Request full state immediately
      sendAction('request_state', {});
    };

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'state_update') {
          // Merge incoming state with current state deeply
          setState(prevState => {
            const newState = { ...prevState };
            const payload = message.data;

            // Handle logs separately to append
            if (payload.log) {
               newState.logs = [...newState.logs, payload.log].slice(-50); // Keep last 50
            }

            if (payload.port !== undefined) newState.port = payload.port;

            if (payload.tabs) {
               // Deep merge tabs
               for (const [tabKey, tabData] of Object.entries(payload.tabs)) {
                  if (newState.tabs[tabKey]) {
                     newState.tabs[tabKey] = { ...newState.tabs[tabKey], ...tabData };
                  }
               }
            }
            return newState;
          });
        }
      } catch (e) {
        console.error("Error parsing WS message:", e);
      }
    };

    ws.current.onclose = () => {
      console.log("WebSocket disconnected");
      setConnectionStatus('disconnected');
      // Attempt reconnect after 3 seconds if still authenticated
      if (isAuthenticated) {
        setTimeout(connectWebSocket, 3000);
      }
    };

    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  };

  useEffect(() => {
    if (isAuthenticated) {
      connectWebSocket();
    }
    return () => {
      if (ws.current) ws.current.close();
    };
  }, [isAuthenticated, token]);

  const sendAction = (action, payload) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action, payload }));
    } else {
      console.warn("WebSocket not open, cannot send action:", action);
    }
  };

  return (
    <AppContext.Provider value={{ state, isAuthenticated, connectionStatus, login, logout, sendAction }}>
      {children}
    </AppContext.Provider>
  );
};
