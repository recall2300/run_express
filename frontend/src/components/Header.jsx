import React from 'react';

const Header = ({ isRunning, onOpenSettings, isDark, onToggleTheme, activeProfile, onLogoClick }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="brand">
          <h1
            className={`logo-text${activeProfile ? ' logo-clickable' : ''}`}
            onClick={activeProfile ? onLogoClick : undefined}
            title={activeProfile ? '프로필 선택으로 돌아가기' : undefined}
          >
            런특급
          </h1>
        </div>
        <div className="header-divider" />
        <span className="header-title">RUN EXPRESS</span>
        <div className="header-divider" />
        <div className="header-actions">
          <div className={`status-pill ${isRunning ? 'running' : 'idle'}`}>
            <span className="pulse" />
            {isRunning ? 'RUNNING' : 'IDLE'}
          </div>
          <button
            className="settings-toggle"
            onClick={onToggleTheme}
            title={isDark ? '라이트 모드로 전환' : '다크 모드로 전환'}
          >
            {isDark ? '☀' : '☾'}
          </button>
          <button
            className="settings-toggle"
            onClick={onOpenSettings}
            title="설정"
            disabled={!activeProfile}
          >
            ⚙
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
