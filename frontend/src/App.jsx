import { useState, useEffect } from 'react'
import { api } from './services/api'
import Header from './components/Header'
import TabSwitcher from './components/TabSwitcher'
import ProfileSelector from './components/ProfileSelector'
import SearchForm from './components/SearchForm'
import TrainList from './components/TrainList'
import MacroStatus from './components/MacroStatus'
import SettingsModal from './components/SettingsModal'

const KTX_STATIONS = [
  "서울", "용산", "영등포", "광명", "수원", "평택", "천안아산", "오송", "대전", "서대전", 
  "김천구미", "동대구", "경주", "포항", "태화강", "울산(통도사)", "부산", 
  "마산", "창원", "창원중앙", "진주", "익산", "정읍", "광주송정", "나주", "목포", 
  "전주", "남원", "순천", "여천", "여수엑스포", "청량리", "강릉", "동해",
  "행신", "서대구", "밀양", "구포", "진영", "공주", "계룡", "논산", "곡성", "구례구", 
  "상봉", "양평", "서원주", "만종", "횡성", "둔내", "평창", "진부", "제천", "단양", "풍기", "영주", "안동"
].sort((a, b) => a.localeCompare(b, 'ko'));

const KTX_NETWORKS = [
  ["행신", "서울", "용산", "영등포", "광명", "수원", "평택", "천안아산", "오송", "대전", "김천구미", "서대구", "동대구", "경주", "포항", "태화강", "울산(통도사)", "부산", "밀양", "구포", "진영", "창원중앙", "창원", "마산", "진주"],
  ["행신", "서울", "용산", "영등포", "광명", "수원", "평택", "천안아산", "오송", "서대전", "공주", "계룡", "논산", "익산", "정읍", "광주송정", "나주", "목포", "전주", "남원", "곡성", "구례구", "순천", "여천", "여수엑스포"],
  ["행신", "서울", "청량리", "상봉", "양평", "서원주", "만종", "횡성", "둔내", "평창", "진부", "강릉", "동해"],
  ["서울", "청량리", "양평", "서원주", "제천", "단양", "풍기", "영주", "안동"],
  ["부산", "마산", "창원", "창원중앙", "진주", "순천", "광주송정"], 
  ["부산", "태화강", "경주", "포항", "동해", "강릉"]
];

const SRT_STATIONS = [
  "수서", "동탄", "평택지제", "천안아산", "오송", "대전", "김천구미", "동대구", "경주", "포항", "울산(통도사)", "부산",
  "마산", "창원", "창원중앙", "진주", "공주", "익산", "정읍", "광주송정", "나주", "목포", "전주", "남원", "순천", "여천", "여수엑스포"
].sort((a, b) => a.localeCompare(b, 'ko'));

const SRT_NETWORKS = [
  ["수서", "동탄", "평택지제", "천안아산", "오송", "대전", "김천구미", "동대구", "경주", "포항", "울산(통도사)", "부산", "마산", "창원", "창원중앙", "진주"],
  ["수서", "동탄", "평택지제", "천안아산", "오송", "공주", "익산", "정읍", "광주송정", "나주", "목포", "전주", "남원", "순천", "여천", "여수엑스포"]
];

const DEFAULT_CONFIG = {
  korail_id: '', korail_pw: '', srt_id: '', srt_pw: '',
  dep: '', arr: '', date: new Date().toISOString().slice(0, 10).replace(/-/g, ''),
  time: '000000', train_no: '', phone_number: ''
};

