import asyncio
import datetime
import os
from typing import List, Optional
from solapi import SolapiMessageService
from solapi.model import RequestMessage

class BaseTrainManager:
    def __init__(self):
        self.is_running = False
        self.logs: List[str] = []
        self.MAX_LOGS = 50
        self.target_train_no = None
        self.target_train_name = None
        self.current_config = None
        
        # Solapi settings
        self.api_key = os.getenv("SOLAPI_API_KEY", "")
        self.api_secret = os.getenv("SOLAPI_API_SECRET", "")
        self.from_number = os.getenv("SOLAPI_SENDER_NUMBER", "")
        self.message_service = None
        if self.api_key and self.api_secret:
            try:
                self.message_service = SolapiMessageService(self.api_key, self.api_secret)
            except Exception as e:
                print(f"Solapi initialization failed: {e}")

        # Telegram settings
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.tg_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.notification_mode = os.getenv("NOTIFICATION_MODE", "telegram").lower() # 'sms' or 'telegram'

    def check_notification_ready(self, config=None) -> bool:
        """알림 설정이 완료되어 있는지 확인. 미설정 시 로그 후 False 반환."""
        if self.notification_mode == 'telegram':
            if not self.tg_token or not self.tg_chat_id:
                self.add_log("알림 설정 오류: TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다. 매크로를 시작할 수 없습니다.")
                return False
        elif self.notification_mode == 'sms':
            if not self.message_service or not self.from_number:
                self.add_log("알림 설정 오류: Solapi API 설정이 완료되지 않았습니다. (SOLAPI_API_KEY, SOLAPI_API_SECRET, SOLAPI_SENDER_NUMBER 확인)")
                return False
            if config is not None and not getattr(config, 'phone_number', ''):
                self.add_log("알림 설정 오류: 수신 전화번호가 비어 있습니다. 설정에서 전화번호를 입력해주세요.")
                return False
        return True

    def add_log(self, msg: str):
        print(msg)
        kst = datetime.timezone(datetime.timedelta(hours=9))
        now = datetime.datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
        self.logs.insert(0, f"[{now}] {msg}")
        if len(self.logs) > self.MAX_LOGS:
            self.logs = self.logs[:self.MAX_LOGS]

    def stop_macro(self):
        if not self.is_running:
            return
            
        self.is_running = False
        self.add_log("매크로 중지 신호를 받았습니다.")
        if self.current_config:
            msg = self.format_notification(self.current_config, "🛑 구동 중지")
            self.send_notification(self.current_config, msg)
        self.current_config = None
        self.target_train_no = None
        self.target_train_name = None

    def format_notification(self, config, event_type, seat_type=None, price=None):
        dep_time = ""
        if hasattr(config, 'time'):
            t = config.time
            dep_time = f"{t[:2]}:{t[2:4]}" if len(t) >= 4 else t
            
        train_type = getattr(config, 'train_type', '기차')
        train_no = getattr(config, 'train_no', '-')
        dep = getattr(config, 'dep', '-')
        arr = getattr(config, 'arr', '-')
        duration = getattr(config, 'duration', '-')
        date = getattr(config, 'date', '')
        date_fmt = f"{date[:4]}-{date[4:6]}-{date[6:8]}" if len(date) >= 8 else date
        profile_name = getattr(config, 'profile_name', '사용자')
        
        s_type = seat_type if seat_type else getattr(config, 'seat_type', '')
        seat_desc = " (특실)" if s_type == 'special' else " (일반실)" if s_type == 'general' else ""
        price_desc = f"\n금액: {price}" if price else ""

        return (
            f"[런특급 알림] {event_type}\n"
            f"열차: {train_type} {train_no}호 ({dep_time} 출발){seat_desc}\n"
            f"구간: {dep} -> {arr} (소요시간: {duration}){price_desc}\n"
            f"날짜: {date_fmt}\n"
            f"사용자: {profile_name}님"
        )

    def send_notification(self, config, message_text: str):
        """환경 변수에 따라 SMS 또는 텔레그램으로 알림 전송"""
        if self.notification_mode == 'sms':
            phone = getattr(config, 'phone_number', '')
            self.send_sms_msg(phone, message_text)
        else:
            self.send_telegram_msg(message_text)

    def send_sms_msg(self, to_number: str, message_text: str):
        if not self.message_service:
            self.add_log("Solapi API 설정이 없습니다. SMS를 전송할 수 없습니다.")
            return
        if not to_number:
            self.add_log("SMS 전송 실패: 수신 전화번호가 설정되지 않았습니다. 설정에서 전화번호를 입력해주세요.")
            return
            
        try:
            to_number = ''.join(filter(str.isdigit, to_number))
            from_number = ''.join(filter(str.isdigit, self.from_number))
            
            message = RequestMessage(
                from_=from_number,
                to=to_number,
                text=message_text
            )
            response = self.message_service.send(message)
            self.add_log(f"SMS 발송 성공: {to_number}")
        except Exception as e:
            self.add_log(f"SMS 전송 실패: {e}")

    def send_telegram_msg(self, message_text: str):
        if not self.tg_token or not self.tg_chat_id:
            self.add_log("텔레그램 설정이 없습니다. (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)")
            return

        try:
            import requests
            url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
            payload = {
                "chat_id": self.tg_chat_id,
                "text": message_text,
                "parse_mode": "HTML"
            }
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                self.add_log("텔레그램 메시지 발송 성공")
            else:
                self.add_log(f"텔레그램 발송 실패: {res.text}")
        except Exception as e:
            self.add_log(f"텔레그램 전송 중 오류: {e}")

    def _format_time(self, t):
        return f"{t[:2]}:{t[2:4]}" if len(t) >= 4 else t

    def _get_search_time(self, config, is_macro=False):
        search_time = getattr(config, 'time', "")
        if not search_time:
            search_time = "000000"
            
        kst = datetime.timezone(datetime.timedelta(hours=9))
        now_kst = datetime.datetime.now(kst)
        now_str = now_kst.strftime("%H%M%S")
        
        # 매크로 구동 시에만 현재 시간보다 이전인 경우 현재 시간으로 조정
        if is_macro and config.date == now_kst.strftime("%Y%m%d") and search_time < now_str:
            search_time = now_str
            
        return search_time
