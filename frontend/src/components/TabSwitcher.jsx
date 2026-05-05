import React from 'react';

const TabSwitcher = ({ activeTab, onTabChange }) => {
  return (
    <div className="tab-switcher">
      <button 
        className={`tab-btn ${activeTab === 'KTX' ? 'active' : ''}`} 
        onClick={() => onTabChange('KTX')}
      >
        <span className="icon">🚆</span> KTX / 일반
      </button>
      <button 
        className={`tab-btn ${activeTab === 'SRT' ? 'active' : ''}`} 
        onClick={() => onTabChange('SRT')}
      >
        <span className="icon">🚅</span> SRT
      </button>
    </div>
  );
};

export default TabSwitcher;
