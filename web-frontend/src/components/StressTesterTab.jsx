import React, { useState } from 'react';
import { useAppContext } from '../AppContext';
import { Gauge, StopCircle, PlayCircle, Hash, Clock, Database, CheckCircle, XOctagon } from 'lucide-react';

const StressTesterTab = () => {
  const { state, sendAction } = useAppContext();
  const {
    is_running,
    from_id,
    to_id,
    reg,
    delay_ms,
    data_type,
    total_hits,
    success,
    failure,
    failure_percent,
    max_fail_id
  } = state.tabs.stress_tester;

  const [localFromId, setLocalFromId] = useState(from_id);
  const [localToId, setLocalToId] = useState(to_id);
  const [localReg, setLocalReg] = useState(reg);
  const [localDelayMs, setLocalDelayMs] = useState(delay_ms);
  const [localDataType, setLocalDataType] = useState(data_type);

  // Sync with incoming state changes from the PC (Two-way sync)
  React.useEffect(() => {
    // Only update local state if the test is NOT running locally to avoid UI jitter
    if (!is_running) {
      setLocalFromId(from_id);
      setLocalToId(to_id);
      setLocalReg(reg);
      setLocalDelayMs(delay_ms);
      setLocalDataType(data_type);
    }
  }, [from_id, to_id, reg, delay_ms, data_type, is_running]);

  const toggleTest = () => {
    if (is_running) {
      sendAction('stop_stress_tester', {});
    } else {
      sendAction('start_stress_tester', {
        from_id: localFromId,
        to_id: localToId,
        reg: localReg,
        delay_ms: localDelayMs,
        data_type: localDataType
      });
    }
  };

  const statCardClass = "bg-gray-700/50 rounded-lg p-4 flex flex-col items-center justify-center border border-gray-600 shadow-sm relative overflow-hidden";
  const statLabelClass = "text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1 z-10";
  const statValueClass = "text-2xl font-bold font-mono z-10";

  return (
    <div className="p-4 space-y-6">
      <div className="bg-gray-800 rounded-lg p-5 border border-gray-700 shadow-sm">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-white flex items-center">
            <Gauge className="mr-2 text-purple-400" />
            Network Stress Tester
          </h2>
          {is_running && (
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="space-y-1">
            <label className="text-xs text-gray-400 font-medium">From ID</label>
            <div className="relative">
              <Hash className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 w-4 h-4" />
              <input
                type="number" min="1" max="247"
                value={localFromId} onChange={e => setLocalFromId(parseInt(e.target.value)||1)}
                disabled={is_running}
                className="w-full bg-gray-900 border border-gray-600 rounded p-2 pl-9 text-white font-mono outline-none disabled:opacity-50"
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-gray-400 font-medium">To ID</label>
            <div className="relative">
              <Hash className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 w-4 h-4" />
              <input
                type="number" min="1" max="247"
                value={localToId} onChange={e => setLocalToId(parseInt(e.target.value)||1)}
                disabled={is_running}
                className="w-full bg-gray-900 border border-gray-600 rounded p-2 pl-9 text-white font-mono outline-none disabled:opacity-50"
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-gray-400 font-medium">Target Register</label>
            <div className="relative">
              <Database className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 w-4 h-4" />
              <input
                type="number" min="0" max="65535"
                value={localReg} onChange={e => setLocalReg(parseInt(e.target.value)||0)}
                disabled={is_running}
                className="w-full bg-gray-900 border border-gray-600 rounded p-2 pl-9 text-white font-mono outline-none disabled:opacity-50"
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-gray-400 font-medium">Delay (ms)</label>
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 w-4 h-4" />
              <input
                type="number" min="0" step="50"
                value={localDelayMs} onChange={e => setLocalDelayMs(parseInt(e.target.value)||0)}
                disabled={is_running}
                className="w-full bg-gray-900 border border-gray-600 rounded p-2 pl-9 text-white font-mono outline-none disabled:opacity-50"
              />
            </div>
          </div>
          <div className="space-y-1 col-span-2">
            <label className="text-xs text-gray-400 font-medium">Data Type</label>
            <select
              value={localDataType} onChange={e => setLocalDataType(e.target.value)}
              disabled={is_running}
              className="w-full bg-gray-900 border border-gray-600 rounded p-2 text-white font-mono outline-none disabled:opacity-50"
            >
              <option>Integer (16-bit)</option>
              <option>Float (32-bit)</option>
              <option>Coil</option>
            </select>
          </div>
        </div>

        <button
          onClick={toggleTest}
          disabled={!state.port && !is_running}
          className={`w-full py-4 px-4 rounded-md font-bold text-lg flex items-center justify-center transition-colors shadow-lg ${
            !state.port && !is_running
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : is_running
                ? 'bg-red-600 hover:bg-red-500 text-white animate-pulse'
                : 'bg-purple-600 hover:bg-purple-500 text-white'
          }`}
        >
          {is_running ? <><StopCircle className="mr-2" /> Stop Stress Test</> : <><PlayCircle className="mr-2" /> Start Stress Test</>}
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg p-5 border border-gray-700 shadow-sm">
        <h3 className="text-lg font-semibold text-white mb-4 border-b border-gray-700 pb-2">Live Statistics</h3>

        <div className="grid grid-cols-2 gap-4">
          <div className={statCardClass}>
            <div className="absolute inset-0 bg-blue-500/5"></div>
            <span className={statLabelClass}>Total Hits</span>
            <span className={`${statValueClass} text-blue-400`}>{total_hits}</span>
          </div>

          <div className={statCardClass}>
            <div className="absolute inset-0 bg-red-500/5"></div>
            <span className={statLabelClass}>Fail Rate</span>
            <span className={`${statValueClass} ${parseFloat(failure_percent) > 0 ? 'text-red-400' : 'text-gray-300'}`}>{failure_percent}</span>
          </div>

          <div className={statCardClass}>
            <div className="absolute inset-0 bg-green-500/5"></div>
            <span className={statLabelClass}>Success</span>
            <span className={`${statValueClass} text-green-400 flex items-center`}><CheckCircle className="w-5 h-5 mr-2 opacity-50"/>{success}</span>
          </div>

          <div className={statCardClass}>
            <div className="absolute inset-0 bg-red-500/5"></div>
            <span className={statLabelClass}>Failures</span>
            <span className={`${statValueClass} ${failure > 0 ? 'text-red-500' : 'text-gray-400'} flex items-center`}><XOctagon className="w-5 h-5 mr-2 opacity-50"/>{failure}</span>
          </div>

          <div className={`${statCardClass} col-span-2 mt-2 bg-gray-900/50 border-gray-700`}>
            <span className="text-xs text-gray-500 uppercase font-bold mb-1">Max Failure Device</span>
            <span className="text-xl font-mono text-yellow-500 font-bold bg-yellow-900/20 px-4 py-1 rounded border border-yellow-700/50 shadow-inner">
              {max_fail_id}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StressTesterTab;
