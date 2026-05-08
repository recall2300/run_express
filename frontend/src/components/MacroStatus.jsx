import React from 'react';

const MacroStatus = ({ isRunning, logs, targetTrain, onStop }) => {
  if (!isRunning && logs.length === 0) return null;

  return (
    <div className="macro-status">
      {isRunning && (
        <div className="running-indicator card">
          <div className="info">
            <span className="label">구동 중:</span>
            <span className="value">{targetTrain}호</span>
          </div>
          <button className="btn-stop" onClick={onStop}>정지하기</button>
        </div>
      )}

      <div className="logs-panel card">
        <h3 className="panel-title">활동 로그 (최신순)</h3>
        <div className="logs-container">
          {logs.map((log, i) => (
            <div key={i} className="log-entry">
              <span className="log-text">{log}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MacroStatus;
