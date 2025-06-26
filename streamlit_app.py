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

# 로컬 스토리지 JavaScript 코드 추가
def add_local_storage_js():
    st.markdown("""
    <script>
    // 로컬 스토리지에 데이터 저장
    function saveToLocalStorage(data) {
        try {
            localStorage.setItem('english_tutor_sentences', JSON.stringify(data));
            console.log('데이터 저장됨:', data.length, '개 문장');
        } catch (e) {
            console.error('로컬 스토리지 저장 실패:', e);
        }
    }
    
    // 로컬 스토리지에서 데이터 로드
    function loadFromLocalStorage() {
        try {
            const data = localStorage.getItem('english_tutor_sentences');
            if (data) {
                const sentences = JSON.parse(data);
                console.log('데이터 로드됨:', sentences.length, '개 문장');
                return sentences;
            }
        } catch (e) {
            console.error('로컬 스토리지 로드 실패:', e);
        }
        return [];
    }
    
    // Streamlit과 로컬 스토리지 동기화
    function syncWithStreamlit() {
        const savedData = loadFromLocalStorage();
        if (savedData.length > 0) {
            // 페이지 로드 시 Streamlit에 저장된 데이터 전달
            window.parent.postMessage({
                type: 'LOAD_SENTENCES',
                sentences: savedData
            }, '*');
        }
    }
    
    // 페이지 로드 시 동기화 실행
    document.addEventListener('DOMContentLoaded', syncWithStreamlit);
    </script>
    """, unsafe_allow_html=True)

