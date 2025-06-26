// 전역 변수
let sentences = [];
let currentSpeechSettings = {
    rate: 1.0,
    pitch: 1.0,
    lang: 'en-US',
    voice: null
};
let availableVoices = [];
// 고정 API 키 (Gemini API)
const FIXED_API_KEY = 'AIzaSyBXVCdF8sWsFocpJx1Cs4YK4eSlwgij2O0';
let currentCategory = 'all';
let searchQuery = '';

// 카테고리 정보
const categories = {
    'general': { name: '📚 일반', emoji: '📚' },
    'greeting': { name: '👋 인사', emoji: '👋' },
    'mealtime': { name: '🍽️ 식사시간', emoji: '🍽️' },
    'bedtime': { name: '😴 잠자리', emoji: '😴' },
    'playing': { name: '🎮 놀이시간', emoji: '🎮' },
    'study': { name: '📖 공부시간', emoji: '📖' },
    'outside': { name: '🚶 외출', emoji: '🚶' },
    'emotion': { name: '💝 감정표현', emoji: '💝' },
    'question': { name: '❓ 질문', emoji: '❓' },
    'daily': { name: '🏠 일상', emoji: '🏠' }
};

// DOM 요소들
const englishInput = document.getElementById('englishInput');
const koreanInput = document.getElementById('koreanInput');
const categorySelect = document.getElementById('categorySelect');
const addBtn = document.getElementById('addBtn');
const playAllBtn = document.getElementById('playAllBtn');
const clearAllBtn = document.getElementById('clearAllBtn');
const sentencesList = document.getElementById('sentencesList');
const speedRange = document.getElementById('speedRange');
const speedValue = document.getElementById('speedValue');
const pitchRange = document.getElementById('pitchRange');
const pitchValue = document.getElementById('pitchValue');
const voiceSelect = document.getElementById('voiceSelect');
const testVoiceBtn = document.getElementById('testVoiceBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearchBtn');
const categoryTabs = document.getElementById('categoryTabs');

// 로컬 스토리지 키
const STORAGE_KEY = 'english-tutor-sentences';

// 앱 초기화
document.addEventListener('DOMContentLoaded', function() {
    loadSentencesFromStorage();
    renderSentencesList();
    updateCategoryTabs();
    initializeEventListeners();
    initializeTTSSettings();
    checkSpeechSynthesisSupport();
});

// 음성 합성 지원 확인
function checkSpeechSynthesisSupport() {
    if (!('speechSynthesis' in window)) {
        alert('죄송합니다. 이 브라우저는 음성 합성을 지원하지 않습니다.');
    }
}

// 이벤트 리스너 초기화
function initializeEventListeners() {
    // 문장 추가
    addBtn.addEventListener('click', addSentence);
    englishInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            koreanInput.focus();
        }
    });
    koreanInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addSentence();
        }
    });

    // 전체 재생 및 삭제
    playAllBtn.addEventListener('click', playAllSentences);
    clearAllBtn.addEventListener('click', clearAllSentences);

    // 검색 기능
    searchInput.addEventListener('input', handleSearch);
    clearSearchBtn.addEventListener('click', clearSearch);

    // 카테고리 탭
    categoryTabs.addEventListener('click', handleCategoryClick);

    // TTS 설정
    speedRange.addEventListener('input', updateSpeed);
    pitchRange.addEventListener('input', updatePitch);
    voiceSelect.addEventListener('change', updateVoice);
    testVoiceBtn.addEventListener('click', testVoice);
}

// TTS 설정 초기화
function initializeTTSSettings() {
    speedValue.textContent = speedRange.value;
    pitchValue.textContent = pitchRange.value;
    currentSpeechSettings.rate = parseFloat(speedRange.value);
    currentSpeechSettings.pitch = parseFloat(pitchRange.value);
    loadVoices();
}

// 로컬 스토리지에서 문장 로드
function loadSentencesFromStorage() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
        try {
            sentences = JSON.parse(stored);
        } catch (e) {
            console.error('저장된 데이터 로드 실패:', e);
            sentences = [];
        }
    }
}

// 로컬 스토리지에 문장 저장
function saveSentencesToStorage() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sentences));
}

