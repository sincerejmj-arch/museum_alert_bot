import requests
import os
from datetime import datetime
import json

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

def get_reservation_data(target_date="20260214"):
    """
    특정 날짜의 예약 정보를 API로 가져오기
    target_date: YYYYMMDD 형식 (예: 20260214)
    """
    api_url = "https://www.museum.go.kr/ticket_reservation/Web/Book/GetBookPlaySequence.json"
    
    params = {
        "shop_code": "102830101202",
        "play_date": target_date,
        "product_group_code": "0101"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Referer': 'https://www.museum.go.kr/MUSEUM/contents/M0104010000.do?schM=child&act=intro',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API 요청 실패: {e}")
        return None

def check_reservation():
    """2월 14일 예약 정보 확인"""
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 2월 14일 예약 정보 가져오기
    data = get_reservation_data("20260214")
    
    if not data:
        # API 실패 시 메시지
        error_message = f"⚠️ <b>API 호출 실패</b>\n"
        error_message += f"⏰ 시간: {current_time}\n\n"
        error_message += "예약 정보를 가져올 수 없습니다.\n"
        error_message += "페이지가 변경되었거나 네트워크 오류일 수 있습니다."
        
        print(error_message)
        send_telegram_message(error_message)
        return False
    
    # 메시지 생성
    status_message = f"🔍 <b>박물관 예약 체크</b>\n"
    status_message += f"⏰ 체크 시간: {current_time}\n"
    status_message += f"📅 조회 날짜: 2026년 2월 14일\n"
    status_message += f"━━━━━━━━━━━━━━━━━\n\n"
    
    try:
        # API 응답 구조에 따라 데이터 파싱
        # 일반적인 예약 API 응답 구조를 가정
        
        if isinstance(data, dict):
            # 예약 가능한 시간대 정보가 있는지 확인
            if 'list' in data or 'data' in data or 'result' in data:
                time_slots = data.get('list') or data.get('data') or data.get('result') or []
                
                if time_slots:
                    status_message += f"📊 <b>예약 현황</b>\n\n"
                    
                    found_10am = False
                    total_available = 0
                    
                    for slot in time_slots:
                        # 시간대 정보 추출
                        play_time = slot.get('play_time', slot.get('time', 'N/A'))
                        total_cnt = slot.get('seat_cnt', slot.get('total', slot.get('total_cnt', 0)))
                        remain_cnt = slot.get('remain_cnt', slot.get('available', slot.get('remain', 0)))
                        
                        # 예약 가능 여부
                        is_available = slot.get('book_status', slot.get('status', '')) != 'N'
                        
                        # 10시 타임 확인
                        if '10:00' in str(play_time) or '10시' in str(play_time):
                            found_10am = True
                        
                        # 예약 가능한 경우만 카운트
                        if is_available and remain_cnt > 0:
                            total_available += remain_cnt
                        
                        # 시간대별 정보 표시
                        status_icon = "✅" if is_available and remain_cnt > 0 else "❌"
                        status_message += f"{status_icon} <b>{play_time}</b>\n"
                        status_message += f"   👥 총 인원: {total_cnt}명\n"
                        status_message += f"   🎫 예약 가능: {remain_cnt}명\n"
                        
                        # 예약률 계산
                        if total_cnt > 0:
                            booked = total_cnt - remain_cnt
                            percentage = (booked / total_cnt * 100)
                            status_message += f"   📈 예약률: {percentage:.1f}%\n"
                        
                        status_message += "\n"
                    
                    # 10시 타임 발견 시 특별 알림
                    if found_10am and total_available > 0:
                        status_message += "🎯 <b>2월 14일 10시 타임 예약 가능!</b>\n\n"
                        status_message += f"🔗 <a href='https://www.museum.go.kr/MUSEUM/contents/M0104010000.do?schM=child&act=intro'>지금 바로 예약하러 가기</a>\n"
                        status_message += "⚠️ <b>서둘러 확인하세요!</b>"
                    elif found_10am:
                        status_message += "ℹ️ 10시 타임이 있지만 현재 예약 불가 상태입니다."
                    else:
                        status_message += "ℹ️ 아직 10시 타임 정보가 표시되지 않았습니다."
                else:
                    status_message += "ℹ️ 예약 가능한 시간대가 없습니다.\n"
                    status_message += "아직 예약이 오픈되지 않았을 수 있습니다."
            else:
                # API 응답은 있지만 예상과 다른 구조
                status_message += "📋 <b>API 응답 내용:</b>\n"
                status_message += f"<code>{json.dumps(data, ensure_ascii=False, indent=2)[:500]}</code>\n\n"
                status_message += "예약 정보 구조를 확인 중입니다."
        else:
            status_message += "⚠️ 예상치 못한 API 응답 형식입니다."
    
    except Exception as e:
        status_message += f"❌ 데이터 파싱 오류\n"
        status_message += f"상세: {str(e)}\n\n"
        status_message += f"원본 데이터:\n<code>{str(data)[:300]}</code>"
    
    # 메시지 전송
    print(status_message)
    send_telegram_message(status_message)
    
    return True

if __name__ == "__main__":
    print("박물관 예약 모니터링 시작...")
    
    # 텔레그램 설정 확인
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ 텔레그램 설정이 없습니다!")
        print("TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID를 설정해주세요.")
    else:
        # 예약 확인 실행
        check_reservation()