# 세션 상태 초기화
def initialize_session_state():
    if "sentences" not in st.session_state:
        st.session_state.sentences = []
    if "current_category" not in st.session_state:
        st.session_state.current_category = "all"
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    if "sentences_loaded" not in st.session_state:
        st.session_state.sentences_loaded = False

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
        position: relative;
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
    
    .sentence-buttons {
        display: flex;
        gap: 0.5rem;
        justify-content: flex-start;
        align-items: center;
        margin-top: 1rem;
    }
    
    .play-button {
        background: #3498db;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: background-color 0.3s ease;
    }
    
    .play-button:hover {
        background: #2980b9;
    }
    
    .delete-column .stButton > button {
        background: #e74c3c !important;
        color: white !important;
        border: none !important;
        padding: 0.3rem 0.5rem !important;
        border-radius: 50% !important;
        cursor: pointer !important;
        font-size: 0.8rem !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.3s ease !important;
        margin: 0 !important;
        min-height: 32px !important;
    }
    
    .delete-column .stButton > button:hover {
        background: #c0392b !important;
        transform: scale(1.1) !important;
        border: none !important;
    }
    
    .delete-column .stButton > button:focus:not(:active) {
        border: none !important;
        box-shadow: none !important;
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
        save_to_storage()  # 로컬 스토리지에 저장
        return True
    return False

# 문장 삭제 함수
def delete_sentence(sentence_id):
    st.session_state.sentences = [s for s in st.session_state.sentences if s["id"] != sentence_id]
    save_to_storage()  # 로컬 스토리지에 저장

# 로컬 스토리지 저장 함수
def save_to_storage():
    # JavaScript를 통해 로컬 스토리지에 저장
    sentences_json = json.dumps(st.session_state.sentences, ensure_ascii=False)
    st.markdown(f"""
    <script>
    try {{
        localStorage.setItem('english_tutor_sentences', '{sentences_json.replace("'", "\\'")}');
        console.log('문장 저장됨: {len(st.session_state.sentences)}개');
    }} catch (e) {{
        console.error('저장 실패:', e);
    }}
    </script>
    """, unsafe_allow_html=True)

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

# 로컬 스토리지에서 데이터 로드
def load_from_local_storage():
    st.markdown("""
    <script>
    // 페이지 로드 시 로컬 스토리지에서 데이터 로드
    document.addEventListener('DOMContentLoaded', function() {
        try {
            const savedData = localStorage.getItem('english_tutor_sentences');
            if (savedData) {
                const sentences = JSON.parse(savedData);
                console.log('로컬 스토리지에서 로드된 문장:', sentences.length, '개');
                
                // Streamlit에 데이터 전달 (URL 파라미터 사용)
                if (sentences.length > 0 && !window.location.search.includes('loaded=true')) {
                    const url = new URL(window.location);
                    url.searchParams.set('loaded', 'true');
                    url.searchParams.set('sentences', btoa(encodeURIComponent(JSON.stringify(sentences))));
                    window.location.href = url.toString();
                }
            }
        } catch (e) {
            console.error('로컬 스토리지 로드 오류:', e);
        }
    });
    </script>
    """, unsafe_allow_html=True)

# URL 파라미터에서 문장 데이터 로드
def load_sentences_from_url():
    query_params = st.query_params
    if 'sentences' in query_params and not st.session_state.sentences_loaded:
        try:
            import base64
            encoded_data = query_params['sentences']
            decoded_data = base64.b64decode(encoded_data.encode()).decode()
            sentences_data = json.loads(decoded_data)
            st.session_state.sentences = sentences_data
            st.session_state.sentences_loaded = True
            st.success(f"💾 저장된 {len(sentences_data)}개 문장을 불러왔습니다!")
        except Exception as e:
            st.error(f"데이터 로드 오류: {e}")

# 메인 앱
def main():
    initialize_session_state()
    apply_custom_css()
    add_local_storage_js()
    load_from_local_storage()
    load_sentences_from_url()
    
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
                <button onclick="speakAllText()" 
                        style="background: #27ae60; color: white; border: none; padding: 0.8rem 2rem; 
                               border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: bold;">
                    🎵 전체 {len(filtered_sentences)}개 문장 재생
                </button>
            </div>
            
            <script>
            const allSentences = {json.dumps([s["english"] for s in filtered_sentences], ensure_ascii=False)};
            
            function speakAllText() {{
                console.log('전체 재생 시작, 문장 수:', allSentences.length);
                
                if (!('speechSynthesis' in window)) {{
                    alert('죄송합니다. 이 브라우저는 음성 합성을 지원하지 않습니다.');
                    return;
                }}
                
                speechSynthesis.cancel();
                let currentIndex = 0;
                
                function prepareAndSpeakNext() {{
                    if (currentIndex >= allSentences.length) {{
                        console.log('전체 재생 완료');
                        return;
                    }}
                    
                    const text = allSentences[currentIndex];
                    console.log(`재생 중 (${currentIndex + 1}/${allSentences.length}):`, text);
                    
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.lang = 'en-US';
                    utterance.rate = 0.8;
                    utterance.pitch = 1.0;
                    utterance.volume = 1.0;
                    
                    const voices = speechSynthesis.getVoices();
                    let selectedVoice = voices.find(voice => 
                        voice.lang.includes('en') && 
                        (voice.name.includes('Google') || voice.name.includes('Microsoft') || !voice.localService)
                    );
                    
                    if (!selectedVoice) {{
                        selectedVoice = voices.find(voice => voice.lang.includes('en'));
                    }}
                    
                    if (selectedVoice) {{
                        utterance.voice = selectedVoice;
                    }}
                    
                    utterance.onend = function() {{
                        console.log(`문장 ${currentIndex + 1} 재생 완료`);
                        currentIndex++;
                        setTimeout(prepareAndSpeakNext, 1000); // 1초 간격
                    }};
                    
                    utterance.onerror = function(event) {{
                        console.error(`문장 ${currentIndex + 1} 재생 오류:`, event.error);
                        currentIndex++;
                        setTimeout(prepareAndSpeakNext, 1000);
                    }};
                    
                    try {{
                        speechSynthesis.speak(utterance);
                    }} catch (error) {{
                        console.error('음성 재생 예외:', error);
                        currentIndex++;
                        setTimeout(prepareAndSpeakNext, 1000);
                    }}
                }}
                
                // 음성 엔진 준비 확인 후 시작
                if (speechSynthesis.getVoices().length === 0) {{
                    speechSynthesis.onvoiceschanged = function() {{
                        prepareAndSpeakNext();
                        speechSynthesis.onvoiceschanged = null;
                    }};
                    setTimeout(() => {{
                        if (speechSynthesis.onvoiceschanged) {{
                            speechSynthesis.onvoiceschanged = null;
                            prepareAndSpeakNext();
                        }}
                    }}, 3000);
                }} else {{
                    prepareAndSpeakNext();
                }}
            }}
            </script>
            """, unsafe_allow_html=True)
        
        # 문장 목록
        st.markdown(f"**총 {len(filtered_sentences)}개 문장**")
        
        for i, sentence in enumerate(filtered_sentences):
            category_info = CATEGORIES.get(sentence.get("category", "general"), {"name": "📚 일반", "emoji": "📚"})
            
            with st.container():
                # 문장 카드와 버튼을 모두 포함한 HTML
                col1, col2 = st.columns([10, 1])
                
                # 문장 카드를 두 개의 컬럼으로 나누기
                card_col, delete_col = st.columns([9, 1])
                
                with card_col:
                    escaped_text = sentence['english'].replace("'", "&#39;").replace('"', '&quot;').replace('\\', '\\\\')
                    
                    # 문장 카드 표시
                    st.markdown(f"""
                    <div class="sentence-item" style="position: relative;">
                        <div class="category-badge">{category_info['emoji']} {category_info['name']}</div>
                        <div class="sentence-english">{sentence['english']}</div>
                        <div class="sentence-korean">{sentence['korean']}</div>
                        <div class="sentence-buttons">
                            <button class="play-button" onclick="speakText_{sentence['id']}('{escaped_text}')">
                                🔊 음성 재생
                            </button>
                        </div>
                    </div>
                    
                    <script>
                    function speakText_{sentence['id']}(text) {{
                        console.log('음성 재생 시도:', text);
                        
                        if (!('speechSynthesis' in window)) {{
                            alert('죄송합니다. 이 브라우저는 음성 합성을 지원하지 않습니다.');
                            return;
                        }}
                        
                        // 기존 음성 중지
                        speechSynthesis.cancel();
                        
                        // 음성 준비 함수
                        function prepareAndSpeak() {{
                            const utterance = new SpeechSynthesisUtterance(text);
                            utterance.lang = 'en-US';
                            utterance.rate = 0.8;
                            utterance.pitch = 1.0;
                            utterance.volume = 1.0;
                            
                            const voices = speechSynthesis.getVoices();
                            console.log('사용 가능한 음성:', voices.length);
                            
                            // 영어 음성 찾기 (우선순위: 온라인 → 로컬)
                            let selectedVoice = voices.find(voice => 
                                voice.lang.includes('en') && 
                                (voice.name.includes('Google') || voice.name.includes('Microsoft') || !voice.localService)
                            );
                            
                            if (!selectedVoice) {{
                                selectedVoice = voices.find(voice => voice.lang.includes('en'));
                            }}
                            
                            if (selectedVoice) {{
                                utterance.voice = selectedVoice;
                                console.log('선택된 음성:', selectedVoice.name);
                            }} else {{
                                console.log('영어 음성을 찾을 수 없음, 기본 음성 사용');
                            }}
                            
                            utterance.onstart = function() {{
                                console.log('음성 재생 시작됨');
                            }};
                            
                            utterance.onend = function() {{
                                console.log('음성 재생 완료됨');
                            }};
                            
                            utterance.onerror = function(event) {{
                                console.error('음성 재생 오류:', event.error);
                                alert('음성 재생 중 오류가 발생했습니다: ' + event.error);
                            }};
                            
                            try {{
                                speechSynthesis.speak(utterance);
                                console.log('음성 재생 명령 실행됨');
                            }} catch (error) {{
                                console.error('음성 재생 예외:', error);
                                alert('음성 재생을 시작할 수 없습니다.');
                            }}
                        }}
                        
                        // 음성 엔진이 준비될 때까지 대기
                        if (speechSynthesis.getVoices().length === 0) {{
                            console.log('음성 목록 로딩 대기 중...');
                            speechSynthesis.onvoiceschanged = function() {{
                                console.log('음성 목록 로드 완료');
                                prepareAndSpeak();
                                speechSynthesis.onvoiceschanged = null; // 이벤트 리스너 제거
                            }};
                            // 타임아웃 설정 (3초 후 강제 실행)
                            setTimeout(() => {{
                                if (speechSynthesis.onvoiceschanged) {{
                                    console.log('음성 로딩 타임아웃, 강제 실행');
                                    speechSynthesis.onvoiceschanged = null;
                                    prepareAndSpeak();
                                }}
                            }}, 3000);
                        }} else {{
                            prepareAndSpeak();
                        }}
                    }}
                    </script>
                    """, unsafe_allow_html=True)
                
                with delete_col:
                    # 삭제 버튼을 위한 HTML 컨테이너
                    st.markdown('<div class="delete-column">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"delete_{sentence['id']}", help="문장 삭제"):
                        delete_sentence(sentence["id"])
                        st.success("문장이 삭제되었습니다.")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("---")

if __name__ == "__main__":
    main() 