// 문장 추가
function addSentence() {
    const english = englishInput.value.trim();
    const korean = koreanInput.value.trim();
    const category = categorySelect.value;

    if (!english) {
        alert('영어 문장을 입력해주세요.');
        englishInput.focus();
        return;
    }

    if (!korean) {
        alert('한국어 뜻을 입력해주세요.');
        koreanInput.focus();
        return;
    }

    const newSentence = {
        id: Date.now(),
        english: english,
        korean: korean,
        category: category,
        createdAt: new Date().toISOString()
    };

    sentences.unshift(newSentence); // 최신 문장을 맨 위에 추가
    saveSentencesToStorage();
    renderSentencesList();
    updateCategoryTabs();

    // 입력 필드 초기화
    englishInput.value = '';
    koreanInput.value = '';
    categorySelect.value = 'general';
    englishInput.focus();

    // 성공 메시지
    const categoryName = categories[category] ? categories[category].name : '📚 일반';
    showToast(`${categoryName}에 문장이 추가되었습니다! 🎉`);
}

// 문장 삭제
function deleteSentence(id) {
    if (confirm('이 문장을 삭제하시겠습니까?')) {
        sentences = sentences.filter(sentence => sentence.id !== id);
        saveSentencesToStorage();
        renderSentencesList();
        updateCategoryTabs();
        showToast('문장이 삭제되었습니다.');
    }
}

// 전체 문장 삭제
function clearAllSentences() {
    if (sentences.length === 0) {
        alert('삭제할 문장이 없습니다.');
        return;
    }

    if (confirm('모든 문장을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.')) {
        sentences = [];
        saveSentencesToStorage();
        renderSentencesList();
        updateCategoryTabs();
        showToast('모든 문장이 삭제되었습니다.');
    }
}

// 검색 처리
function handleSearch() {
    searchQuery = searchInput.value.trim().toLowerCase();
    
    // 검색 지우기 버튼 표시/숨기기
    if (searchQuery) {
        clearSearchBtn.classList.remove('hidden');
    } else {
        clearSearchBtn.classList.add('hidden');
    }
    
    renderSentencesList();
}

// 검색 지우기
function clearSearch() {
    searchInput.value = '';
    searchQuery = '';
    clearSearchBtn.classList.add('hidden');
    renderSentencesList();
}

// 카테고리 탭 클릭 처리
function handleCategoryClick(event) {
    if (event.target.classList.contains('tab-btn')) {
        const category = event.target.dataset.category;
        setActiveCategory(category);
    }
}

