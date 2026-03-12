import React, { useState } from 'react';
import { useAppContext } from '../AppContext';
import { Settings2, ArrowRight } from 'lucide-react';

const SetIDTab = () => {
  const { state, sendAction } = useAppContext();
  const { id, status } = state.tabs.set_id || {};
  const isFlashing = status?.includes('Flashing');

  const [localId, setLocalId] = useState(id || 1);

  // Sync with incoming state changes from the PC
  React.useEffect(() => {
    if (id !== undefined) {
      setLocalId(id);
    }
  }, [id]);

  const handleSetID = () => {
    sendAction('set_slave_id', { id: localId });
  };

  return (
    <div className="p-4 space-y-6">
      <div className="bg-gray-800 rounded-lg p-5 border border-gray-700 shadow-sm">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
          <Settings2 className="mr-2 text-blue-400" />
          Set Device ID
        </h2>

        <div className="grid grid-cols-1 gap-4 items-center">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-400">Device ID</label>
            <input
              type="number"
              min="1" max="247"
              value={localId}
              onChange={(e) => setLocalId(parseInt(e.target.value) || 1)}
              className="w-full bg-gray-900 border border-blue-500/50 rounded p-3 text-blue-400 text-lg font-bold font-mono focus:ring-2 focus:ring-blue-500 outline-none shadow-[0_0_10px_rgba(59,130,246,0.2)]"
            />
          </div>
        </div>

        <button
          onClick={handleSetID}
          disabled={!state.port || isFlashing}
          className={`mt-6 w-full py-4 px-4 rounded-md font-bold text-lg flex items-center justify-center transition-colors ${!state.port
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : isFlashing
                ? 'bg-yellow-600 text-white cursor-wait animate-pulse'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg'
            }`}
        >
          {isFlashing ? status : (
            <>
              Apply New ID <ArrowRight className="ml-2 w-5 h-5" />
            </>
          )}
        </button>

        {!state.port && (
          <p className="text-red-400 text-sm text-center mt-3 bg-red-900/20 py-2 rounded">
            Cannot flash: No COM Port connected
          </p>
        )}
      </div>

      <div className="bg-gray-900 p-4 rounded-lg font-mono text-sm h-32 overflow-y-auto border border-gray-700 shadow-inner">
        {state.tabs.set_id.log ? (
          <div dangerouslySetInnerHTML={{ __html: state.tabs.set_id.log }}></div>
        ) : (
          <span className="text-gray-500">Ready to set ID...</span>
        )}
      </div>
    </div>
  );
};

export default SetIDTab;
