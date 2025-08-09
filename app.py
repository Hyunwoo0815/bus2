import json
import os
import glob
from datetime import datetime
import random

# 📂 폴더 경로 설정 (GitHub Actions 환경에 맞게)
data_folder = "data"
output_folder = "outputs"
route_file_path = "route/total_route.json"
published_dates_file = os.path.join(output_folder, "published_dates.json")

# 📂 출력 폴더 생성
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 🔍 data 폴더의 모든 JSON 파일 찾기
json_files = glob.glob(os.path.join(data_folder, "*_schedules.json"))

if not json_files:
    print(f"🚫 {data_folder} 폴더에 '*_schedules.json' 파일을 찾을 수 없습니다.")
    exit(1)

print(f"✅ 발견된 JSON 파일: {len(json_files)}개")
for file in json_files:
    print(f"  📄 {file}")

# ✅ 오늘 날짜
today_date = datetime.today().strftime("%Y-%m-%d")
update_date = datetime.today().strftime("%Y년 %m월 %d일")
year = datetime.today().year

# ✅ 파일별 발행일 관리
if os.path.exists(published_dates_file):
    try:
        with open(published_dates_file, "r", encoding="utf-8") as f:
            published_dates = json.load(f)
    except json.JSONDecodeError:
        print("🚫 'published_dates.json' 파일이 손상되었습니다. 새로 생성합니다.")
        published_dates = {}
else:
    published_dates = {}

# ✅ 출발지 기준 도착지 리스트 불러오기 (파일이 없으면 빈 딕셔너리)
try:
    with open(route_file_path, "r", encoding="utf-8") as f:
        route_map = json.load(f)
    print(f"✅ 노선 데이터 로드 완료: {route_file_path}")
except FileNotFoundError:
    print(f"⚠️  노선 파일을 찾을 수 없습니다: {route_file_path}")
    print("📝 내부 링크 생성을 건너뛰고 계속 진행합니다.")
    route_map = {}
except json.JSONDecodeError:
    print(f"🚫 노선 파일이 손상되었습니다: {route_file_path}")
    print("📝 내부 링크 생성을 건너뛰고 계속 진행합니다.")
    route_map = {}

# ✅ 생성된 HTML 파일 목록
all_created_files = []
all_skipped_destinations = []

def extract_duration_minutes(info_text):
    """차편정보에서 소요시간(분) 추출"""
    if not info_text:
        return 0
    
    try:
        # "경남여객(일반)1:10 소요" → "1:10" 추출
        import re
        time_match = re.search(r'(\d+):(\d+)\s*소요', info_text)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            return hours * 60 + minutes
        
        # "1시간 30분" 형태도 처리
        hour_match = re.search(r'(\d+)시간', info_text)
        min_match = re.search(r'(\d+)분', info_text)
        
        hours = int(hour_match.group(1)) if hour_match else 0
        minutes = int(min_match.group(1)) if min_match else 0
        
        return hours * 60 + minutes
    except:
        return 0

def sanitize_filename(filename):
    """파일명에서 특수문자를 제거하거나 안전한 문자로 대체"""
    # 허용되지 않는 문자들을 대체
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\r', '\t']
    sanitized = filename
    
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '-')
    
    # 연속된 하이픈을 하나로 변경
    while '--' in sanitized:
        sanitized = sanitized.replace('--', '-')
    
    # 앞뒤 하이픈 제거
    sanitized = sanitized.strip('-')
    
    # 빈 문자열 방지
    if not sanitized or sanitized.isspace():
        sanitized = "unknown"
    
    return sanitized

def generate_internal_links(route_map, dep_terminal, arr_terminal, max_links=7):
    """내부 링크 생성 함수 - route_map이 비어있으면 빈 문자열 반환"""
    if not route_map or dep_terminal not in route_map:
        return ""  # 📝 노선 데이터가 없으면 내부 링크를 생성하지 않음
        
    links_html = ""
    others = [to for to in route_map.get(dep_terminal, []) if to != arr_terminal]
    
    if not others:  # 다른 노선이 없으면 빈 문자열 반환
        return ""
        
    random.shuffle(others)
    max_links = min(len(others), max_links)
    others = others[:max_links]
    
    links_html += f"""
    <div class='other-routes'>
        <h3>🚌 {dep_terminal}에서 출발하는 다른 주요 노선</h3>
        <div class='route-grid'>
    """
    for to in others:
        links_html += f"""
            <a href="/{dep_terminal}-에서-{to}-가는-시외버스-시간표" class="route-card">
                <span class="route-text">{dep_terminal} → {to}</span>
                <span class="route-arrow">→</span>
            </a>
        """
    links_html += "</div></div>"
    return links_html

