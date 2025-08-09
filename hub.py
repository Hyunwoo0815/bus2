import os
import json
import glob
from urllib.parse import quote
from datetime import datetime

def load_route_data():
    """data 폴더의 모든 JSON 파일에서 노선 정보를 추출합니다."""
    routes = []
    
    # data 폴더의 모든 JSON 파일 찾기
    json_files = glob.glob('data/*.json')
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 출발지와 도착지 추출
            if 'route' in data:
                route_info = data['route']
                departure = route_info.get('departure', '')
                arrival = route_info.get('arrival', '')
                
                if departure and arrival:
                    routes.append({
                        'departure': departure,
                        'arrival': arrival,
                        'filename': f"{departure}-에서-{arrival}-가는-시외버스-시간표.html",
                        'url': f"/{departure}-에서-{arrival}-가는-시외버스-시간표"
                    })
                    
        except Exception as e:
            print(f"❌ {json_file} 파일 처리 중 오류: {e}")
            continue
    
    return routes

def group_routes_by_departure(routes):
    """출발지별로 노선을 그룹화합니다."""
    grouped = {}
    
    for route in routes:
        departure = route['departure']
        if departure not in grouped:
            grouped[departure] = []
        grouped[departure].append(route)
    
    # 도착지별로 정렬
    for departure in grouped:
        grouped[departure].sort(key=lambda x: x['arrival'])
    
    return grouped

