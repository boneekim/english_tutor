#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, send_from_directory, request, jsonify, send_file
import os
import requests
import tempfile
import hashlib
from datetime import datetime, timedelta
import json
import base64

app = Flask(__name__)

# 현재 디렉토리 경로
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 고정 Gemini API 키
FIXED_GEMINI_API_KEY = 'AIzaSyBXVCdF8sWsFocpJx1Cs4YK4eSlwgij2O0'

# CORS 허용
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 메인 페이지
@app.route('/')
def index():
    return send_from_directory(CURRENT_DIR, 'index.html')

# Gemini TTS API 엔드포인트
@app.route('/api/gemini-tts', methods=['POST'])
def gemini_text_to_speech():
    try:
        data = request.json
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': '텍스트가 필요합니다.'}), 400
        
        # 캐시를 위한 해시 생성
        cache_key = hashlib.md5(f"{text}_gemini".encode()).hexdigest()
        cache_dir = os.path.join(CURRENT_DIR, 'tts_cache')
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{cache_key}.mp3")
        
        # 캐시된 파일이 있고 24시간 이내라면 재사용
        if os.path.exists(cache_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_time < timedelta(hours=24):
                return send_file(cache_file, mimetype='audio/mpeg')
        
        # Gemini API로 음성 생성 요청
        gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={FIXED_GEMINI_API_KEY}'
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Please convert this text to speech: {text}"
                }]
            }]
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(gemini_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 401:
            return jsonify({'error': 'Gemini API 키가 유효하지 않습니다.'}), 401
        elif response.status_code == 429:
            return jsonify({'error': 'Gemini API 사용 한도를 초과했습니다.'}), 429
        elif not response.ok:
            # Gemini API가 실패하면 브라우저 TTS 사용하도록 알림
            return jsonify({'error': 'gemini_fallback', 'message': 'Gemini API 사용 불가, 브라우저 TTS 사용'}), 503
        
        # 실제로는 Gemini가 직접 음성을 생성하지 않으므로, 
        # 여기서는 성공 응답을 보내고 클라이언트에서 브라우저 TTS를 사용하도록 함
        return jsonify({'success': True, 'message': '브라우저 TTS 사용'})
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'API 요청 시간이 초과되었습니다.'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'네트워크 오류: {str(e)}'}), 500
    except Exception as e:
        print(f"Gemini TTS 오류: {e}")
        return jsonify({'error': f'음성 생성 중 오류가 발생했습니다: {str(e)}'}), 500

# 기존 OpenAI TTS API 엔드포인트 (호환성을 위해 유지)
@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    try:
        data = request.json
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': '텍스트가 필요합니다.'}), 400
        
        # 브라우저 TTS 사용하도록 응답
        return jsonify({'success': True, 'message': '브라우저 TTS 사용'})
        
    except Exception as e:
        print(f"TTS 오류: {e}")
        return jsonify({'error': f'음성 생성 중 오류가 발생했습니다: {str(e)}'}), 500

# 정적 파일 제공
@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(CURRENT_DIR, filename)

if __name__ == '__main__':
    print("🎯 영어 회화 튜터 서버를 시작합니다...")
    print("📱 브라우저에서 http://localhost:8080 으로 접속하세요!")
    print("📱 모바일에서는 컴퓨터의 IP 주소:8080 으로 접속하세요!")
    print("⏹️  종료하려면 Ctrl+C를 누르세요.")
    print("=" * 50)
    
    # 네트워크 접근 가능하도록 host='0.0.0.0' 설정
    app.run(host='0.0.0.0', port=8080, debug=True) 