// 활성 카테고리 설정
function setActiveCategory(category) {
    currentCategory = category;
    
    // 탭 버튼 활성화 상태 업데이트
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-category="${category}"]`).classList.add('active');
    
    renderSentencesList();
}

// 필터링된 문장 목록 가져오기
function getFilteredSentences() {
    let filtered = sentences;
    
    // 카테고리 필터링
    if (currentCategory !== 'all') {
        filtered = filtered.filter(sentence => {
            const category = sentence.category || 'general';
            return category === currentCategory;
        });
    }
    
    // 검색 필터링
    if (searchQuery) {
        filtered = filtered.filter(sentence => {
            return sentence.english.toLowerCase().includes(searchQuery) ||
                   sentence.korean.toLowerCase().includes(searchQuery);
        });
    }
    
    return filtered;
}

// 카테고리 표시 이름 가져오기
function getCategoryDisplayName(category) {
    if (category === 'all') return '전체';
    return categories[category] ? categories[category].name : '📚 일반';
}

// 카테고리 탭 업데이트 (문장 수 표시)
function updateCategoryTabs() {
    const categoryCounts = {};
    
    // 각 카테고리별 문장 수 계산
    sentences.forEach(sentence => {
        const category = sentence.category || 'general';
        categoryCounts[category] = (categoryCounts[category] || 0) + 1;
    });
    
    // 탭 버튼들 업데이트
    document.querySelectorAll('.tab-btn').forEach(btn => {
        const category = btn.dataset.category;
        
        if (category === 'all') {
            // 전체 탭
            if (sentences.length > 0) {
                btn.setAttribute('data-count', sentences.length);
                btn.classList.add('has-count');
            } else {
                btn.removeAttribute('data-count');
                btn.classList.remove('has-count');
            }
        } else {
            // 개별 카테고리 탭
            const count = categoryCounts[category] || 0;
            if (count > 0) {
                btn.setAttribute('data-count', count);
                btn.classList.add('has-count');
            } else {
                btn.removeAttribute('data-count');
                btn.classList.remove('has-count');
            }
        }
    });
}

// 문장 목록 렌더링
function renderSentencesList() {
    const filteredSentences = getFilteredSentences();
    
    if (sentences.length === 0) {
        sentencesList.innerHTML = `
            <div class="empty-state">
                <h3>📝 등록된 문장이 없습니다</h3>
                <p>위에서 영어 문장과 한국어 뜻을 입력하여<br>첫 번째 문장을 추가해보세요!</p>
            </div>
        `;
        return;
    }

    if (filteredSentences.length === 0) {
        const message = searchQuery ? 
            `"${searchQuery}"에 해당하는 문장을 찾을 수 없습니다` :
            `${getCategoryDisplayName(currentCategory)}에 등록된 문장이 없습니다`;
        
        sentencesList.innerHTML = `
            <div class="empty-state">
                <h3>🔍 검색 결과가 없습니다</h3>
                <p>${message}</p>
            </div>
        `;
        return;
    }

    sentencesList.innerHTML = filteredSentences.map(sentence => {
        // 기존 문장에 카테고리가 없는 경우 'general'로 처리
        const category = sentence.category || 'general';
        const categoryInfo = categories[category] || { emoji: '📚', name: '일반' };
        
        return `
            <div class="sentence-item" data-id="${sentence.id}" data-category="${category}">
                <div class="sentence-category">${categoryInfo.emoji}</div>
                <div class="sentence-english">${escapeHtml(sentence.english)}</div>
                <div class="sentence-korean">${escapeHtml(sentence.korean)}</div>
                <div class="sentence-actions">
                    <button class="btn-small btn-play" onclick="speakSentence('${escapeHtml(sentence.english)}')">
                        🔊 재생
                    </button>
                    <button class="btn-small btn-delete" onclick="deleteSentence(${sentence.id})">
                        🗑️ 삭제
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// HTML 이스케이프 처리
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// 문장 음성 재생
async function speakSentence(text) {
    try {
        // 먼저 Gemini API를 통한 TTS 시도
        const success = await speakWithGemini(text);
        if (!success) {
            // Gemini 실패시 브라우저 TTS 사용
            await speakWithBrowser(text);
        }
    } catch (error) {
        console.error('음성 재생 오류:', error);
        // 오류 발생시 브라우저 TTS 사용
        await speakWithBrowser(text);
    }
}

// Gemini API를 통한 음성 재생
async function speakWithGemini(text) {
    try {
        showLoadingOverlay();
        
        const response = await fetch('/api/gemini-tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Gemini API 성공 (실제로는 브라우저 TTS 사용)
            hideLoadingOverlay();
            showLoadingOverlay(); // 브라우저 TTS용 로딩 표시
            return await speakWithBrowser(text);
        } else {
            // Gemini API 실패
            console.log('Gemini API 사용 불가:', data.message || data.error);
            hideLoadingOverlay();
            return false;
        }
    } catch (error) {
        console.error('Gemini API 호출 오류:', error);
        hideLoadingOverlay();
        return false;
    }
}

// 브라우저 음성으로 재생
function speakWithBrowser(text) {
    // 현재 재생 중인 음성 중지
    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = currentSpeechSettings.lang;
    utterance.rate = currentSpeechSettings.rate;
    utterance.pitch = currentSpeechSettings.pitch;
    
    // 선택된 음성 적용
    if (currentSpeechSettings.voice) {
        utterance.voice = currentSpeechSettings.voice;
    }

    // 음성 재생 시작
    utterance.onstart = function() {
        showLoadingOverlay();
    };

    // 음성 재생 완료
    utterance.onend = function() {
        hideLoadingOverlay();
    };

    // 음성 재생 오류
    utterance.onerror = function(event) {
        hideLoadingOverlay();
        console.error('브라우저 음성 재생 오류:', event);
        showToast('음성 재생 중 오류가 발생했습니다.');
    };

    speechSynthesis.speak(utterance);
}