# ✅ 새로운 현대적인 HTML 템플릿
html_template = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3349170217265964" crossorigin="anonymous"></script>
    
    <!-- 📅 발행일 및 수정일 메타데이터 (property와 name 혼용) -->
    <meta property="article:published_time" content="{published_date}">
    <meta property="article:modified_time" content="{last_modified_date}">
    <meta name="date" content="{today_date}">
    <meta name="last-modified" content="{last_modified_date}">

    <!-- 🎯 SEO 최적화 -->
    <title>{dep_terminal}에서 {arr_terminal} 가는 시외버스 시간표 | 첫차·막차·소요시간</title>
    <meta name="description" content="🚍 {dep_terminal}에서 {arr_terminal} 가는 최신 시외버스 시간표입니다. 총 {bus_count}회 운행 중이며, 첫차 {first_bus}, 막차 {last_bus}로 운행됩니다. 요금과 소요시간을 확인하고 빠르게 예매하세요.">
    <meta name="keywords" content="{dep_terminal} {arr_terminal} 시외버스, {dep_terminal} {arr_terminal} 버스 시간표, {dep_terminal} {arr_terminal} 버스 요금, {dep_terminal} {arr_terminal} 버스 예매">
    <meta name="robots" content="index, follow">
    <meta name="author" content="버스 시간표 서비스">

    <!-- 🔗 Canonical URL -->
    <link rel="canonical" href="https://bus.medilocator.co.kr/{dep_terminal}-에서-{arr_terminal}-가는-시외버스-시간표">

    <!-- 📱 Open Graph -->
    <meta property="og:title" content="{dep_terminal}에서 {arr_terminal} 가는 시외버스 시간표">
    <meta property="og:description" content="🚍 {dep_terminal}에서 {arr_terminal} 가는 최신 시외버스 시간표를 확인하고 빠르게 예매하세요!">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://bus.medilocator.co.kr/{dep_terminal}-에서-{arr_terminal}-가는-시외버스-시간표">
    <meta property="og:image" content="https://bus.medilocator.co.kr/images/bus.jpg">
    <meta property="og:site_name" content="버스 시간표">
    <meta property="og:locale" content="ko_KR">

    <!-- 🐦 Twitter Cards -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{dep_terminal}에서 {arr_terminal} 가는 시외버스 시간표">
    <meta name="twitter:description" content="🚍 {dep_terminal}에서 {arr_terminal} 가는 최신 시외버스 시간표를 확인하고 빠르게 예매하세요!">
    <meta name="twitter:image" content="https://bus.medilocator.co.kr/images/bus.jpg">

    <!-- 🎨 모바일 테마 -->
    <meta name="theme-color" content="#2563eb">
    
    <!-- 📱 Font & Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            line-height: 1.6;
            color: #1e293b;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px 0;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        .main-card {{
            background: white;
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            overflow: hidden;
            margin-bottom: 30px;
        }}

        .header {{
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="2" fill="rgba(255,255,255,0.1)"/></svg>') repeat;
            animation: float 20s infinite linear;
        }}

        @keyframes float {{
            0% {{ transform: translateX(0) translateY(0) rotate(0deg); }}
            100% {{ transform: translateX(-50px) translateY(-50px) rotate(360deg); }}
        }}

        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
            position: relative;
            z-index: 1;
        }}

        .header .subtitle {{
            font-size: 16px;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }}

        .info-section {{
            padding: 40px 30px;
            background: #f8fafc;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .info-card {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #2563eb;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .info-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.1);
        }}

        .info-card-title {{
            font-size: 14px;
            color: #64748b;
            margin-bottom: 8px;
            font-weight: 500;
        }}

        .info-card-value {{
            font-size: 20px;
            font-weight: 600;
            color: #1e293b;
        }}

        .schedule-section {{
            padding: 0 30px 40px;
        }}

        .schedule-title {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 24px;
            text-align: center;
            color: #1e293b;
        }}

        .schedule-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .schedule-table th {{
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white;
            padding: 16px;
            font-weight: 600;
            text-align: center;
            font-size: 14px;
        }}

        .schedule-table td {{
            padding: 16px;
            text-align: center;
            border-bottom: 1px solid #e2e8f0;
            font-size: 15px;
        }}

        .schedule-table tr:last-child td {{
            border-bottom: none;
        }}

        .schedule-table tr:hover {{
            background: #f8fafc;
        }}

        .btn-book {{
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.2s ease;
            display: inline-block;
        }}

        .btn-book:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(220, 38, 38, 0.3);
        }}

        .booking-section {{
            background: white;
            border-radius: 24px;
            padding: 40px 30px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }}

        .booking-title {{
            font-size: 24px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 16px;
            color: #1e293b;
        }}

        .booking-subtitle {{
            text-align: center;
            color: #64748b;
            margin-bottom: 32px;
            font-size: 16px;
        }}

        .booking-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}

        .booking-btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            padding: 16px 24px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .booking-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.2);
        }}

        .btn-bustago {{
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
        }}

        .btn-tmoney {{
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            color: white;
        }}

        .btn-kobus {{
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
            color: white;
        }}

        .return-section {{
            background: white;
            border-radius: 24px;
            padding: 40px 30px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            text-align: center;
        }}

        .return-btn {{
            display: inline-flex;
            align-items: center;
            gap: 12px;
            padding: 16px 32px;
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            color: white;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .return-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.2);
        }}

        .other-routes {{
            background: white;
            border-radius: 24px;
            padding: 40px 30px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }}

        .other-routes h3 {{
            font-size: 24px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 32px;
            color: #1e293b;
        }}

        .route-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
        }}

        .route-card {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 12px;
            text-decoration: none;
            color: #1e293b;
            font-weight: 500;
            transition: all 0.3s ease;
            border: 1px solid #e2e8f0;
        }}

        .route-card:hover {{
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 8px 15px -3px rgba(37, 99, 235, 0.3);
        }}

        .route-arrow {{
            font-size: 18px;
            opacity: 0.7;
        }}

        .hub-section {{
            background: white;
            border-radius: 24px;
            padding: 40px 30px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            text-align: center;
        }}

        .hub-btn {{
            display: inline-flex;
            align-items: center;
            gap: 12px;
            padding: 16px 32px;
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            color: white;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .hub-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 15px -3px rgba(5, 150, 105, 0.3);
        }}

        .train-section {{
            background: white;
            border-radius: 24px;
            padding: 40px 30px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            text-align: center;
        }}

        .train-btn {{
            display: inline-flex;
            align-items: center;
            gap: 12px;
            padding: 16px 32px;
            background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
            color: white;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .train-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 15px -3px rgba(124, 58, 237, 0.3);
        }}

        .faq-section {{
            background: white;
            border-radius: 24px;
            padding: 40px 30px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }}

        .faq-container {{
            max-width: 100%;
        }}

        .faq-item {{
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            margin-bottom: 16px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}

        .faq-item:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}

        .faq-question {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 20px 24px;
            background: #f8fafc;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            font-size: 16px;
            color: #1e293b;
        }}

        .faq-question:hover {{
            background: #e2e8f0;
        }}

        .faq-item.active .faq-question {{
            background: #2563eb;
            color: white;
        }}

        .faq-question span {{
            flex: 1;
        }}

        .faq-icon {{
            font-size: 14px;
            transition: transform 0.3s ease;
            color: #64748b;
        }}

        .faq-item.active .faq-icon {{
            color: white;
        }}

        .faq-answer {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
            background: white;
        }}

        .faq-answer p {{
            padding: 20px 24px;
            margin: 0;
            line-height: 1.7;
            color: #475569;
            font-size: 15px;
        }}

        .faq-answer strong {{
            color: #2563eb;
            font-weight: 600;
        }}

        .update-info {{
            text-align: center;
            margin-top: 32px;
            padding: 20px;
            background: #f1f5f9;
            border-radius: 12px;
            color: #64748b;
            font-size: 14px;
        }}

        /* 📱 반응형 디자인 */
        @media (max-width: 768px) {{
            .container {{
                padding: 0 16px;
            }}

            .header {{
                padding: 30px 20px;
            }}

            .header h1 {{
                font-size: 24px;
            }}

            .info-section,
            .schedule-section,
            .booking-section,
            .return-section,
            .other-routes,
            .hub-section,
            .train-section {{
                padding: 30px 20px;
            }}

            .info-grid {{
                grid-template-columns: 1fr;
                gap: 16px;
            }}

            .booking-grid {{
                grid-template-columns: 1fr;
            }}

            .route-grid {{
                grid-template-columns: 1fr;
            }}

            .schedule-table th,
            .schedule-table td {{
                padding: 12px 8px;
                font-size: 14px;
            }}
        }}
    </style>
    {structured_data}
