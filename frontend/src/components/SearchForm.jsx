import React from 'react';

const SearchForm = ({ 
  config, 
  activeTab, 
  stations, 
  validArrivals, 
  onChange, 
  onSearch, 
  isSearching,
  hasResults,
  activeProfile,
  onResetProfile
}) => {
  const formattedDate = config.date.length >= 8 
    ? `${config.date.slice(0,4)}-${config.date.slice(4,6)}-${config.date.slice(6,8)}` 
    : '';

  return (
    <div className="search-form card">
      <div className="profile-header">
        <span className="user-badge">👤 {activeProfile}님</span>
        <button className="btn-text" onClick={onResetProfile}>프로필 변경</button>
      </div>
      
      <div className="input-grid">
        <div className="input-field">
          <label>출발역</label>
          <select name="dep" value={config.dep} onChange={onChange}>
            {stations.map(st => <option key={st} value={st}>{st}</option>)}
          </select>
        </div>
        
        <div className="input-field">
          <label>도착역</label>
          <select name="arr" value={config.arr} onChange={onChange}>
            {validArrivals.map(st => <option key={st} value={st}>{st}</option>)}
          </select>
        </div>
        
        <div className="input-field">
          <label>출발 일자</label>
          <input 
            type="date" 
            value={formattedDate} 
            onChange={(e) => onChange({ target: { name: 'date', value: e.target.value.replace(/-/g, '') } })} 
          />
        </div>

        <div className="input-field">
          <label>출발 시간</label>
          <select 
            name="time" 
            value={config.time.slice(0, 2)} 
            onChange={(e) => onChange({ target: { name: 'time', value: e.target.value + '0000' } })}
          >
            {Array.from({ length: 24 }, (_, i) => i).map(h => {
              const hour = h.toString().padStart(2, '0');
              return <option key={hour} value={hour}>{hour}시 이후</option>;
            })}
          </select>
        </div>

        <button 
          className="btn-primary search-btn" 
          onClick={onSearch} 
          disabled={isSearching}
        >
          {isSearching ? (
            <div className="searching-container">
              <span className="spinner"></span>
              조회 중...
            </div>
          ) : (
            hasResults ? '다시 조회하기' : '열차 조회하기'
          )}
        </button>
      </div>
    </div>
  );
};

export default SearchForm;