// 전체 문장 재생
async function playAllSentences() {
    const filteredSentences = getFilteredSentences();
    
    if (filteredSentences.length === 0) {
        alert('재생할 문장이 없습니다.');
        return;
    }

    const categoryName = getCategoryDisplayName(currentCategory);
    const searchInfo = searchQuery ? ` (검색: "${searchQuery}")` : '';
    const message = `${categoryName}${searchInfo}의 ${filteredSentences.length}개 문장을 순서대로 재생하시겠습니까?`;

    if (confirm(message)) {
        showLoadingOverlay();
        
        for (let i = 0; i < filteredSentences.length; i++) {
            const sentence = filteredSentences[i];
            await speakSentenceAsync(sentence.english);
            
            // 각 문장 사이에 1초 간격
            if (i < filteredSentences.length - 1) {
                await delay(1000);
            }
        }
        
        hideLoadingOverlay();
        showToast(`${filteredSentences.length}개 문장 재생이 완료되었습니다! 🎉`);
    }
}

// 비동기 음성 재생
async function speakSentenceAsync(text) {
    try {
        // 먼저 Gemini API를 통한 TTS 시도
        const success = await speakWithGeminiAsync(text);
        if (!success) {
            // Gemini 실패시 브라우저 TTS 사용
            return await speakWithBrowserAsync(text);
        }
        return true;
    } catch (error) {
        console.error('비동기 음성 재생 오류:', error);
        // 오류 발생시 브라우저 TTS 사용
        return await speakWithBrowserAsync(text);
    }
}

// Gemini API를 통한 비동기 음성 재생
async function speakWithGeminiAsync(text) {
    try {
        const response = await fetch('/api/gemini-tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Gemini API 성공 (실제로는 브라우저 TTS 사용)
            return await speakWithBrowserAsync(text);
        } else {
            // Gemini API 실패
            console.log('Gemini API 사용 불가 (비동기):', data.message || data.error);
            return false;
        }
    } catch (error) {
        console.error('Gemini API 비동기 호출 오류:', error);
        return false;
    }
}

// 브라우저 음성 비동기 재생
function speakWithBrowserAsync(text) {
    return new Promise((resolve, reject) => {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = currentSpeechSettings.lang;
        utterance.rate = currentSpeechSettings.rate;
        utterance.pitch = currentSpeechSettings.pitch;
        
        // 선택된 음성 적용
        if (currentSpeechSettings.voice) {
            utterance.voice = currentSpeechSettings.voice;
        }

        utterance.onend = function() {
            resolve();
        };

        utterance.onerror = function(event) {
            console.error('브라우저 음성 재생 오류:', event);
            reject(event);
        };

        speechSynthesis.speak(utterance);
    });
}

// 지연 함수
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 음성 목록 로드
function loadVoices() {
    // 음성 목록이 로드될 때까지 기다림
    function getVoices() {
        availableVoices = speechSynthesis.getVoices();
        
        if (availableVoices.length === 0) {
            // 음성이 아직 로드되지 않았으면 잠시 후 다시 시도
            setTimeout(getVoices, 100);
            return;
        }
        
        populateVoiceSelect();
    }
    
    // 음성 목록 변경 이벤트 리스너
    speechSynthesis.onvoiceschanged = getVoices;
    getVoices();
}

// 음성 선택 드롭다운 채우기
function populateVoiceSelect() {
    voiceSelect.innerHTML = '';
    
    // 기본 옵션
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = '🔊 기본 음성';
    voiceSelect.appendChild(defaultOption);
    
    // 영어 음성만 필터링하고 카테고리별로 분류
    const englishVoices = availableVoices.filter(voice => 
        voice.lang.startsWith('en') || voice.lang.includes('US') || voice.lang.includes('GB')
    );
    
    // 음성 카테고리별 분류
    const voiceCategories = {
        female: [],
        male: [],
        child: [],
        other: []
    };
    
    englishVoices.forEach(voice => {
        const name = voice.name.toLowerCase();
        
        if (name.includes('female') || name.includes('woman') || name.includes('samantha') || 
            name.includes('karen') || name.includes('moira') || name.includes('tessa') ||
            name.includes('veena') || name.includes('fiona') || name.includes('alice') ||
            name.includes('allison') || name.includes('kate') || name.includes('susan')) {
            voiceCategories.female.push(voice);
        } else if (name.includes('male') || name.includes('man') || name.includes('daniel') || 
                   name.includes('thomas') || name.includes('alex') || name.includes('fred') ||
                   name.includes('tom') || name.includes('diego') || name.includes('oliver')) {
            voiceCategories.male.push(voice);
        } else if (name.includes('child') || name.includes('junior') || name.includes('kid')) {
            voiceCategories.child.push(voice);
        } else {
            voiceCategories.other.push(voice);
        }
    });
    
    // 카테고리별로 옵션 그룹 생성
    if (voiceCategories.female.length > 0) {
        const femaleGroup = document.createElement('optgroup');
        femaleGroup.label = '👩 여성 목소리';
        voiceCategories.female.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.name;
            option.textContent = `${voice.name} (${voice.lang})`;
            femaleGroup.appendChild(option);
        });
        voiceSelect.appendChild(femaleGroup);
    }
    
    if (voiceCategories.male.length > 0) {
        const maleGroup = document.createElement('optgroup');
        maleGroup.label = '👨 남성 목소리';
        voiceCategories.male.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.name;
            option.textContent = `${voice.name} (${voice.lang})`;
            maleGroup.appendChild(option);
        });
        voiceSelect.appendChild(maleGroup);
    }
    
    if (voiceCategories.child.length > 0) {
        const childGroup = document.createElement('optgroup');
        childGroup.label = '👶 아이 목소리';
        voiceCategories.child.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.name;
            option.textContent = `${voice.name} (${voice.lang})`;
            childGroup.appendChild(option);
        });
        voiceSelect.appendChild(childGroup);
    }
    
    if (voiceCategories.other.length > 0) {
        const otherGroup = document.createElement('optgroup');
        otherGroup.label = '🎭 기타 목소리';
        voiceCategories.other.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.name;
            option.textContent = `${voice.name} (${voice.lang})`;
            otherGroup.appendChild(option);
        });
        voiceSelect.appendChild(otherGroup);
    }
}