</head>
<body>
    <div class="container">
        <!-- 🎯 메인 헤더 -->
        <div class="main-card">
            <div class="header">
                <h1><i class="fas fa-bus"></i> {dep_terminal}에서 {arr_terminal}가는 버스 시간표</h1>
                <p class="subtitle">시외버스 시간표 및 예매 안내</p>
            </div>

            <!-- 📊 정보 섹션 -->
            <div class="info-section">
                <div class="info-grid">
                    <div class="info-card">
                        <div class="info-card-title"><i class="fas fa-calendar-day"></i> 기준 연도</div>
                        <div class="info-card-value">{year}년</div>
                    </div>
                    <div class="info-card">
                        <div class="info-card-title"><i class="fas fa-bus"></i> 일일 운행 횟수</div>
                        <div class="info-card-value">{bus_count}회</div>
                    </div>
                    <div class="info-card">
                        <div class="info-card-title"><i class="fas fa-clock"></i> 첫차 시간</div>
                        <div class="info-card-value">{first_bus}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-card-title"><i class="fas fa-moon"></i> 막차 시간</div>
                        <div class="info-card-value">{last_bus}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-card-title"><i class="fas fa-route"></i> 평균 소요시간</div>
                        <div class="info-card-value">{avg_duration}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-card-title"><i class="fas fa-map-marker-alt"></i> 출발 터미널</div>
                        <div class="info-card-value">
                            <a href="https://www.google.com/maps/search/{dep_terminal} 터미널" target="_blank" style="color: #2563eb; text-decoration: none;">
                                {dep_terminal}
                            </a>
                        </div>
                    </div>
                </div>
                
                <p style="text-align: center; color: #64748b; line-height: 1.8;">
                    본 페이지는 <strong>버스타고</strong>, <strong>코버스</strong>, <strong>티머니</strong>의 공식 정보를 바탕으로 
                    최신 버스 시간표를 제공합니다. 정확한 운행 일정과 요금을 확인 후 예매하시기 바랍니다.
                </p>
            </div>

            <!-- 🕐 시간표 섹션 -->
            <div class="schedule-section">
                <h2 class="schedule-title"><i class="fas fa-table"></i> 상세 시간표</h2>
                <table class="schedule-table">
                    <thead>
                        <tr>
                            <th><i class="fas fa-clock"></i> 출발시간</th>
                            <th><i class="fas fa-hourglass-half"></i> 소요시간</th>
                            <th><i class="fas fa-building"></i> 운행회사</th>
                            <th><i class="fas fa-ticket-alt"></i> 예매하기</th>
                        </tr>
                    </thead>
                    <tbody>
                        {bus_rows}
                    </tbody>
                </table>
                
                <div class="update-info">
                    <i class="fas fa-info-circle"></i>
                    <strong>최신 업데이트:</strong> {update_date} | 
                    <strong>발행일:</strong> {published_date} | 
                    <strong>수정일:</strong> {last_modified_date}
                </div>
            </div>
        </div>

        <!-- 🎫 예매 섹션 -->
        <div class="booking-section">
            <h2 class="booking-title"><i class="fas fa-ticket-alt"></i> 빠른 예매하기</h2>
            <p class="booking-subtitle">아래 공식 예매 사이트에서 실시간 좌석을 확인하고 예약하세요</p>
            <div class="booking-grid">
                <a href="https://www.bustago.or.kr" target="_blank" class="booking-btn btn-bustago">
                    <i class="fas fa-bus"></i>
                    <span>버스타고</span>
                </a>
                <a href="https://www.t-money.co.kr" target="_blank" class="booking-btn btn-tmoney">
                    <i class="fas fa-credit-card"></i>
                    <span>티머니</span>
                </a>
                <a href="https://www.kobus.co.kr" target="_blank" class="booking-btn btn-kobus">
                    <i class="fas fa-globe"></i>
                    <span>코버스</span>
                </a>
            </div>
        </div>

        <!-- 🔄 돌아오는 버스 -->
        <div class="return-section">
            <h2 class="booking-title"><i class="fas fa-undo-alt"></i> 돌아오는 시간표</h2>
            <p class="booking-subtitle"><strong>{arr_terminal}</strong>에서 <strong>{dep_terminal}</strong>로 가는 버스 시간표를 확인하세요</p>
            <a href="https://bus.medilocator.co.kr/{arr_terminal}-에서-{dep_terminal}-가는-시외버스-시간표" class="return-btn">
                <i class="fas fa-arrow-left"></i>
                <span>{arr_terminal} → {dep_terminal} 시간표</span>
            </a>
        </div>

        <!-- 🗺️ 전체 노선 -->
        <div class="hub-section">
            <h2 class="booking-title"><i class="fas fa-map"></i> {dep_terminal} 전체 노선 보기</h2>
            <p class="booking-subtitle">{dep_terminal}에서 출발하는 모든 버스 노선을 한 번에 확인하세요</p>
            <a href="/{dep_terminal}-시외버스터미널-버스-시간표" class="hub-btn">
                <i class="fas fa-list"></i>
                <span>{dep_terminal} 전체 시간표</span>
            </a>
        </div>

        <!-- 🚌 다른 노선들 -->
        {related_links}

        <!-- 🚄 기차 시간표 -->
        <div class="train-section">
            <h2 class="booking-title"><i class="fas fa-train"></i> 기차 시간표도 확인해보세요</h2>
            <p class="booking-subtitle">버스 외에 기차 시간표도 함께 비교해서 더 편리한 교통편을 선택하세요</p>
            <a href="https://time.guide-lee.co.kr" target="_blank" class="train-btn">
                <i class="fas fa-train"></i>
                <span>기차 시간표 확인하기</span>
            </a>
        </div>

        <!-- 🤔 FAQ 섹션 -->
        <div class="faq-section">
            <h2 class="booking-title"><i class="fas fa-question-circle"></i> 자주 묻는 질문 (FAQ)</h2>
            <div class="faq-container">
                <div class="faq-item">
                    <div class="faq-question">
                        <i class="fas fa-clock"></i>
                        <span>{dep_terminal}에서 {arr_terminal} 가는 첫차와 막차는 몇 시인가요?</span>
                        <i class="fas fa-chevron-down faq-icon"></i>
                    </div>
                    <div class="faq-answer">
                        <p>{dep_terminal}에서 {arr_terminal}로 가는 첫차는 <strong>{first_bus}</strong>이고, 막차는 <strong>{last_bus}</strong>입니다. 주말이나 공휴일에는 운행 시간이 달라질 수 있으니 예매 전 확인하시기 바랍니다.</p>
                    </div>
                </div>

                <div class="faq-item">
                    <div class="faq-question">
                        <i class="fas fa-route"></i>
                        <span>{dep_terminal}에서 {arr_terminal}까지 소요시간은 얼마나 걸리나요?</span>
                        <i class="fas fa-chevron-down faq-icon"></i>
                    </div>
                    <div class="faq-answer">
                        <p>{dep_terminal}에서 {arr_terminal}까지 평균 소요시간은 <strong>{avg_duration}</strong>입니다. 교통 상황이나 경유지에 따라 시간이 달라질 수 있습니다.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

