import os
import glob
from datetime import datetime
from urllib.parse import quote

def generate_sitemap():
    """sitemap.xml 파일을 생성합니다."""
    base_url = "https://hyunwoo0815.github.io/bus2/"
    
    # XML 헤더
    sitemap_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'''
    
    # outputs 폴더의 모든 HTML 파일 찾기
    html_files = glob.glob('outputs/*.html')
    
    # 각 HTML 파일에 대한 URL 추가
    for html_file in sorted(html_files):
        filename = os.path.basename(html_file)
        
        # index.html은 제외 (필요에 따라 수정 가능)
        if filename == 'index.html':
            continue
            
        # URL 인코딩 (한글 파일명 처리)
        encoded_filename = quote(filename, safe='-._~')
        url = base_url + encoded_filename
        lastmod = datetime.now().strftime('%Y-%m-%d')
        
        sitemap_content += f'''
    <url>
        <loc>{url}</loc>
        <lastmod>{lastmod}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>'''
    
    # XML 푸터
    sitemap_content += '''
</urlset>'''
    
    # sitemap.xml 파일 저장
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap_content)
    
    print(f"✅ Sitemap 생성 완료: {len(html_files)}개 페이지")

def generate_rss():
    """rss.xml 파일을 생성합니다."""
    base_url = "https://hyunwoo0815.github.io/bus2/"
    
    # 현재 시간
    build_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # RSS 헤더
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>전국 시외버스 시간표</title>
        <description>전국 시외버스 노선별 시간표 정보를 제공합니다</description>
        <link>{base_url}</link>
        <atom:link href="{base_url}rss.xml" rel="self" type="application/rss+xml"/>
        <language>ko-kr</language>
        <lastBuildDate>{build_date}</lastBuildDate>
        <pubDate>{build_date}</pubDate>
        <ttl>1440</ttl>'''
    
    # outputs 폴더의 HTML 파일들 찾기
    html_files = glob.glob('outputs/*.html')
    
    # 최근 파일들을 RSS 아이템으로 추가 (최대 20개)
    recent_files = sorted(html_files, key=os.path.getmtime, reverse=True)[:20]
    
    for html_file in recent_files:
        filename = os.path.basename(html_file)
        
        # index.html은 제외
        if filename == 'index.html':
            continue
            
        # 파일명에서 노선 정보 추출
        route_info = filename.replace('-시외버스-시간표.html', '').replace('-', ' → ')
        
        # URL 인코딩
        encoded_filename = quote(filename, safe='-._~')
        url = base_url + encoded_filename
        
        # 파일 수정 시간
        mtime = os.path.getmtime(html_file)
        pub_date = datetime.fromtimestamp(mtime).strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        rss_content += f'''
        <item>
            <title>{route_info} 시외버스 시간표</title>
            <description>{route_info} 노선의 시외버스 시간표 정보입니다.</description>
            <link>{url}</link>
            <guid>{url}</guid>
            <pubDate>{pub_date}</pubDate>
        </item>'''
    
    # RSS 푸터
    rss_content += '''
    </channel>
</rss>'''
    
    # rss.xml 파일 저장
    with open('outputs/rss.xml', 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    print(f"✅ RSS 생성 완료: {len(recent_files)}개 항목")

def generate_robots_txt():
    """robots.txt 파일을 생성합니다."""
    base_url = "https://hyunwoo0815.github.io/bus2/"
    
    robots_content = f'''User-agent: *
Allow: /

# Sitemap
Sitemap: {base_url}sitemap.xml

# 크롤링 지연 (1초)
Crawl-delay: 1'''
    
    with open('outputs/robots.txt', 'w', encoding='utf-8') as f:
        f.write(robots_content)
    
    print("✅ robots.txt 생성 완료")

if __name__ == "__main__":
    print("🚀 SEO 파일 생성 시작...")
    
    # outputs 폴더가 있는지 확인
    if not os.path.exists('outputs'):
        print("❌ outputs 폴더가 없습니다. app.py를 먼저 실행해주세요.")
        exit(1)
    
    # HTML 파일이 있는지 확인
    html_files = glob.glob('outputs/*.html')
    if not html_files:
        print("❌ HTML 파일이 없습니다. app.py를 먼저 실행해주세요.")
        exit(1)
    
    try:
        generate_sitemap()
        generate_rss()
        generate_robots_txt()
        print("🎉 모든 SEO 파일 생성 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        exit(1)