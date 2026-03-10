import React, { useState } from 'react';
import { useAppContext } from '../AppContext';
import { Lock } from 'lucide-react';

const Login = () => {
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const { login } = useAppContext();

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!pin) {
      setError('Please enter PIN');
      return;
    }
    const success = await login(pin);
    if (!success) {
      setError('Invalid PIN code');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="bg-gray-800 p-8 rounded-lg shadow-xl w-full max-w-sm border border-gray-700">
        <div className="flex flex-col items-center mb-6">
          <div className="bg-blue-900 p-3 rounded-full mb-3">
            <Lock className="text-blue-400 w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-white text-center">LDU Remote</h1>
          <p className="text-gray-400 text-sm mt-1">Enter PIN to access</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <input
              type="password"
              placeholder="••••"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 text-white text-center text-2xl tracking-widest px-4 py-3 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              maxLength={10}
              autoFocus
            />
          </div>

          {error && <div className="text-red-400 text-sm text-center font-medium bg-red-900/30 py-2 rounded">{error}</div>}

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-md transition duration-200"
          >
            Connect
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