function App() {
  const [activeTab, setActiveTab] = useState(localStorage.getItem('runktx_tab') || 'KTX');
  const [activeProfiles, setActiveProfiles] = useState({ KTX: '', SRT: '' });
  const [configs, setConfigs] = useState({
    KTX: { ...DEFAULT_CONFIG, dep: '서울', arr: '부산' },
    SRT: { ...DEFAULT_CONFIG, dep: '수서', arr: '부산' }
  });
  const [trainLists, setTrainLists] = useState({ KTX: [], SRT: [] });
  const [profiles, setProfiles] = useState({ KTX: {}, SRT: {} });
  const [isRunningAll, setIsRunningAll] = useState({ 
    KTX: { is_running: false, target_train_no: null }, 
    SRT: { is_running: false, target_train_no: null } 
  });
  const [logsAll, setLogsAll] = useState({ KTX: [], SRT: [] });
  const [isSearching, setIsSearching] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    ['KTX', 'SRT'].forEach(async (type) => {
      try {
        const data = await api.getProfiles(type);
        if (data.status === 'success') {
          setProfiles(prev => ({ ...prev, [type]: data.profiles }));
        }
      } catch (err) { console.error(`${type} Profiles load failed`, err); }
    });
  }, []);

  const checkStatus = async () => {
    try {
      const data = await api.getStatus();
      setIsRunningAll({ 
        KTX: { is_running: data.KTX.is_running, target_train_no: data.KTX.target_train_no }, 
        SRT: { is_running: data.SRT.is_running, target_train_no: data.SRT.target_train_no } 
      });
      setLogsAll({ KTX: data.KTX.logs, SRT: data.SRT.logs });
    } catch (err) { console.error('Status check failed', err); }
  };

  useEffect(() => {
    const interval = setInterval(checkStatus, 1500);
    return () => clearInterval(interval);
  }, []);

  const config = configs[activeTab];
  const activeProfile = activeProfiles[activeTab];
  const trainList = trainLists[activeTab];
  const currentLogs = logsAll[activeTab];
  const currentRunning = isRunningAll[activeTab];

  const updateConfig = (newConf) => setConfigs(prev => ({ ...prev, [activeTab]: newConf }));

  const handleChange = (e) => {
    let newConf = { ...config, [e.target.name]: e.target.value };
    if (e.target.name === 'dep') {
      const validArr = getValidArrivals(e.target.value, activeTab);
      if (!validArr.includes(newConf.arr)) newConf.arr = validArr[0] || '';
    }
    updateConfig(newConf);
  };

  const getValidArrivals = (dep, type) => {
    const networks = type === 'SRT' ? SRT_NETWORKS : KTX_NETWORKS;
    const stations = type === 'SRT' ? SRT_STATIONS : KTX_STATIONS;
    const valid = new Set();
    networks.forEach(net => { if (net.includes(dep)) net.forEach(st => valid.add(st)); });
    if (valid.size === 0) return stations.filter(st => st !== dep);
    return stations.filter(st => valid.has(st) && st !== dep);
  };

  const handleLogin = (pName) => {
    setActiveProfiles(prev => ({ ...prev, [activeTab]: pName }));
    if (profiles[activeTab][pName]) {
      updateConfig({ 
        ...config, ...profiles[activeTab][pName], 
        date: new Date().toISOString().slice(0, 10).replace(/-/g, '') 
      });
    }
  };

  const handleCreateProfile = async (name, phone) => {
    const initialConf = { ...DEFAULT_CONFIG, dep: activeTab === 'KTX' ? '서울' : '수서', arr: '부산', phone_number: phone };
    try {
      const res = await api.saveProfile(activeTab, name, initialConf);
      if (res.status === 'success') {
        setProfiles(prev => ({ ...prev, [activeTab]: { ...prev[activeTab], [name]: initialConf } }));
        handleLogin(name);
      }
    } catch (err) { alert("프로필 생성 실패"); }
  };

  const handleDeleteProfile = async (pName) => {
    console.log("handleDeleteProfile called for:", pName, "activeTab:", activeTab);
    if (!window.confirm(`'${pName}' 프로필을 삭제하시겠습니까?`)) return;
    try {
      const res = await api.deleteProfile(activeTab, pName);
      console.log("Delete response:", res);
      if (res.status === 'success') {
        setProfiles(prev => {
          const newP = { ...prev[activeTab] };
          delete newP[pName];
          return { ...prev, [activeTab]: newP };
        });
        if (activeProfile === pName) setActiveProfiles(prev => ({ ...prev, [activeTab]: '' }));
      }
    } catch (err) { 
      console.error("Delete failed:", err);
      alert("프로필 삭제 실패"); 
    }
  };

  const handleSearch = async () => {
    const id = activeTab === 'KTX' ? config.korail_id : config.srt_id;
    const pw = activeTab === 'KTX' ? config.korail_pw : config.srt_pw;
    if (!id || !pw) {
      alert(`설정에서 ${activeTab} 계정을 먼저 입력해주세요!`);
      setShowSettings(true);
      return;
    }
    setIsSearching(true);
    setTrainLists(prev => ({ ...prev, [activeTab]: [] }));
    try {
      const data = await api.searchTrains(activeTab, config);
      if (data.status === 'success') {
        setTrainLists(prev => ({ ...prev, [activeTab]: data.trains || [] }));
        if (data.trains?.length === 0) alert("조건에 맞는 열차가 없습니다.");
      } else alert(data.message || "조회 실패");
    } catch (err) { alert("서버 연결 실패"); }
    setIsSearching(false);
  };

  const handleStartMacro = async (trainNo, depTime, duration, seatType = 'general', price = '') => {
    const updated = { 
      ...config, 
      train_no: trainNo, 
      time: depTime, 
      profile_name: activeProfile, 
      train_type: activeTab, 
      duration,
      seat_type: seatType,
      price: price
    };
    updateConfig(updated);
    try {
      const res = await api.startMacro(activeTab, updated);
      if (res.status === 'success') {
        setIsRunningAll(prev => ({ ...prev, [activeTab]: { is_running: true, target_train_no: trainNo } }));
      } else alert(res.message);
    } catch (err) { alert("서버 연결 실패"); }
  };

  const handleStopMacro = async () => {
    try {
      const res = await api.stopMacro(activeTab);
      if (res.status === 'success') {
        setIsRunningAll(prev => ({ ...prev, [activeTab]: { is_running: false, target_train_no: null } }));
      }
    } catch (err) { alert("서버 연결 실패"); }
  };

  const handleSaveSettings = async () => {
    if (!activeProfile) return;
    try {
      const res = await api.saveProfile(activeTab, activeProfile, config);
      if (res.status === 'success') {
        setProfiles(prev => ({ ...prev, [activeTab]: { ...prev[activeTab], [activeProfile]: config } }));
        setShowSettings(false);
      }
    } catch (err) { alert("저장 실패"); }
  };

  return (
    <div className="app-layout">
      <Header 
        isRunning={isRunningAll.KTX.is_running || isRunningAll.SRT.is_running} 
        onOpenSettings={() => setShowSettings(true)} 
      />
      
      <main className="main-content">
        <TabSwitcher 
          activeTab={activeTab} 
          onTabChange={(tab) => { localStorage.setItem('runktx_tab', tab); setActiveTab(tab); }} 
        />

        {!activeProfile ? (
          <ProfileSelector 
            profiles={profiles[activeTab]} 
            activeTab={activeTab}
            onSelect={handleLogin}
            onCreate={handleCreateProfile}
            onDelete={handleDeleteProfile}
          />
        ) : (
          <>
            <SearchForm 
              config={config} 
              activeTab={activeTab}
              stations={activeTab === 'SRT' ? SRT_STATIONS : KTX_STATIONS}
              validArrivals={getValidArrivals(config.dep, activeTab)}
              onChange={handleChange}
              onSearch={handleSearch}
              isSearching={isSearching}
              hasResults={trainList.length > 0}
              activeProfile={activeProfile}
              onResetProfile={() => setActiveProfiles(prev => ({ ...prev, [activeTab]: '' }))}
            />

            <MacroStatus 
              isRunning={currentRunning.is_running}
              logs={currentLogs}
              targetTrain={currentRunning.target_train_no || config.train_no}
              onStop={handleStopMacro}
            />

            <TrainList 
              trains={trainList} 
              onStart={handleStartMacro} 
              isRunning={currentRunning.is_running}
            />
          </>
        )}
      </main>

      <SettingsModal 
        show={showSettings}
        config={config}
        activeTab={activeTab}
        activeProfile={activeProfile}
        onChange={handleChange}
        onSave={handleSaveSettings}
        onClose={() => setShowSettings(false)}
      />
    </div>
  );
}

export default App
