import React, { useState } from 'react';

const ProfileSelector = ({ 
  profiles, 
  activeTab, 
  onSelect, 
  onCreate, 
  onDelete 
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [newName, setNewName] = useState('');
  const [newPhone, setNewPhone] = useState('');

  const handleCreate = () => {
    if (!newName) return;
    onCreate(newName, newPhone);
    setNewName('');
    setNewPhone('');
    setIsAdding(false);
  };

  return (
    <div className="profile-selector card">
      <h2 className="card-title">{activeTab} 프로필 선택</h2>
      <div className="profile-grid">
        {Object.keys(profiles).map(name => (
          <div key={name} className="profile-item" onClick={() => onSelect(name)}>
            <div className="avatar">👤</div>
            <div className="name">{name}</div>
            <button 
              className="delete-btn" 
              onClick={(e) => { e.stopPropagation(); onDelete(name); }}
            >
              ✕
            </button>
          </div>
        ))}
        
        {isAdding ? (
          <div className="profile-item adding">
            <input 
              type="text" 
              placeholder="이름" 
              value={newName} 
              onChange={e => setNewName(e.target.value)} 
              autoFocus
            />
            <input 
              type="text" 
              placeholder="전화번호" 
              value={newPhone} 
              onChange={e => setNewPhone(e.target.value)}
            />
            <button className="btn-save" onClick={handleCreate}>생성</button>
            <button className="btn-cancel" onClick={() => setIsAdding(false)}>취소</button>
          </div>
        ) : (
          <div className="profile-item add-new" onClick={() => setIsAdding(true)}>
            <div className="avatar">+</div>
            <div className="name">추가하기</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfileSelector;