def generate_terminal_page(terminal_name, destinations):
    """개별 터미널 페이지 HTML을 생성합니다."""
    
    html_content = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- 📅 발행일 및 수정일 메타데이터 -->
    <meta property="article:published_time" content="{datetime.now().strftime('%Y-%m-%d')}">
    <meta property="article:modified_time" content="{datetime.now().strftime('%Y-%m-%d')}">
    <meta name="date" content="{datetime.now().strftime('%Y-%m-%d')}">
    <meta name="last-modified" content="{datetime.now().strftime('%Y-%m-%d')}">

    <!-- 🎯 SEO 최적화 -->
    <title>{terminal_name} 터미널 시외버스 시간표 | {len(destinations)}개 노선</title>
    <meta name="description" content="🚌 {terminal_name} 터미널에서 출발하는 시외버스 시간표를 확인하세요. {len(destinations)}개 목적지로 가는 버스 시간표를 한눈에 볼 수 있습니다.">
    <meta name="keywords" content="{terminal_name} 터미널, {terminal_name} 시외버스, {terminal_name} 버스 시간표, 시외버스 시간표">
    <meta name="robots" content="index, follow">
    <meta name="author" content="버스 시간표 서비스">

    <!-- 🔗 Canonical URL -->
    <link rel="canonical" href="https://bus.medilocator.co.kr/{terminal_name}-터미널-시외버스-시간표">

    <!-- 📱 Open Graph -->
    <meta property="og:title" content="{terminal_name} 터미널 시외버스 시간표 | {len(destinations)}개 노선">
    <meta property="og:description" content="{terminal_name} 터미널에서 출발하는 시외버스 시간표를 확인하세요. {len(destinations)}개 목적지로 가는 버스 시간표를 제공합니다.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://bus.medilocator.co.kr/{terminal_name}-터미널-시외버스-시간표">
    <meta property="og:image" content="https://bus.medilocator.co.kr/images/bus.jpg">
    <meta property="og:site_name" content="전국 시외버스 시간표">
    <meta property="og:locale" content="ko_KR">

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
            max-width: 1000px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        .main-header {{
            background: white;
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            overflow: hidden;
            margin-bottom: 40px;
        }}

        .header-content {{
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .header-content h1 {{
            font-size: 42px;
            font-weight: 700;
            margin-bottom: 16px;
        }}

        .header-content .subtitle {{
            font-size: 20px;
            opacity: 0.9;
        }}

        .breadcrumb {{
            background: #f8fafc;
            padding: 16px 24px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            color: #64748b;
        }}

        .breadcrumb a {{
            color: #2563eb;
            text-decoration: none;
        }}

        .breadcrumb a:hover {{
            text-decoration: underline;
        }}

        .search-section {{
            background: white;
            border-radius: 24px;
            padding: 30px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            margin-bottom: 40px;
        }}

        .search-box {{
            position: relative;
            max-width: 600px;
            margin: 0 auto;
        }}

        .search-input {{
            width: 100%;
            padding: 16px 50px 16px 20px;
            font-size: 18px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            outline: none;
            transition: border-color 0.3s ease;
        }}

        .search-input:focus {{
            border-color: #2563eb;
        }}

        .search-icon {{
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: #64748b;
            font-size: 20px;
        }}

        .routes-section {{
            background: white;
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            margin-bottom: 40px;
        }}

        .routes-title {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            color: #1e293b;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .routes-count {{
            background: #2563eb;
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 16px;
            font-weight: 600;
        }}

        .routes-subtitle {{
            color: #64748b;
            margin-bottom: 30px;
            font-size: 16px;
        }}

        .routes-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 16px;
        }}

        .route-card {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 24px;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            color: #1e293b;
            text-decoration: none;
            border-radius: 16px;
            font-size: 17px;
            font-weight: 600;
            transition: all 0.3s ease;
            border: 2px solid transparent;
            position: relative;
            overflow: hidden;
        }}

        .route-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 1;
        }}

        .route-card:hover::before {{
            opacity: 1;
        }}

        .route-card:hover {{
            color: white;
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.3);
            border-color: #2563eb;
        }}

        .route-text {{
            position: relative;
            z-index: 2;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .route-arrow {{
            position: relative;
            z-index: 2;
            font-size: 16px;
            opacity: 0.7;
        }}

        .no-routes {{
            text-align: center;
            padding: 60px 40px;
            color: #64748b;
        }}

        .no-routes i {{
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }}

        .back-to-home {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #2563eb;
            color: white;
            padding: 16px;
            border-radius: 50%;
            text-decoration: none;
            font-size: 20px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
            transition: all 0.3s ease;
            z-index: 1000;
        }}

        .back-to-home:hover {{
            background: #1d4ed8;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
        }}

        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: white;
            opacity: 0.8;
        }}

        .footer a {{
            color: white;
            text-decoration: none;
            font-weight: 500;
        }}

        .footer a:hover {{
            text-decoration: underline;
        }}

        /* 📱 반응형 디자인 */
        @media (max-width: 768px) {{
            .container {{
                padding: 0 16px;
            }}

            .header-content {{
                padding: 40px 20px;
            }}

            .header-content h1 {{
                font-size: 32px;
            }}

            .header-content .subtitle {{
                font-size: 16px;
            }}

            .routes-section {{
                padding: 24px 20px;
            }}

            .routes-grid {{
                grid-template-columns: 1fr;
                gap: 12px;
            }}

            .route-card {{
                padding: 16px 20px;
                font-size: 16px;
            }}

            .back-to-home {{
                bottom: 20px;
                right: 20px;
                padding: 14px;
                font-size: 18px;
            }}
        }}
    </style>

    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "{terminal_name} 터미널 시외버스 시간표",
        "description": "{terminal_name} 터미널에서 출발하는 시외버스 시간표 정보를 제공합니다.",
        "url": "https://bus.medilocator.co.kr/{terminal_name}-터미널-시외버스-시간표",
        "publisher": {{
            "@type": "Organization",
            "name": "버스 시간표 서비스"
        }}
    }}
    </script>
