import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re
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

def check_reservation():
    """예약 페이지 확인 및 상세 정보 수집"""
    url = "https://www.museum.go.kr/MUSEUM/contents/M0104010000.do?schM=child&act=form"
    
    try:
        # 페이지 요청
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        }
        
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 현재 시간
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 상태 메시지 초기화
        status_message = f"🔍 <b>박물관 예약 체크</b>\n"
        status_message += f"⏰ 체크 시간: {current_time}\n"
        status_message += f"━━━━━━━━━━━━━━━━━\n\n"
        
        # 예약 가능 여부 체크를 위한 키워드
        page_text = soup.get_text()
        
        # 2월 14일 키워드 확인
        feb_14_keywords = ["2월 14일", "02월 14일", "2.14", "02.14", "14일"]
        found_feb_14 = any(keyword in page_text for keyword in feb_14_keywords)
        
        # 10시 타임 키워드 확인
        time_10_keywords = ["10:00", "10시", "10 : 00"]
        found_time_10 = any(keyword in page_text for keyword in time_10_keywords)
        
        # 예약 관련 정보 추출 시도
        reservation_info = extract_reservation_info(soup, page_text)
        
        # 예약 정보가 있으면 상세 정보 표시
        if reservation_info:
            status_message += "📊 <b>예약 현황</b>\n\n"
            
            for date_info in reservation_info:
                status_message += f"📅 날짜: {date_info['date']}\n"
                status_message += f"🕐 시간: {date_info['time']}\n"
                status_message += f"👥 총 인원: {date_info['total']}\n"
                status_message += f"✅ 예약 가능: {date_info['available']}\n"
                
                # 예약 가능 인원 계산
                try:
                    total = int(date_info['total'])
                    available = int(date_info['available'])
                    booked = total - available
                    percentage = (booked / total * 100) if total > 0 else 0
                    
                    status_message += f"📈 예약률: {percentage:.1f}%\n"
                except:
                    pass
                
                status_message += f"\n"
            
            # 2월 14일 10시가 발견되면 특별 알림
            if found_feb_14 and found_time_10:
                status_message += "🎯 <b>2월 14일 10시 타임 발견!</b>\n\n"
                status_message += f"🔗 <a href='{url}'>지금 바로 예약하러 가기</a>\n"
                status_message += "⚠️ <b>서둘러 확인하세요!</b>"
        else:
            # 예약 정보를 찾을 수 없는 경우
            status_message += "ℹ️ <b>현재 상태</b>\n\n"
            
            if found_feb_14:
                status_message += "✅ 2월 14일 정보 발견\n"
            else:
                status_message += "❌ 2월 14일 정보 없음\n"
            
            if found_time_10:
                status_message += "✅ 10시 타임 정보 발견\n"
            else:
                status_message += "❌ 10시 타임 정보 없음\n"
            
            status_message += "\n"
            
            # 페이지에서 숫자 패턴 찾기 (예약 가능 인원 추정)
            numbers = re.findall(r'\d+', page_text)
            if numbers:
                status_message += f"📝 페이지에서 발견된 숫자들: {', '.join(numbers[:10])}\n\n"
            
            status_message += "💡 예약 상세 정보는 아직 로드되지 않았거나\n"
            status_message += "   페이지 구조가 변경되었을 수 있습니다.\n\n"
            status_message += f"🔗 <a href='{url}'>페이지 직접 확인하기</a>"
        
        # 메시지 전송
        print(status_message)
        send_telegram_message(status_message)
        
        return True
        
    except Exception as e:
        error_message = f"⚠️ <b>오류 발생</b>\n"
        error_message += f"⏰ 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        error_message += f"❌ 내용: {str(e)}"
        
        send_telegram_message(error_message)
        print(f"오류: {e}")
        return False

def extract_reservation_info(soup, page_text):
    """페이지에서 예약 정보 추출"""
    reservation_data = []
    
    try:
        # 방법 1: 테이블이나 리스트에서 추출
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    # 날짜, 시간, 인원 정보가 있는지 확인
                    text_content = [cell.get_text(strip=True) for cell in cells]
                    
                    # 패턴 매칭으로 예약 정보 추출
                    for i, text in enumerate(text_content):
                        if '월' in text and '일' in text:
                            # 예약 정보로 보이는 행 발견
                            date_info = {
                                'date': text,
                                'time': text_content[i+1] if i+1 < len(text_content) else 'N/A',
                                'total': extract_number(text_content, i+2),
                                'available': extract_number(text_content, i+3)
                            }
                            reservation_data.append(date_info)
        
        # 방법 2: div나 span에서 추출
        if not reservation_data:
            # 예약 관련 클래스나 ID를 가진 요소 찾기
            reservation_sections = soup.find_all(['div', 'section'], class_=re.compile(r'reserv|book|schedule', re.I))
            for section in reservation_sections:
                # 날짜 패턴 찾기
                dates = re.findall(r'(\d{1,2}월\s*\d{1,2}일)', section.get_text())
                times = re.findall(r'(\d{1,2}:\d{2})', section.get_text())
                
                if dates and times:
                    for date, time in zip(dates, times):
                        date_info = {
                            'date': date,
                            'time': time,
                            'total': 'N/A',
                            'available': 'N/A'
                        }
                        reservation_data.append(date_info)
        
    except Exception as e:
        print(f"예약 정보 추출 중 오류: {e}")
    
    return reservation_data

def extract_number(text_list, index):
    """텍스트 리스트에서 숫자 추출"""
    try:
        if index < len(text_list):
            numbers = re.findall(r'\d+', text_list[index])
            return numbers[0] if numbers else 'N/A'
    except:
        pass
    return 'N/A'

if __name__ == "__main__":
    print("박물관 예약 모니터링 시작...")
    
    # 텔레그램 설정 확인
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ 텔레그램 설정이 없습니다!")
        print("TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID를 설정해주세요.")
    else:
        # 예약 확인 실행
        check_reservation()