// 음성 선택 업데이트
function updateVoice() {
    const selectedVoiceName = voiceSelect.value;
    if (selectedVoiceName) {
        const selectedVoice = availableVoices.find(voice => voice.name === selectedVoiceName);
        currentSpeechSettings.voice = selectedVoice;
        if (selectedVoice) {
            currentSpeechSettings.lang = selectedVoice.lang;
        }
    } else {
        currentSpeechSettings.voice = null;
        currentSpeechSettings.lang = 'en-US';
    }
}

// 읽기 속도 업데이트
function updateSpeed() {
    const value = parseFloat(speedRange.value);
    currentSpeechSettings.rate = value;
    speedValue.textContent = value.toFixed(2);
}

// 음성 높이 업데이트
function updatePitch() {
    const value = parseFloat(pitchRange.value);
    currentSpeechSettings.pitch = value;
    pitchValue.textContent = value.toFixed(1);
}

// 음성 테스트
async function testVoice() {
    const testText = "Hello! This is a voice test. How do you like this voice?";
    await speakSentence(testText);
}

// 로딩 오버레이 표시
function showLoadingOverlay() {
    loadingOverlay.classList.remove('hidden');
}

// 로딩 오버레이 숨김
function hideLoadingOverlay() {
    loadingOverlay.classList.add('hidden');
}

// 토스트 메시지 표시
function showToast(message) {
    // 기존 토스트 제거
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    // 새 토스트 생성
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #48bb78;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        z-index: 1001;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideInDown 0.3s ease-out;
    `;

    // 애니메이션 키프레임 추가
    if (!document.querySelector('#toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            @keyframes slideInDown {
                from {
                    opacity: 0;
                    transform: translateX(-50%) translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(-50%) translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    // 3초 후 자동 제거
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slideInDown 0.3s ease-out reverse';
            setTimeout(() => {
                toast.remove();
            }, 300);
        }
    }, 3000);
}

// 페이지 언로드 시 음성 합성 중지
window.addEventListener('beforeunload', function() {
    speechSynthesis.cancel();
});

// 음성 합성이 중단되었을 때 로딩 오버레이 숨기기
speechSynthesis.addEventListener('voiceschanged', function() {
    // 음성 목록이 변경되었을 때 처리
    console.log('사용 가능한 음성:', speechSynthesis.getVoices().length);
});

// 디버깅용 함수들
window.debugApp = {
    getSentences: () => sentences,
    clearStorage: () => {
        localStorage.removeItem(STORAGE_KEY);
        sentences = [];
        renderSentencesList();
        console.log('저장소가 초기화되었습니다.');
    },
    exportSentences: () => {
        const data = JSON.stringify(sentences, null, 2);
        console.log('저장된 문장들:', data);
        return data;
    }
};

console.log('🎯 영어 회화 튜터가 로드되었습니다!');
console.log('디버깅: window.debugApp 객체를 사용하세요.'); 