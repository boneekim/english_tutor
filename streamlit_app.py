#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import json
import base64
import tempfile
import os
from datetime import datetime
import hashlib
import requests

# 페이지 설정
st.set_page_config(
    page_title="🎯 영어튜터",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 카테고리 정보
CATEGORIES = {
    'general': {'name': '📚 일반', 'emoji': '📚'},
    'greeting': {'name': '👋 인사', 'emoji': '👋'},
    'mealtime': {'name': '🍽️ 식사시간', 'emoji': '🍽️'},
    'bedtime': {'name': '😴 잠자리', 'emoji': '😴'},
    'playing': {'name': '🎮 놀이시간', 'emoji': '🎮'},
    'study': {'name': '📖 공부시간', 'emoji': '📖'},
    'outside': {'name': '🚶 외출', 'emoji': '🚶'},
    'emotion': {'name': '💝 감정표현', 'emoji': '💝'},
    'question': {'name': '❓ 질문', 'emoji': '❓'},
    'daily': {'name': '🏠 일상', 'emoji': '🏠'}
}

# 세션 상태 초기화
def initialize_session_state():
    if "sentences" not in st.session_state:
        st.session_state.sentences = []
    if "current_category" not in st.session_state:
        st.session_state.current_category = "all"
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""

# CSS 스타일 적용
def apply_custom_css():
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-top: -1rem;
    }
    
    .sentence-item {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .sentence-item:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .sentence-english {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .sentence-korean {
        font-size: 1rem;
        color: #7f8c8d;
        margin-bottom: 1rem;
    }
    
    .category-badge {
        display: inline-block;
        background: #3498db;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin-bottom: 0.5rem;
    }
    
    .stats-container {
        display: flex;
        justify-content: space-around;
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #3498db;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #7f8c8d;
    }
    
    .audio-controls {
        margin-top: 1rem;
        text-align: center;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: #7f8c8d;
    }
    
    .empty-state h3 {
        color: #95a5a6;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 텍스트를 음성으로 변환 (브라우저의 Web Speech API 사용)
def create_audio_html(text, key):
    """브라우저의 Web Speech API를 사용한 TTS"""
    audio_html = f"""
    <div class="audio-controls">
        <button onclick="speakText('{text.replace("'", "&#39;")}')" 
                style="background: #3498db; color: white; border: none; padding: 0.5rem 1rem; 
                       border-radius: 5px; cursor: pointer; font-size: 0.9rem;">
            🔊 음성 재생
        </button>
    </div>
    
    <script>
    function speakText(text) {{
        if ('speechSynthesis' in window) {{
            // 기존 음성 중지
            speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US';
            utterance.rate = 0.9;
            utterance.pitch = 1.0;
            
            // 영어 음성 찾기
            const voices = speechSynthesis.getVoices();
            const englishVoice = voices.find(voice => 
                voice.lang.startsWith('en') && voice.localService === false
            ) || voices.find(voice => voice.lang.startsWith('en'));
            
            if (englishVoice) {{
                utterance.voice = englishVoice;
            }}
            
            speechSynthesis.speak(utterance);
        }} else {{
            alert('죄송합니다. 이 브라우저는 음성 합성을 지원하지 않습니다.');
        }}
    }}
    
    // 음성 목록 로딩
    if ('speechSynthesis' in window) {{
        speechSynthesis.onvoiceschanged = function() {{
            // 음성 목록이 로드되면 업데이트
        }};
    }}
    </script>
    """
    return audio_html

# 문장 추가 함수
def add_sentence(english, korean, category):
    if english.strip() and korean.strip():
        new_sentence = {
            "id": len(st.session_state.sentences) + 1,
            "english": english.strip(),
            "korean": korean.strip(),
            "category": category,
            "created_at": datetime.now().isoformat()
        }
        st.session_state.sentences.insert(0, new_sentence)  # 최신 문장을 맨 위에 추가
        return True
    return False

# 문장 삭제 함수
def delete_sentence(sentence_id):
    st.session_state.sentences = [s for s in st.session_state.sentences if s["id"] != sentence_id]

# 필터링된 문장 목록 가져오기
def get_filtered_sentences():
    sentences = st.session_state.sentences
    
    # 카테고리 필터링
    if st.session_state.current_category != "all":
        sentences = [s for s in sentences if s.get("category", "general") == st.session_state.current_category]
    
    # 검색 필터링
    if st.session_state.search_query:
        query = st.session_state.search_query.lower()
        sentences = [s for s in sentences if 
                    query in s["english"].lower() or query in s["korean"].lower()]
    
    return sentences

# 카테고리별 통계
def get_category_stats():
    stats = {"all": len(st.session_state.sentences)}
    for category in CATEGORIES.keys():
        stats[category] = len([s for s in st.session_state.sentences 
                              if s.get("category", "general") == category])
    return stats

# 메인 앱
def main():
    initialize_session_state()
    apply_custom_css()
    
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🎯 영어튜터</h1>
        <p>아이와 함께하는 일상 영어 학습</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 사이드바 - 설정 및 통계
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        
        # 데이터 관리
        st.markdown("#### 📊 데이터 관리")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 데이터 내보내기", use_container_width=True):
                if st.session_state.sentences:
                    json_data = json.dumps(st.session_state.sentences, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="💾 JSON 파일 다운로드",
                        data=json_data,
                        file_name=f"english_tutor_sentences_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                else:
                    st.warning("내보낼 데이터가 없습니다.")
        
        with col2:
            uploaded_file = st.file_uploader("📤 데이터 가져오기", type="json", key="import_data")
            if uploaded_file is not None:
                try:
                    imported_data = json.loads(uploaded_file.read().decode())
                    if isinstance(imported_data, list) and all(isinstance(item, dict) for item in imported_data):
                        st.session_state.sentences = imported_data
                        st.success(f"{len(imported_data)}개 문장을 가져왔습니다!")
                        st.rerun()
                    else:
                        st.error("올바른 JSON 형식이 아닙니다.")
                except json.JSONDecodeError:
                    st.error("JSON 파일을 읽을 수 없습니다.")
        
        # 통계
        st.markdown("#### 📈 통계")
        stats = get_category_stats()
        
        st.markdown(f"""
        <div class="stats-container">
            <div class="stat-item">
                <div class="stat-number">{stats['all']}</div>
                <div class="stat-label">전체 문장</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 카테고리별 통계
        for category, info in CATEGORIES.items():
            if stats[category] > 0:
                st.markdown(f"{info['emoji']} {info['name']}: **{stats[category]}**개")
        
        # 전체 삭제
        st.markdown("#### 🗑️ 전체 삭제")
        if st.button("🚨 모든 문장 삭제", type="secondary", use_container_width=True):
            if st.session_state.sentences:
                st.session_state.sentences = []
                st.success("모든 문장이 삭제되었습니다.")
                st.rerun()
            else:
                st.warning("삭제할 문장이 없습니다.")
    
    # 메인 컨텐츠
    # 문장 추가 섹션
    st.markdown("### 📝 새 문장 추가")
    
    col1, col2, col3, col4 = st.columns([2, 3, 3, 1])
    
    with col1:
        category = st.selectbox(
            "카테고리",
            options=list(CATEGORIES.keys()),
            format_func=lambda x: CATEGORIES[x]["name"],
            key="add_category"
        )
    
    with col2:
        english = st.text_input("영어 문장", placeholder="영어 문장을 입력하세요", key="add_english")
    
    with col3:
        korean = st.text_input("한국어 뜻", placeholder="한국어 뜻을 입력하세요", key="add_korean")
    
    with col4:
        if st.button("➕ 추가", type="primary", use_container_width=True):
            if add_sentence(english, korean, category):
                st.success(f"{CATEGORIES[category]['name']}에 문장이 추가되었습니다! 🎉")
                st.rerun()
            else:
                st.error("영어 문장과 한국어 뜻을 모두 입력해주세요.")
    
    # 검색 및 필터링
    st.markdown("### 📚 등록된 문장들")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        search_query = st.text_input("🔍 검색", placeholder="영어 또는 한국어로 검색...", key="search_input")
        if search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
            st.rerun()
    
    with col2:
        category_options = ["all"] + list(CATEGORIES.keys())
        category_labels = ["🌟 전체"] + [CATEGORIES[cat]["name"] for cat in CATEGORIES.keys()]
        
        selected_category = st.selectbox(
            "카테고리 필터",
            options=category_options,
            format_func=lambda x: "🌟 전체" if x == "all" else CATEGORIES[x]["name"],
            index=category_options.index(st.session_state.current_category),
            key="filter_category"
        )
        
        if selected_category != st.session_state.current_category:
            st.session_state.current_category = selected_category
            st.rerun()
    
    # 문장 목록 표시
    filtered_sentences = get_filtered_sentences()
    
    if not st.session_state.sentences:
        st.markdown("""
        <div class="empty-state">
            <h3>📝 등록된 문장이 없습니다</h3>
            <p>위에서 영어 문장과 한국어 뜻을 입력하여<br>첫 번째 문장을 추가해보세요!</p>
        </div>
        """, unsafe_allow_html=True)
    
    elif not filtered_sentences:
        filter_info = f"검색어: '{st.session_state.search_query}'" if st.session_state.search_query else f"카테고리: {CATEGORIES.get(st.session_state.current_category, {'name': '전체'})['name']}"
        st.markdown(f"""
        <div class="empty-state">
            <h3>🔍 검색 결과가 없습니다</h3>
            <p>{filter_info}에 해당하는 문장을 찾을 수 없습니다</p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # 전체 재생 버튼
        if len(filtered_sentences) > 1:
            st.markdown("### 🎵 전체 재생")
            
            all_text = " ... ".join([sentence["english"] for sentence in filtered_sentences])
            
            st.markdown(f"""
            <div class="audio-controls">
                <button onclick="speakText('{all_text.replace("'", "&#39;")}')" 
                        style="background: #27ae60; color: white; border: none; padding: 0.8rem 2rem; 
                               border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: bold;">
                    🎵 전체 {len(filtered_sentences)}개 문장 재생
                </button>
            </div>
            
            <script>
            function speakText(text) {{
                if ('speechSynthesis' in window) {{
                    speechSynthesis.cancel();
                    
                    const sentences = text.split(' ... ');
                    let currentIndex = 0;
                    
                    function speakNext() {{
                        if (currentIndex < sentences.length) {{
                            const utterance = new SpeechSynthesisUtterance(sentences[currentIndex]);
                            utterance.lang = 'en-US';
                            utterance.rate = 0.9;
                            utterance.pitch = 1.0;
                            
                            const voices = speechSynthesis.getVoices();
                            const englishVoice = voices.find(voice => 
                                voice.lang.startsWith('en') && voice.localService === false
                            ) || voices.find(voice => voice.lang.startsWith('en'));
                            
                            if (englishVoice) {{
                                utterance.voice = englishVoice;
                            }}
                            
                            utterance.onend = function() {{
                                currentIndex++;
                                setTimeout(speakNext, 1000); // 1초 간격
                            }};
                            
                            speechSynthesis.speak(utterance);
                        }}
                    }}
                    
                    speakNext();
                }} else {{
                    alert('죄송합니다. 이 브라우저는 음성 합성을 지원하지 않습니다.');
                }}
            }}
            </script>
            """, unsafe_allow_html=True)
        
        # 문장 목록
        st.markdown(f"**총 {len(filtered_sentences)}개 문장**")
        
        for i, sentence in enumerate(filtered_sentences):
            category_info = CATEGORIES.get(sentence.get("category", "general"), {"name": "📚 일반", "emoji": "📚"})
            
            with st.container():
                st.markdown(f"""
                <div class="sentence-item">
                    <div class="category-badge">{category_info['emoji']} {category_info['name']}</div>
                    <div class="sentence-english">{sentence['english']}</div>
                    <div class="sentence-korean">{sentence['korean']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # 음성 재생 버튼
                    st.markdown(create_audio_html(sentence["english"], f"audio_{sentence['id']}"), unsafe_allow_html=True)
                
                with col2:
                    # 삭제 버튼
                    if st.button("🗑️", key=f"delete_{sentence['id']}", help="문장 삭제"):
                        delete_sentence(sentence["id"])
                        st.success("문장이 삭제되었습니다.")
                        st.rerun()
                
                st.markdown("---")

if __name__ == "__main__":
    main() 