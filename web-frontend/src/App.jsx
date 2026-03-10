import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, NavLink } from 'react-router-dom';
import { AppProvider, useAppContext } from './AppContext';
import Login from './components/Login';
import SetIDTab from './components/SetIDTab';
import SlaveTesterTab from './components/SlaveTesterTab';
import StressTesterTab from './components/StressTesterTab';
import { LogOut, Activity, Settings2, Gauge, Wifi, WifiOff, Terminal } from 'lucide-react';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAppContext();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
};

const Navigation = () => {
  const navClass = ({ isActive }) =>
    `flex flex-col items-center justify-center p-3 w-1/3 text-xs font-semibold transition-colors border-b-2 ${
      isActive
        ? 'text-blue-400 border-blue-500 bg-gray-800'
        : 'text-gray-400 border-transparent hover:bg-gray-800/50 hover:text-gray-300'
    }`;

  return (
    <nav className="flex bg-gray-900 border-b border-gray-700 shadow-md sticky top-0 z-50">
      <NavLink to="/set-id" className={navClass}>
        <Settings2 className="w-5 h-5 mb-1" />
        Set ID
      </NavLink>
      <NavLink to="/slave-tester" className={navClass}>
        <Activity className="w-5 h-5 mb-1" />
        Slave Tester
      </NavLink>
      <NavLink to="/stress-tester" className={navClass}>
        <Gauge className="w-5 h-5 mb-1" />
        Stress Tester
      </NavLink>
    </nav>
  );
};

const Header = () => {
  const { connectionStatus, logout, state } = useAppContext();

  return (
    <header className="bg-gray-800 text-white p-4 flex justify-between items-center border-b border-gray-700 shadow-sm relative">
      <div className="flex items-center space-x-3">
        <div className="bg-blue-900 p-2 rounded text-blue-400 shadow-inner">
          {connectionStatus === 'connected' ? <Wifi className="w-5 h-5" /> : <WifiOff className="w-5 h-5 text-red-400" />}
        </div>
        <div>
          <h1 className="font-bold text-lg leading-tight tracking-wide">LDU Remote</h1>
          <div className="flex items-center space-x-2 text-xs">
            <span className={`flex w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-green-500 shadow-[0_0_5px_#22c55e]' : 'bg-red-500'}`}></span>
            <span className={connectionStatus === 'connected' ? 'text-green-400 font-medium' : 'text-red-400 font-medium'}>
              {connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
            </span>
            <span className="text-gray-500">|</span>
            <span className="text-gray-400 font-mono font-medium truncate max-w-[120px]" title={state.port || 'No COM Port'}>
              {state.port || 'No COM Port'}
            </span>
          </div>
        </div>
      </div>

      <button
        onClick={logout}
        className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
        title="Logout"
      >
        <LogOut className="w-5 h-5" />
      </button>
    </header>
  );
};

const GlobalLogs = () => {
  const { state } = useAppContext();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 shadow-[0_-4px_15px_-3px_rgba(0,0,0,0.5)] z-40 transition-transform duration-300">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-2 flex items-center justify-center text-xs font-semibold text-gray-400 hover:text-gray-300 hover:bg-gray-800 uppercase tracking-widest border-b border-gray-800"
      >
        <Terminal className="w-4 h-4 mr-2 text-gray-500" />
        {isOpen ? 'Hide Terminal' : 'Show Terminal'}
      </button>

      {isOpen && (
        <div className="h-48 overflow-y-auto p-3 font-mono text-xs bg-black text-gray-300">
          {state.logs.length === 0 ? (
            <span className="text-gray-600 italic">No logs received yet...</span>
          ) : (
            state.logs.map((log, i) => (
              <div key={i} className="mb-1 pb-1 border-b border-gray-800/50" dangerouslySetInnerHTML={{ __html: log }} />
            ))
          )}
        </div>
      )}
    </div>
  );
};

const MainApp = () => {
  return (
    <div className="min-h-screen bg-gray-900 pb-16 flex flex-col font-sans">
      <Header />
      <Navigation />
      <main className="flex-grow max-w-lg mx-auto w-full relative">
        <div className="absolute inset-0 bg-gradient-to-b from-gray-800/50 to-transparent pointer-events-none -z-10"></div>
        <Routes>
          <Route path="/" element={<Navigate to="/set-id" replace />} />
          <Route path="/set-id" element={<SetIDTab />} />
          <Route path="/slave-tester" element={<SlaveTesterTab />} />
          <Route path="/stress-tester" element={<StressTesterTab />} />
        </Routes>
      </main>
      <GlobalLogs />
    </div>
  );
};

function App() {
  return (
    <AppProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <MainApp />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AppProvider>
  );
}

export default App;