</head>
<body>
    <div class="container">
        <!-- 🎯 메인 헤더 -->
        <div class="main-header">
            <div class="header-content">
                <h1><i class="fas fa-bus"></i> {terminal_name} 터미널</h1>
                <p class="subtitle">시외버스 시간표 및 노선 안내</p>
            </div>
            <div class="breadcrumb">
                <a href="/"><i class="fas fa-home"></i> 홈</a>
                <i class="fas fa-chevron-right"></i>
                <span>{terminal_name} 터미널</span>
            </div>
        </div>

        <!-- 🔍 검색 섹션 -->
        <div class="search-section">
            <div class="search-box">
                <input type="text" class="search-input" id="searchInput" placeholder="목적지를 검색하세요... (예: 서울, 부산, 대전)">
                <i class="fas fa-search search-icon"></i>
            </div>
        </div>

        <!-- 🚌 노선 목록 -->
        <div class="routes-section">
            <h2 class="routes-title">
                <i class="fas fa-route"></i> 운행 노선
                <span class="routes-count">{len(destinations)}개 노선</span>
            </h2>
            <p class="routes-subtitle">{terminal_name}에서 출발하는 시외버스 노선을 선택하여 시간표를 확인하세요</p>
            
            <div class="routes-grid" id="routesGrid">'''

    if destinations:
        for destination in destinations:
            html_content += f'''
                <a href="{destination['url']}" class="route-card" data-destination="{destination['arrival']}">
                    <div class="route-text">
                        <i class="fas fa-map-marker-alt"></i>
                        {destination['arrival']} 시간표
                    </div>
                    <i class="fas fa-chevron-right route-arrow"></i>
                </a>'''
    else:
        html_content += '''
                <div class="no-routes">
                    <i class="fas fa-bus"></i>
                    <h3>운행 중인 노선이 없습니다</h3>
                    <p>현재 이 터미널에서 운행하는 시외버스 노선이 없습니다.</p>
                </div>'''

    html_content += f'''
            </div>
        </div>
    </div>

    <!-- 🏠 홈으로 버튼 -->
    <a href="/" class="back-to-home" title="메인으로 돌아가기">
        <i class="fas fa-home"></i>
    </a>

    <!-- 📝 푸터 -->
    <div class="footer">
        <p>&copy; 2025 전국 시외버스 시간표. 최신 업데이트: {datetime.now().strftime('%Y년 %m월 %d일')}</p>
        <p><a href="/sitemap.xml">사이트맵</a> | <a href="/rss.xml">RSS</a> | <a href="/">메인으로</a></p>
    </div>

    <script>
        // 검색 기능
        document.addEventListener('DOMContentLoaded', function() {{
            const searchInput = document.getElementById('searchInput');
            const routeCards = document.querySelectorAll('.route-card');

            searchInput.addEventListener('input', function() {{
                const searchTerm = this.value.toLowerCase().trim();
                
                routeCards.forEach(card => {{
                    const destination = card.dataset.destination.toLowerCase();
                    
                    if (searchTerm === '' || destination.includes(searchTerm)) {{
                        card.style.display = 'flex';
                    }} else {{
                        card.style.display = 'none';
                    }}
                }});
            }});

            // 카드 호버 효과
            routeCards.forEach(card => {{
                card.addEventListener('mouseenter', function() {{
                    this.style.transform = 'translateY(-4px)';
                }});
                
                card.addEventListener('mouseleave', function() {{
                    this.style.transform = 'translateY(0)';
                }});
            }});
        }});
    </script>
</body>
</html>'''

    return html_content

def generate_all_terminal_pages():
    """모든 터미널 페이지를 생성합니다."""
    
    # 노선 데이터 로드
    routes = load_route_data()
    grouped_routes = group_routes_by_departure(routes)
    
    if not routes:
        print("❌ 노선 데이터가 없습니다.")
        return
    
    # outputs 폴더 생성
    os.makedirs('outputs', exist_ok=True)
    
    generated_count = 0
    
    # 각 터미널별로 페이지 생성
    for terminal_name, destinations in grouped_routes.items():
        # HTML 생성
        html_content = generate_terminal_page(terminal_name, destinations)
        
        # 파일명 생성
        filename = f"{terminal_name}-터미널-시외버스-시간표.html"
        output_file = f"outputs/{filename}"
        
        # 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        generated_count += 1
        print(f"✅ {terminal_name} 터미널 페이지 생성 완료 ({len(destinations)}개 노선)")
    
    print(f"🎉 총 {generated_count}개 터미널 페이지 생성 완료!")

if __name__ == "__main__":
    print("🚀 터미널 페이지 생성 시작...")
    
    try:
        generate_all_terminal_pages()
        print("🎉 모든 터미널 페이지 생성 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        exit(1)