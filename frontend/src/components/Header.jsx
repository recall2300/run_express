import React from 'react';

const Header = ({ isRunning, onOpenSettings }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="brand">
          <h1 className="logo-text">런특급</h1>
          <div className={`status-pill ${isRunning ? 'running' : 'idle'}`}>
            <span className="pulse"></span>
            {isRunning ? '매크로 동작 중' : '대기 중'}
          </div>
        </div>
        <button className="settings-toggle" onClick={onOpenSettings} title="설정">
          <span className="icon">⚙️</span>
        </button>
      </div>
      <p className="subtitle">Korail & SRT Auto Reservation System</p>
    </header>
  );
};

export default Header;
