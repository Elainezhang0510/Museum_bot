

# tts.py - gTTS 版本 (适用于 Raspberry Pi)
from ast import Str
import os
import json
import hashlib
from re import I
import time
from typing import Optional
from winsound import PlaySound
from gtts import gTTS, lang
import pygame



# 可选：用于 mp3 -> wav 转换（需要 ffmpeg 安装）
try:
    from pydub import AudioSegment
    PDUB_AVAILABLE = True
except Exception:
    PDUB_AVAILABLE = False

# ----------------------
# 全局配置
TTS_INITIALIZED = False
TTS_PROMPTS = {}

# 缓存目录（保存在 sounds/en, sounds/zh）
TTS_CACHE_EN_DIR = os.path.join("sounds", "en")
TTS_CACHE_ZH_DIR = os.path.join("sounds", "zh")

# gTTS 语言代码映射
LANG_CODE_MAP = {
    "EN": "en",
    "ZH": "zh-CN",
}

# ----------------------


def load_tts_prompts():
    global TTS_PROMPTS
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_file_path = os.path.join(base_dir, "data", "generated_tts_prompts.json")
        if not os.path.exists(data_file_path):
            data_file_path = os.path.join(os.getcwd(), "data", "generated_tts_prompts.json")
        with open(data_file_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
            TTS_PROMPTS = obj.get("tts_prompts", obj)
        print("[TTS Manager] Loaded TTS prompts from file system.")
    except Exception as e:
        print(f"[TTS Manager] WARNING: Failed to load TTS prompts: {e}")
        TTS_PROMPTS = {}


def get_tts_prompt(key: str, default: Optional[str] = None) -> str:
    return TTS_PROMPTS.get(key, default or f"Prompt not found: {key}")


def _get_cache_dir(language: str) -> str:
    return TTS_CACHE_EN_DIR if language.upper() == "EN" else TTS_CACHE_ZH_DIR


def _get_cached_file_path(text: str, language: str, speed:str, key: Optional[str] = None) -> str:
    # 使用 key 或 text 的 md5 作为文件名，后缀为 .mp3（保持简单）
    cache_key = f"{text}_{language}_{speed}"
    text_hash = hashlib.md5((key or text).encode("utf-8")).hexdigest()
    cache_dir = "tts_cache"
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{text_hash}.mp3")


def init_tts():
    global TTS_INITIALIZED
    if TTS_INITIALIZED:
        return
    # 创建缓存目录
    os.makedirs(TTS_CACHE_EN_DIR, exist_ok=True)
    os.makedirs(TTS_CACHE_ZH_DIR, exist_ok=True)

    # 初始化 prompts
    load_tts_prompts()

    # 初始化 pygame mixer（允许播放 mp3/wav）
    try:
        pygame.mixer.init(frequency=22050)
    except Exception as e:
        # 在某些环境下需要不同参数或提前安装 SDL 支持库
        print(f"[TTS Manager] Warning: pygame.mixer.init failed: {e}. Trying default init.")
        try:
            pygame.mixer.init()
        except Exception as e2:
            print(f"[TTS Manager] ERROR: pygame mixer cannot be initialized: {e2}")

    TTS_INITIALIZED = True
    print("[TTS Manager] TTS initialized (gTTS + pygame).")


def _play_audio_file(file_path: str):
    try:
        # 如果正在播放，先停止
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except Exception:
                pass

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    except Exception:
        # ignore
        pass

    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        tmp_mp3=None
        
        while pygame.mixer.music.get_busy():
              continue
        return(tmp_mp3)
    except Exception as e:
        print(f"TTS: Error generating/playing audio: {e}")
        return None



def _synthesize_to_file_gtts(text: str, language: str, out_path: str, speed: float = 3.0):
    lang_code = LANG_CODE_MAP.get(language.upper(), "en")
    tmp_mp3 = out_path + ".tmp.mp3"
    try:
        tts = gTTS(text=text, lang=lang_code)
        tts.save(tmp_mp3)
       
    except Exception as e:
        if os.path.exists(tmp_mp3):
            os.remove(tmp_mp3)
        raise RuntimeError(f"gTTS synthesis failed: {e}")

    # 若最终文件是 .mp3（out_path endswith .mp3），直接重命名
    try:
        os.replace(tmp_mp3, out_path)
    except Exception:
        # fallback copy & remove
        import shutil
        shutil.copy(tmp_mp3, out_path)
        os.remove(tmp_mp3)


def speak(text: str, language: str, speed: float = 2.0, key: None = None):

    tts=None

    try:
        # 规范化语言代码：转换为小写
        language = language.lower()
        print(f"Normalized language code: '{language}'")
        
        # 为不同语言设置正确的参数
        if language == 'zh':
            tts_lang = 'zh'
            tts_slow = False
        else:
            tts_lang = 'en'
            tts_slow = False
        
        print(f"Generating TTS for {tts_lang}: {text[:30]}...")
    except Exception as e:
        print(f'[TTS Error] {e}. Fallback: {text}')
    try:    
        # 尝试多种中文语言代码
        if language.lower() in ['zh', 'cn', 'chinese']:
            lang_options = ['zh', 'zh-cn', 'zh-tw', 'zh-CN', 'zh-TW']
        else:
            lang_options = [language, 'en', 'en-US']
        
        success = False
        for lang_option in lang_options:
            try:
                print(f"Trying language: {lang_option}")
                tts = gTTS(text=text, lang=lang_option, slow=False)
                success = True
                print(f"Success with language: {lang_option}")
                break
            except Exception as lang_error:
                print(f"Failed with {lang_option}: {lang_error}")
                continue
        
        if not success:
            print(f"All language options failed for: {language}")
            print(f"Fallback text: {text}")
            return

    except Exception as e:
        print(f"[TTS Critical Error] {e}")
        print(f"Fallback: {text}")
        
    tts = gTTS(text=text, lang=language, slow=False)
    try:
        # 直接转换语言代码
        if language == 'zh':
            tts_lang = 'zh-cn'
        else:
            tts_lang = language  # 保持其他语言不变
    except Exception as e:
        print(f'[TTS Manager]Unsupported language code:{language},defaulting to English.Error:{e}')

    # 使用缓存
    try:
        cached_file_path = _get_cached_file_path(text, language, speed)
        language=language.lower()
    except Exception as e:
        print(f'[TTS Manager]Error generating cache path:{e}')
        return

    if os.path.exists(cached_file_path):
        print(f"[TTS Manager] Using cached file: {cached_file_path}")
        _play_audio_file(cached_file_path)
        return

    # 合成并缓存
    try:
        print(f"[TTS Manager] Synthesizing: '{text[:40]}...' (lang={language})")
        _synthesize_to_file_gtts(text, language, cached_file_path, speed=speed)
        print(f"[TTS Manager] Cached generated speech to: {cached_file_path}")
        _play_audio_file(cached_file_path)
    
    except Exception as e:
        print(f"[TTS Manager] TTS synthesis error: {e}")


def pregenerate_fixed_strings():
    print("[TTS Manager] Pre-generating fixed strings...")
    if not TTS_PROMPTS:
        load_tts_prompts()
    for key, prompt_text in TTS_PROMPTS.items():
        language = "ZH" if key.endswith("_zh") else "EN" if key.endswith("_en") else None
        if language:
            print(f"[TTS Manager] Generating: '{prompt_text}' ({language}) for key '{key}'")
            try:
                speak(prompt_text, language, key=key)
            except Exception as e:
                print(f"[TTS Manager] Warning: failed to generate prompt {key}: {e}")
    print("[TTS Manager] Pre-generation complete.")

