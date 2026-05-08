import React from 'react';

const TrainList = ({ trains, onStart, isRunning }) => {
  if (trains.length === 0) return null;

  const formatTime = (t) => t ? `${t.slice(0,2)}:${t.slice(2,4)}` : '';
  
  const calculateDuration = (dep, arr) => {
    if (!dep || !arr) return "";
    const dH = parseInt(dep.slice(0,2));
    const dM = parseInt(dep.slice(2,4));
    let aH = parseInt(arr.slice(0,2));
    const aM = parseInt(arr.slice(2,4));
    if (aH < dH) aH += 24; 
    let diff = (aH * 60 + aM) - (dH * 60 + dM);
    return `${Math.floor(diff / 60)}시간 ${diff % 60}분`;
  };

  return (
    <div className="train-list card">
      <h2 className="card-title">조회 결과</h2>
      <div className="train-items">
        {trains.map((t, i) => (
          <div key={i} className="train-item">
            <div className="train-row">
              <div className="time-box">
                <span className="time dep">{formatTime(t.dep_time)}</span>
                <span className="arrow">→</span>
                <span className="time arr">{formatTime(t.arr_time)}</span>
              </div>

              <div className="detail-box">
                <div className="train-meta">
                  <span className="train-tag">{t.train_name} {t.train_no}호</span>
                  <span className="duration-tag">{calculateDuration(t.dep_time, t.arr_time)}</span>
                </div>
              </div>

              <div className="action-row">
                <button 
                  className={`btn-action ${t.has_special ? 'available' : 'soldout'}`} 
                  onClick={() => onStart(t.train_no, t.dep_time, calculateDuration(t.dep_time, t.arr_time), 'special', t.special_price, t.train_name)}
                  disabled={isRunning}
                >
                  <span className="seat-type">특실</span>
                  <span className="status-text">{t.has_special ? '예매하기' : '매진'}</span>
                </button>
                <button
                  className={`btn-action ${t.has_general ? 'available' : 'soldout'}`}
                  onClick={() => onStart(t.train_no, t.dep_time, calculateDuration(t.dep_time, t.arr_time), 'general', t.general_price, t.train_name)}
                  disabled={isRunning}
                >
                  <span className="seat-type">일반실</span>
                  <span className="status-text">{t.has_general ? '예매하기' : '매진'}</span>
                </button>
              </div>
            </div>
            
          </div>
        ))}
      </div>
    </div>
  );
};

export default TrainList;
