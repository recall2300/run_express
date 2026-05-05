import asyncio
import datetime
import re
import requests
from korail2 import Korail, KorailError, ReserveOption
from .base_manager import BaseTrainManager

class KorailManager(BaseTrainManager):
    def __init__(self):
        super().__init__()

    def _format_time(self, t):
        return f"{t[:2]}:{t[2:4]}" if len(t) >= 4 else t

    def _fetch_all_trains(self, korail: Korail, dep: str, arr: str, date: str, start_time: str):
        all_trains = []
        current_time = start_time
        seen_train_nos = set()
        
        while True:
            try:
                # include_no_seats=True 로 설정하여 예매 불가능한 기차도 조회
                trains = korail.search_train(dep, arr, date, current_time, include_no_seats=True)
                if not trains:
                    break
                
                new_trains_added = False
                for t in trains:
                    if t.train_no not in seen_train_nos:
                        all_trains.append(t)
                        seen_train_nos.add(t.train_no)
                        new_trains_added = True
                
                if not new_trains_added:
                    break
                
                # 다음 페이지 조회를 위해 가져온 마지막 기차의 출발 시간에 1분 추가
                last_train_time = trains[-1].dep_time
                last_dt = datetime.datetime.strptime(last_train_time, "%H%M%S")
                next_dt = last_dt + datetime.timedelta(minutes=1)
                
                # 하루가 넘어가면 중단
                if next_dt.day != last_dt.day:
                    break
                
                current_time = next_dt.strftime("%H%M%S")
            except KorailError:
                break
            except Exception as e:
                self.add_log(f"Error in _fetch_all_trains: {e}")
                break
                
        return all_trains

    def get_train_list(self, config):
        try:
            # 세션 누수 방지를 위한 세션 초기화
            Korail._session = requests.Session()
            korail = Korail(config.korail_id, config.korail_pw)
            
            search_time = self._get_search_time(config, is_macro=False)

            # pagination 을 우회하여 조건 내의 모든 기차 조회
            trains = self._fetch_all_trains(korail, config.dep, config.arr, config.date, search_time)
            result = []
            for t in trains:
                str_t = str(t)
                # 디버그용 로그: 실제 데이터가 어떻게 들어오는지 콘솔에 출력
                print(f"[DEBUG RAW DATA] {str_t}")

                # 가격 정보 추출 시도 (다양한 속성명 확인)
                general_price = getattr(t, 'general_seat_price', getattr(t, 'general_price', ''))
                special_price = getattr(t, 'special_seat_price', getattr(t, 'special_price', ''))
                
                # 만약 속성이 숫자로 되어있다면 쉼표 포맷팅
                if isinstance(general_price, (int, float)) and general_price > 0: general_price = f"{int(general_price):,}원"
                if isinstance(special_price, (int, float)) and special_price > 0: special_price = f"{int(special_price):,}원"

                # 문자열 파싱 보완
                if not general_price or not special_price:
                    str_t = str(t)
                    # 가격 패턴 정교화: 반드시 '원'으로 끝나는 패턴만 허용 (좌석 수와 혼동 방지)
                    g_match = re.search(r'일반실[:\s]*[^()]*?([\d,]+원)', str_t)
                    s_match = re.search(r'특실[:\s]*[^()]*?([\d,]+원)', str_t)
                    
                    if g_match and not general_price:
                        general_price = g_match.group(1)
                    if s_match and not special_price:
                        special_price = s_match.group(1)
                    
                    # 만약 여전히 특실 가격이 없다면, 문자열 내에서 '원'이 붙은 두 번째 금액을 탐색
                    if not special_price:
                        prices = re.findall(r'([\d,]+원)', str_t)
                        if len(prices) >= 2:
                            special_price = prices[1]

                result.append({
                    "train_no": t.train_no,
                    "train_name": getattr(t, 'train_type_name', str(t).split(']')[0][1:]), 
                    "dep_time": t.dep_time,
                    "arr_time": t.arr_time,
                    "has_general": t.has_general_seat() if hasattr(t, 'has_general_seat') else ('11' in getattr(t, 'general_seat', '')),
                    "has_special": t.has_special_seat() if hasattr(t, 'has_special_seat') else ('11' in getattr(t, 'special_seat', '')),
                    "general_price": general_price,
                    "special_price": special_price
                })
            return result
        except Exception as e:
            self.add_log(f"Error fetching train list: {e}")
            return []

    async def run_macro(self, config):
        self.is_running = True
        self.target_train_no = config.train_no
        self.current_config = config
        self.logs = []
        dep_time_formatted = f"{config.time[:2]}:{config.time[2:4]}" if len(config.time) >= 4 else config.time
        
        # 좌석 및 가격 정보 포함
        seat_name = "특실" if config.seat_type == 'special' else "일반실"
        price_info = ""
        if hasattr(config, 'price') and config.price:
            price_info = f", {config.price}"
        
        self.add_log(f"매크로 시작: {config.dep} -> {config.arr} ({config.date}) [열차번호: {config.train_no}호, {dep_time_formatted} 출발, {seat_name}{price_info}]")
        
        # 구동 시작 알림 전송
        start_msg = self.format_notification(config, "🚀 구동 시작")
        self.send_notification(config, start_msg)
        
        try:
            # 세션 누수 방지를 위한 클래스 세션 리셋
            Korail._session = requests.Session()
            korail = Korail(config.korail_id, config.korail_pw)
            
            # 로그인 성공 여부를 토큰 발급 및 쿠키 생성 유무로 판단
            if not getattr(korail, 'krX_token', None) and not korail._session.cookies:
                self.add_log("Login failed: 아이디/비밀번호 오류이거나 코레일 서버 응답 지연입니다.")
                self.is_running = False
                return
            
            self.add_log("로그인 성공!")
        except Exception as e:
            self.add_log(f"Login failed: {e}")
            self.is_running = False
            self.send_notification(config, f"❌ 코레일 로그인 실패: {e}")
            return

        search_time = self._get_search_time(config, is_macro=True)

        attempt = 1
        while self.is_running:
            try:
                self.add_log(f"{attempt}회차: 기차표 조회 중...")
                # 지정된 조건으로 기차표 단일 페이지 조회 (기차 시간에 가까운 시점 기준)
                trains = korail.search_train(config.dep, config.arr, config.date, search_time, include_no_seats=True)
                
                reserved = False
                
                # 안전한 예매 시도를 위해 korail2 라이브러리 내장 메서드 사용:
                for train in trains:
                    # 지정한 기차 번호와 정확히 일치하는 열차만 예매 (100% 매칭)
                    if train.train_no != config.train_no:
                        continue

                    has_general = train.has_general_seat() if hasattr(train, 'has_general_seat') else ('11' in getattr(train, 'general_seat', ''))
                    has_special = train.has_special_seat() if hasattr(train, 'has_special_seat') else ('11' in getattr(train, 'special_seat', ''))
                    
                    if has_general or has_special:
                        try:
                            # 가격 정보 추출 (예: 44,500원)
                            price = ""
                            price_match = re.search(r'(\d{1,3}(,\d{3})*원)', str(train))
                            if price_match:
                                price = price_match.group(1)

                            # 빈자리 발견 로그 개선
                            seat_desc = "특실" if config.seat_type == 'special' else "일반실"
                            train_name = getattr(train, 'train_type_name', str(train).split(']')[0][1:])
                            self.add_log(f"빈자리 발견! 예매 시도 중: [{train_name}] {config.date[4:6]}월 {config.date[6:8]}일, {config.dep}~{config.arr}({self._format_time(train.dep_time)}~{self._format_time(train.arr_time)}) {seat_desc}")
                            
                            # 좌석 등급 지정
                            option = ReserveOption.SPECIAL_ONLY if config.seat_type == 'special' else ReserveOption.GENERAL_ONLY
                            
                            reservation = korail.reserve(train, option=option)
                            self.add_log(f"예매가 성공적으로 완료되었습니다: {reservation}")
                            
                            # 예매 성공 문자열(str)에서 직접 금액 파싱 (가장 정확함)
                            str_res = str(reservation)
                            p_match = re.search(r'([\d,]+원)', str_res)
                            if p_match:
                                actual_price = p_match.group(1)
                            else:
                                # 실패 시 속성값 확인
                                actual_price = getattr(reservation, 'total_price', getattr(reservation, 'amount', config.price))
                                if isinstance(actual_price, (int, float)):
                                    actual_price = f"{int(actual_price):,}원"
                            
                            msg = self.format_notification(config, "🎉 예매 성공!", seat_type=config.seat_type, price=actual_price)
                            self.send_notification(config, msg)
                            reserved = True
                            break
                        except KorailError as e:
                            self.add_log(f"예매 중 오류 발생: {e}")
                            # 동일한 예약 내역 오류 발생 시 매크로 중단
                            if "동일한 예약 내역" in str(e) or "WRR800029" in str(e):
                                self.add_log(f"중단 사유: {e}")
                                self.is_running = False
                                break
                
                if reserved:
                    self.is_running = False
                    break
                else:
                    msg = "조회된 기차가 없습니다." if not trains else "잔여 좌석 없음."
                    self.add_log(msg)
                    
            except Exception as e:
                self.add_log(f"조회 실패: {e}")

            attempt += 1
            await asyncio.sleep(3) # 3초 주기로 조회 대기

        self.add_log("매크로가 종료되었습니다.")
        self.is_running = False
        self.target_train_no = None
        self.current_config = None