<script>
// FAQ 아코디언 기능
document.addEventListener('DOMContentLoaded', function() {{
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {{
        const question = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');
        const icon = item.querySelector('.faq-icon');
        
        question.addEventListener('click', () => {{
            const isActive = item.classList.contains('active');
            
            // 모든 FAQ 아이템 닫기
            faqItems.forEach(otherItem => {{
                otherItem.classList.remove('active');
                otherItem.querySelector('.faq-answer').style.maxHeight = '0';
                otherItem.querySelector('.faq-icon').style.transform = 'rotate(0deg)';
            }});
            
            // 클릭한 아이템이 비활성 상태였다면 열기
            if (!isActive) {{
                item.classList.add('active');
                answer.style.maxHeight = answer.scrollHeight + 'px';
                icon.style.transform = 'rotate(180deg)';
            }}
        }});
    }});
}});
</script>

{structured_data}
</body>
</html>
"""

# 🚀 모든 JSON 파일 처리 시작
print(f"\n🚀 HTML 파일 생성 시작...")

for json_file_path in json_files:
    print(f"\n📄 처리 중: {json_file_path}")
    
    # ✅ 출발지 자동 추출 (파일명 기반)
    filename = os.path.basename(json_file_path)
    dep_terminal = filename.replace("_schedules.json", "")
    
    # 🔍 JSON 파일 확인
    if not os.path.exists(json_file_path):
        print(f"🚫 파일을 찾을 수 없습니다: {json_file_path}")
        continue

    # 🔍 JSON 파일 읽기
    try:
        with open(json_file_path, encoding='utf-8') as f:
            bus_data = json.load(f)
        print(f"✅ JSON 데이터 로드 완료.")
        print(f"📊 데이터 타입: {type(bus_data)}")
    except Exception as e:
        print(f"🚫 JSON 파일 읽기 오류: {e}")
        continue

    # ✅ JSON 데이터의 구조 확인 및 변환
    schedules = {}  # 📌 schedules 변수 초기화

    if isinstance(bus_data, list):
        print(f"📋 리스트 형태 데이터 감지. 항목 개수: {len(bus_data)}")
        
        # 새로운 JSON 구조에 맞게 처리: [{"출발지": "인천", "도착지": "신갈", "스케줄": [...]}]
        for route_item in bus_data:
            if isinstance(route_item, dict):
                departure = route_item.get('출발지', '')
                destination = route_item.get('도착지', '')
                schedule_list = route_item.get('스케줄', [])
                
                print(f"🚌 노선: {departure} → {destination} ({len(schedule_list)}개 스케줄)")
                
                if destination and schedule_list:
                    if destination not in schedules:
                        schedules[destination] = []
                    
                    # 스케줄 리스트의 각 항목을 버스 데이터로 변환
                    for schedule in schedule_list:
                        if isinstance(schedule, dict):
                            # 기존 버스 데이터 형식으로 변환
                            bus_data_converted = {
                                'TIM_TIM': schedule.get('출발시각', '').replace(':', ''),  # "07:45" → "0745"
                                'COR_NAM': schedule.get('차편정보', '').split('(')[0] if schedule.get('차편정보') else '정보 없음',  # "경남여객(일반)" → "경남여객"
                                'LIN_TIM': extract_duration_minutes(schedule.get('차편정보', '')),  # "1:10 소요" → 70분
                                'ARR_PLN': destination,
                                'DEP_PLN': departure,
                                '출발시각': schedule.get('출발시각', ''),
                                '차편정보': schedule.get('차편정보', ''),
                                '어른요금': schedule.get('어른요금', ''),
                                '잔여좌석': schedule.get('잔여좌석', '')
                            }
                            schedules[destination].append(bus_data_converted)
        
        print(f"🔷 변환된 도착지 개수: {len(schedules)}")
        if schedules:
            print(f"🔷 도착지 목록: {list(schedules.keys())[:10]}")  # 처음 10개만 표시

    elif isinstance(bus_data, dict):
        print(f"📋 딕셔너리 형태 데이터 감지. 키 개수: {len(bus_data)}")
        print(f"🔷 첫 5개 키: {list(bus_data.keys())[:5]}")
        schedules = bus_data

    else:
        print("🚫 JSON 데이터가 올바른 형식이 아닙니다. 리스트 또는 딕셔너리 구조여야 합니다.")
        continue

    # ✅ 도착지별 HTML 파일 생성
    skipped_destinations = []  # 현재 파일에서 건너뛴 도착지 목록
    created_files = []  # 현재 파일에서 생성된 HTML 파일 목록
    last_modified_date = today_date  # 📌 기본값 설정

    print(f"\n📋 {dep_terminal}: 처리할 도착지 개수: {len(schedules)}")

    for arr_terminal, schedule_list in schedules.items():
        arr_terminal_original = str(arr_terminal)  # 원본 도착지명 보존
        arr_terminal_safe = sanitize_filename(arr_terminal_original)  # 파일명용 안전한 이름
        
        try:
            # ✅ 시간표 데이터가 없거나 비어있으면 건너뛰기
            if not schedule_list or len(schedule_list) == 0:
                print(f"⚠️  {arr_terminal_original}: 시간표 데이터가 없어 건너뜁니다.")
                skipped_destinations.append(f"{arr_terminal_original} (데이터 없음)")
                continue
            
            # ✅ 버스 시간표 데이터 처리 (새로운 JSON 구조에 맞게)
            valid_buses = []
            for bus in schedule_list:
                # 시간 정보 확인 (변환된 데이터 구조)
                dep_time_raw = bus.get('TIM_TIM') or bus.get('출발시각', '')
                
                if dep_time_raw and str(dep_time_raw).strip():
                    valid_buses.append(bus)
                    if len(valid_buses) <= 3:  # 처음 3개만 로그 출력
                        print(f"   ✅ 유효한 버스: {dep_time_raw} - {bus.get('COR_NAM', bus.get('차편정보', ''))}")
            
            print(f"   📊 총 {len(schedule_list)}개 중 {len(valid_buses)}개 유효한 버스 발견")
            
            # ✅ 유효한 버스 데이터가 없으면 건너뛰기
            if not valid_buses:
                print(f"⚠️  {arr_terminal_original}: 유효한 시간표 데이터가 없어 건너뜁니다.")
                skipped_destinations.append(f"{arr_terminal_original} (유효 데이터 없음)")
                continue
            
            # ✅ 파일명 안전성 검사
            if arr_terminal_original != arr_terminal_safe:
                print(f"🔧 {arr_terminal_original}: 특수문자 포함으로 파일명을 '{arr_terminal_safe}'로 변경합니다.")
            
            print(f"📍 {arr_terminal_original}: {len(valid_buses)}개의 시간표로 HTML 생성 중...")

            # ✅ HTML 파일명 생성 (안전한 이름 사용)
            html_filename = f"{dep_terminal}-에서-{arr_terminal_safe}-가는-시외버스-시간표.html"
            html_file_path = os.path.join(output_folder, html_filename)

            # ✅ 현재 파일의 발행일 가져오기
            published_date = published_dates.get(html_filename, today_date)

            # ✅ 발행일이 등록되지 않았다면 JSON 파일에 저장
            if html_filename not in published_dates:
                published_dates[html_filename] = today_date

            # ✅ 마지막 수정일
            last_modified_date = today_date

            # ✅ 버스 시간표 데이터 처리 (valid_buses 사용)
            bus_rows = ""
            times, durations, companies = [], [], []

            for bus in valid_buses:  # 유효한 버스 데이터만 사용
                # 새로운 JSON 구조에 맞게 시간 정보 추출
                dep_time_raw = bus.get('TIM_TIM', bus.get('출발시각', '0000'))
                if isinstance(dep_time_raw, str):
                    if ':' in dep_time_raw:  # "07:45" 형태
                        dep_time = dep_time_raw
                    elif len(dep_time_raw) >= 4:  # "0745" 형태
                        dep_time = f"{dep_time_raw[:2]}:{dep_time_raw[2:4]}"
                    else:
                        dep_time = dep_time_raw
                else:
                    dep_time = str(dep_time_raw)
                
                # 소요시간 정보 추출
                duration_min = bus.get('LIN_TIM', 0)
                if duration_min > 0:
                    duration = f"{duration_min//60}시간 {duration_min%60}분"
                else:
                    duration = "정보 없음"
                
                # 운행회사 정보 추출
                company = bus.get("COR_NAM", bus.get("차편정보", "정보 없음"))
                if company and company != "정보 없음":
                    # "경남여객(일반)1:10 소요" → "경남여객" 추출
                    company = company.split('(')[0].strip()

                times.append(dep_time)
                durations.append(duration_min)
                companies.append(company)

                bus_rows += f"""
                    <tr>
                        <td><strong>{dep_time}</strong></td>
                        <td>{duration}</td>
                        <td>{company}</td>
                        <td><a href='https://www.bustago.or.kr/newweb/kr/booking/info_schedule.jsp' target='_blank' class='btn-book'><i class="fas fa-ticket-alt"></i> 예매</a></td>
                    </tr>
                """

            # ✅ 기본 정보 계산 (이 시점에서 times는 비어있지 않음을 보장)
            first_bus = min(times) if times else "정보 없음"
            last_bus = max(times) if times else "정보 없음"
            avg_duration = f"{(sum(durations)//len(durations))//60}시간 {(sum(durations)//len(durations))%60}분" if durations else "정보 없음"
            bus_count = len(times)

            # ✅ 구조화 데이터 생성
            structured_data = ""
            if times and durations and first_bus != "정보 없음":
                try:
                    first_bus_hour, first_bus_minute = map(int, first_bus.split(":"))
                    avg_minute_duration = sum(durations)//len(durations) if durations else 0
                    arrival_total_min = first_bus_hour * 60 + first_bus_minute + avg_minute_duration
                    arrival_hour_str = str(arrival_total_min // 60).zfill(2)
                    arrival_minute_str = str(arrival_total_min % 60).zfill(2)
                    first_bus_hour_str = str(first_bus_hour).zfill(2)
                    first_bus_minute_str = str(first_bus_minute).zfill(2)

                    unique_companies = list(set([c for c in companies if c != "정보 없음"]))
                    if len(unique_companies) == 1:
                        provider_json = f'  "provider": {{"@type": "Organization", "name": "{unique_companies[0]}"}},'
                    elif len(unique_companies) > 1:
                        provider_json = '  "provider": [' + ",".join([f'{{"@type": "Organization", "name": "{c}"}}' for c in unique_companies]) + '],'
                    else:
                        provider_json = ''

                    structured_data = f"""
                <script type="application/ld+json">
                {{
                    "@context": "https://schema.org",
                    "@type": "BusTrip",
                    "name": "{dep_terminal}에서 {arr_terminal_original} 가는 시외버스 시간표",
                    "description": "{dep_terminal}에서 {arr_terminal_original} 가는 시외버스 시간표, 요금, 소요시간 정보",
                    {provider_json}
                    "departureBusStop": {{"@type": "BusStation", "name": "{dep_terminal} 터미널"}},
                    "arrivalBusStop": {{"@type": "BusStation", "name": "{arr_terminal_original} 터미널"}},
                    "departureTime": "{first_bus_hour_str}:{first_bus_minute_str}",
                    "arrivalTime": "{arrival_hour_str}:{arrival_minute_str}",
                    "busNumber": "{bus_count}",
                    "url": "https://bus.medilocator.co.kr/{dep_terminal}-에서-{arr_terminal_safe}-가는-시외버스-시간표"
                }}
                </script>
                """
                except (ValueError, AttributeError):
                    structured_data = ""

            # ✅ 내부링크 생성 (원본 도착지명 사용)
            related_links = generate_internal_links(route_map, dep_terminal, arr_terminal_original)

            # ✅ HTML 내용 생성 (원본 도착지명을 화면 표시용으로 사용)
            html_content = html_template.format(
                dep_terminal=dep_terminal,
                arr_terminal=arr_terminal_original,  # 화면에는 원본 이름 표시
                today_date=today_date,
                year=year,
                bus_count=bus_count,
                first_bus=first_bus,
                last_bus=last_bus,
                avg_duration=avg_duration,
                bus_rows=bus_rows,
                update_date=update_date,
                published_date=published_dates.get(html_filename, today_date),
                last_modified_date=today_date,
                structured_data=structured_data,
                related_links=related_links
            )

            # ✅ HTML 파일 저장
            with open(html_file_path, "w", encoding="utf-8") as html_file:
                html_file.write(html_content)

            created_files.append(html_filename)
            all_created_files.append(html_filename)
            print(f"   ✅ 생성 완료: {html_filename}")

        except Exception as e:
            # ✅ 개별 노선 처리 중 오류 발생 시 해당 노선만 건너뛰고 계속 진행
            error_msg = f"{arr_terminal_original} (오류: {str(e)})"
            print(f"🚫 {arr_terminal_original}: 처리 중 오류 발생 - {str(e)}")
            print(f"   ➡️  해당 노선을 건너뛰고 다음 노선을 처리합니다.")
            skipped_destinations.append(error_msg)
            all_skipped_destinations.extend([error_msg])
            continue

    # ✅ 현재 파일 처리 결과
    total_destinations = len(schedules)
    generated_files = len(created_files)
    skipped_count = len(skipped_destinations)

    print(f"\n📊 {dep_terminal} 처리 결과:")
    print(f"   📁 전체 도착지: {total_destinations}개")
    print(f"   ✅ 생성된 파일: {generated_files}개")
    print(f"   ⚠️  건너뛴 도착지: {skipped_count}개")

    if created_files:
        print(f"\n📋 생성된 파일 목록:")
        for i, file in enumerate(created_files, 1):
            print(f"  {i:2d}. {file}")

    if skipped_destinations:
        print(f"\n⚠️  건너뛴 도착지 목록:")
        for i, destination in enumerate(skipped_destinations, 1):
            print(f"  {i:2d}. {destination}")

# ✅ JSON 파일 업데이트 후 저장
with open(published_dates_file, "w", encoding="utf-8") as f:
    json.dump(published_dates, f, ensure_ascii=False, indent=4)

# ✅ 최종 전체 결과
total_json_files = len(json_files)
total_generated_files = len(all_created_files)
total_skipped = len(all_skipped_destinations)

print(f"\n🎉 모든 JSON 파일 처리 완료!")
print(f"📅 발행일: {today_date} | 마지막 수정일: {last_modified_date}")
print(f"📊 전체 처리 결과:")
print(f"   📄 처리된 JSON 파일: {total_json_files}개")
print(f"   ✅ 생성된 HTML 파일: {total_generated_files}개")
print(f"   ⚠️  건너뛴 도착지: {total_skipped}개")

if all_created_files:
    print(f"\n📋 전체 생성된 파일 목록 (처음 20개):")
    for i, file in enumerate(all_created_files[:20], 1):
        print(f"  {i:2d}. {file}")
    if len(all_created_files) > 20:
        print(f"  ... 외 {len(all_created_files) - 20}개 파일")

if all_skipped_destinations:
    print(f"\n⚠️  전체 건너뛴 도착지 목록 (처음 10개):")
    for i, destination in enumerate(all_skipped_destinations[:10], 1):
        print(f"  {i:2d}. {destination}")
    if len(all_skipped_destinations) > 10:
        print(f"  ... 외 {len(all_skipped_destinations) - 10}개 도착지")

if not all_created_files:
    print("\n🚫 생성된 HTML 파일이 없습니다. JSON 데이터를 확인하세요.")

print(f"\n✨ 새로운 특징:")
print("  🎨 현대적인 그라데이션 디자인")
print("  📱 완전 반응형 레이아웃") 
print("  🎯 향상된 SEO 최적화")
print("  ⚡ 부드러운 애니메이션 효과")
print("  🔍 구조화된 데이터 포함")
print("  📋 meta property와 name 혼용 적용")
print("  🚌 새로운 제목 형식: '출발지에서-도착지-가는-시외버스-시간표'")
print("  🛡️ 강화된 오류 처리 및 다양한 JSON 구조 지원")
print("  🚫 시간표 데이터가 없는 도착지 자동 건너뛰기")
print("  🔧 특수문자 포함 도착지명 안전 처리")
print("  🔄 개별 노선 오류 시 자동 복구 (다음 노선 계속 처리)")
print("  📁 data 폴더의 모든 JSON 파일 자동 처리")