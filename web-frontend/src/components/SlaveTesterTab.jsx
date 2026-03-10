import React, { useState } from 'react';
import { useAppContext } from '../AppContext';
import { Activity, Play, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

const SlaveTesterTab = () => {
  const { state, sendAction } = useAppContext();
  const { status, results } = state.tabs.slave_tester;
  const isTesting = status.includes('Testing');

  const [testId, setTestId] = useState(1);

  const startTest = () => {
    sendAction('start_slave_tester', { slave_id: testId });
  };

  return (
    <div className="p-4 space-y-6">
      <div className="bg-gray-800 rounded-lg p-5 border border-gray-700 shadow-sm">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
          <Activity className="mr-2 text-green-400" />
          Single Slave Tester
        </h2>

        <div className="flex flex-col space-y-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-400">Slave ID to Test</label>
            <input
              type="number"
              min="1" max="247"
              value={testId}
              onChange={(e) => setTestId(parseInt(e.target.value) || 1)}
              className="w-full bg-gray-900 border border-gray-600 rounded p-3 text-white text-lg font-mono focus:ring-2 focus:ring-green-500 outline-none"
            />
          </div>

          <button
            onClick={startTest}
            disabled={!state.port || isTesting}
            className={`w-full py-4 px-4 rounded-md font-bold text-lg flex items-center justify-center transition-colors ${
              !state.port
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : isTesting
                  ? 'bg-yellow-600 text-white cursor-wait animate-pulse'
                  : 'bg-green-600 hover:bg-green-500 text-white shadow-lg'
            }`}
          >
            {isTesting ? <><RefreshCw className="mr-2 animate-spin" /> {status}</> : <><Play className="mr-2" /> Start Test</>}
          </button>
        </div>

        {!state.port && (
          <p className="text-red-400 text-sm text-center mt-3 bg-red-900/20 py-2 rounded">
            Cannot test: No COM Port connected
          </p>
        )}
      </div>

      <div className="bg-gray-800 rounded-lg border border-gray-700 shadow-sm overflow-hidden">
        <div className="bg-gray-700 px-4 py-2 border-b border-gray-600">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Test Results</h3>
        </div>
        <div className="p-0">
          <table className="w-full text-left text-sm text-gray-400">
            <thead className="bg-gray-900 text-gray-500 font-medium">
              <tr>
                <th className="px-4 py-3 border-b border-gray-700">Parameter</th>
                <th className="px-4 py-3 border-b border-gray-700 text-right">Value/Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700 font-mono">
              {Object.entries(results).length === 0 ? (
                <tr><td colSpan="2" className="px-4 py-6 text-center text-gray-600">No test results yet. Run a test.</td></tr>
              ) : (
                Object.entries(results).map(([key, value]) => (
                  <tr key={key} className="hover:bg-gray-700/50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-300">{key}</td>
                    <td className="px-4 py-3 text-right">
                      {value === "PASS" || value === "true" ? (
                        <span className="inline-flex items-center text-green-400 font-bold bg-green-900/30 px-2 py-1 rounded">
                          <CheckCircle className="w-4 h-4 mr-1" /> {value}
                        </span>
                      ) : value === "FAIL" || value === "ERR" || value === "false" ? (
                        <span className="inline-flex items-center text-red-400 font-bold bg-red-900/30 px-2 py-1 rounded">
                          <XCircle className="w-4 h-4 mr-1" /> {value}
                        </span>
                      ) : (
                        <span className="text-white bg-gray-900 px-2 py-1 rounded border border-gray-600 shadow-inner">{value}</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SlaveTesterTab;
