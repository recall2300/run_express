import React from 'react';

const SettingsModal = ({ 
  show, 
  config, 
  activeTab, 
  activeProfile, 
  onChange, 
  onSave, 
  onClose 
}) => {
  if (!show) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{activeProfile || '전체'} 설정</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="settings-section">
          <h3>{activeTab} 계정 정보</h3>
          <div className="input-group">
            <label>회원번호 / ID</label>
            <input 
              type="text" 
              name={activeTab === 'KTX' ? 'korail_id' : 'srt_id'} 
              value={activeTab === 'KTX' ? config.korail_id : config.srt_id} 
              onChange={onChange}
              placeholder="멤버십 번호 등"
            />
          </div>
          <div className="input-group">
            <label>비밀번호</label>
            <input 
              type="password" 
              name={activeTab === 'KTX' ? 'korail_pw' : 'srt_pw'} 
              value={activeTab === 'KTX' ? config.korail_pw : config.srt_pw} 
              onChange={onChange}
              placeholder="****"
            />
          </div>
        </div>

        <div className="modal-actions">
          <button className="btn-primary" onClick={onSave}>설정 저장</button>
          <button className="btn-secondary" onClick={onClose}>닫기</button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
