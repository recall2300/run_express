import asyncio
import datetime
import re
from SRT import SRT, SRTError, SeatType
from .base_manager import BaseTrainManager

class SrtManager(BaseTrainManager):
    def __init__(self):
        super().__init__()

    def _fetch_all_trains(self, srt: SRT, dep: str, arr: str, date: str, start_time: str):
        all_trains = []
        current_time = start_time
        seen_train_nos = set()
        
        while True:
            try:
                # available_only=False 로 설정하여 예매 불가능한 기차도 조회
                trains = srt.search_train(dep, arr, date, current_time, available_only=False)
                if not trains:
                    break
                
                new_trains_added = False
                for t in trains:
                    if t.train_number not in seen_train_nos:
                        all_trains.append(t)
                        seen_train_nos.add(t.train_number)
                        new_trains_added = True
                
                if not new_trains_added:
                    break
                
                last_train_time = trains[-1].dep_time
                last_dt = datetime.datetime.strptime(last_train_time, "%H%M%S")
                next_dt = last_dt + datetime.timedelta(minutes=1)
                
                if next_dt.day != last_dt.day:
                    break
                
                current_time = next_dt.strftime("%H%M%S")
            except SRTError:
                break
            except Exception as e:
                self.add_log(f"Error in _fetch_all_trains: {e}")
                break
                
        return all_trains

    def get_train_list(self, config):
        try:
            srt = SRT(config.srt_id, config.srt_pw)
            
            search_time = self._get_search_time(config, is_macro=False)

            trains = self._fetch_all_trains(srt, config.dep, config.arr, config.date, search_time)
            result = []
            for t in trains:
                str_t = str(t)
                print(f"[DEBUG RAW DATA SRT] {str_t}")
                
                # SRT 가격 정보 추출 보완 (속성값 우선 확인)
                general_price = getattr(t, 'general_seat_price', getattr(t, 'price', ""))
                special_price = getattr(t, 'special_seat_price', "")
                
                if isinstance(general_price, (int, float)) and general_price > 0: general_price = f"{int(general_price):,}원"
                if isinstance(special_price, (int, float)) and special_price > 0: special_price = f"{int(special_price):,}원"

                if not general_price or not special_price:
                    str_t = str(t)
                    # SRT 객체 문자열에서 가격 패턴 찾기 (예: "59,800원")
                    # 숫자로 시작하고 '원'으로 끝나는 패턴만 추출
                    prices = [p for p in re.findall(r'([\d,]+원)', str_t) if any(c.isdigit() for c in p)]
                    if len(prices) >= 2:
                        if not general_price: general_price = prices[0]
                        if not special_price: special_price = prices[1]
                    elif len(prices) == 1 and not general_price:
                        general_price = prices[0]
                
                result.append({
                    "train_no": t.train_number,
                    "train_name": t.train_name,
                    "dep_time": t.dep_time,
                    "arr_time": t.arr_time,
                    "has_general": t.general_seat_available(),
                    "has_special": t.special_seat_available(),
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

        if not self.check_notification_ready():
            self.is_running = False
            self.target_train_no = None
            self.target_train_name = None
            self.current_config = None
            return

        dep_time_formatted = f"{config.time[:2]}:{config.time[2:4]}" if len(config.time) >= 4 else config.time

        # 좌석 및 가격 정보 포함
        seat_name = "특실" if config.seat_type == 'special' else "일반실"
        price_info = ""
        if hasattr(config, 'price') and config.price:
            price_info = f", {config.price}"

        self.target_train_name = getattr(config, 'train_name', '')
        self.add_log(f"매크로 시작: {config.dep} -> {config.arr} ({config.date}) [열차번호: {config.train_no}호, {dep_time_formatted} 출발, {seat_name}{price_info}]")

        # 구동 시작 알림 전송
        start_msg = self.format_notification(config, "🚀 구동 시작")
        self.send_notification(config, start_msg)

        try:
            srt = SRT(config.srt_id, config.srt_pw)
            self.add_log("로그인 성공!")
        except Exception as e:
            self.add_log(f"Login failed: {e}")
            self.is_running = False
            self.send_notification(config, f"❌ SRT 로그인 실패: {e}")
            return

        search_time = self._get_search_time(config, is_macro=True)

        attempt = 1
        while self.is_running:
            try:
                self.add_log(f"{attempt}회차: 기차표 조회 중...")
                trains = srt.search_train(config.dep, config.arr, config.date, search_time, available_only=False)
                
                reserved = False
                
                for train in trains:
                    if train.train_number != config.train_no:
                        continue

                    has_general = train.general_seat_available()
                    has_special = train.special_seat_available()
                    
                    if has_general or has_special:
                        try:
                            # 가격 정보 추출 (SRT 객체 문자열에서 추출 시도)
                            price = ""
                            price_match = re.search(r'(\d{1,3}(,\d{3})*원)', str(train))
                            if price_match:
                                price = price_match.group(1)

                            # 빈자리 발견 로그 개선
                            seat_desc = "특실" if config.seat_type == 'special' else "일반실"
                            def format_time(t): return f"{t[:2]}:{t[2:4]}" if len(t) >= 4 else t
                            train_name = getattr(train, 'train_name', '[SRT]')
                            def format_time(t): return f"{t[:2]}:{t[2:4]}" if len(t) >= 4 else t
                            self.add_log(f"빈자리 발견! 예매 시도 중: [{train_name}] {config.date[4:6]}월 {config.date[6:8]}일, {config.dep}~{config.arr}({format_time(train.dep_time)}~{format_time(train.arr_time)}) {seat_desc}")
                            
                            # SRT reserve 인자 수정 (SeatType 상수 사용)
                            if config.seat_type == 'special':
                                reservation = srt.reserve(train, special_seat=SeatType.SPECIAL_ONLY)
                            else:
                                reservation = srt.reserve(train, special_seat=SeatType.GENERAL_ONLY)
                            
                            self.add_log(f"예매가 성공적으로 완료되었습니다: {reservation}")
                            
                            # 예매 성공 문자열(str)에서 직접 금액 파싱 (가장 정확함)
                            str_res = str(reservation)
                            p_match = re.search(r'([\d,]+원)', str_res)
                            if p_match:
                                actual_price = p_match.group(1)
                            else:
                                # 실패 시 속성값 확인
                                actual_price = getattr(reservation, 'total_fee', getattr(reservation, 'price', config.price))
                                if isinstance(actual_price, (int, float)):
                                    actual_price = f"{int(actual_price):,}원"
                                elif isinstance(actual_price, str) and actual_price.isdigit():
                                    actual_price = f"{int(actual_price):,}원"
                            
                            msg = self.format_notification(config, "🎉 예매 성공!", seat_type=config.seat_type, price=actual_price)
                            self.send_notification(config, msg)
                            reserved = True
                            break
                        except SRTError as e:
                            self.add_log(f"예매 중 오류 발생: {e}")
                            # 동일한 예약 내역 오류 발생 시 매크로 중단
                            if "동일한 예약 내역" in str(e) or "already reserved" in str(e).lower():
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
            await asyncio.sleep(3) 

        self.add_log("매크로가 종료되었습니다.")
        self.is_running = False
        self.target_train_no = None
        self.target_train_name = None
        self.current_config = None
