import React from 'react';

const Header = ({ isRunning, onOpenSettings }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="brand">
          <h1 className="logo-text">런특급</h1>
        </div>
        <div className="header-divider" />
        <span className="header-title">RUN EXPRESS</span>
        <div className="header-divider" />
        <div className="header-actions">
          <div className={`status-pill ${isRunning ? 'running' : 'idle'}`}>
            <span className="pulse" />
            {isRunning ? 'RUNNING' : 'IDLE'}
          </div>
          <button className="settings-toggle" onClick={onOpenSettings} title="설정">
            ⚙
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
