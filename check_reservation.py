import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 환경 변수에서 텔레그램 정보 가져오기
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    """텔레그램으로 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")
        return None

def check_reservation():
    """예약 페이지 확인"""
    url = "https://www.museum.go.kr/MUSEUM/contents/M0104010000.do?schM=child&act=form"
    
    try:
        # 페이지 요청
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 현재 시간
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 페이지 내용에서 "2월 14일", "14일", "10:00", "10시" 등의 키워드 확인
        page_text = soup.get_text()
        
        # 예약 가능 여부 확인을 위한 키워드들
        keywords_to_check = [
            "2월 14일",
            "02월 14일",
            "2.14",
            "02.14",
            "10:00",
            "10시"
        ]
        
        # 예약 관련 버튼이나 링크 확인
        buttons = soup.find_all(['button', 'a'], text=lambda text: text and '예약' in text)
        links = soup.find_all('a', href=True)
        
        # 상태 메시지
        status_message = f"🔍 <b>박물관 예약 체크</b>\n"
        status_message += f"⏰ 시간: {current_time}\n\n"
        
        # 키워드 발견 여부 확인
        found_keywords = [kw for kw in keywords_to_check if kw in page_text]
        
        if found_keywords:
            status_message += f"✅ <b>발견된 키워드:</b> {', '.join(found_keywords)}\n\n"
            
            # 예약 버튼이 있는지 확인
            if buttons:
                status_message += f"🎯 <b>예약 버튼 발견!</b>\n"
                status_message += f"버튼 개수: {len(buttons)}\n\n"
                status_message += f"🔗 <a href='{url}'>지금 바로 예약하러 가기</a>\n\n"
                status_message += "⚠️ <b>서둘러 확인하세요!</b>"
                
                # 알림 전송
                send_telegram_message(status_message)
                return True
            else:
                status_message += "ℹ️ 키워드는 있지만 아직 예약 버튼은 없습니다."
                print(status_message)
        else:
            status_message += "❌ 아직 2월 14일 10시 예약이 오픈되지 않았습니다."
            print(status_message)
        
        return False
        
    except Exception as e:
        error_message = f"⚠️ <b>오류 발생</b>\n"
        error_message += f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        error_message += f"내용: {str(e)}"
        send_telegram_message(error_message)
        print(f"오류: {e}")
        return False

if __name__ == "__main__":
    print("박물관 예약 모니터링 시작...")
    
    # 텔레그램 설정 확인
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ 텔레그램 설정이 없습니다!")
        print("TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID를 설정해주세요.")
    else:
        # 시작 메시지
        start_msg = f"🚀 <b>박물관 예약 모니터링 시작</b>\n"
        start_msg += f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        start_msg += f"🎯 대상: 2월 14일 10시 타임\n"
        start_msg += f"🔄 체크 주기: 10분마다"
        send_telegram_message(start_msg)
        
        # 예약 확인 실행
        check_reservation()
