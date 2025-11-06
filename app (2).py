import streamlit as st
import requests
import time
from datetime import datetime
import threading
import copy
import random
import logging
import streamlit.components.v1 as components

# --- 1. 页面配置和全局设置 ---

st.set_page_config(
    page_title="RunningHub AI - 智能图片处理工具",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 配置日志，减少噪音
logging.getLogger("tornado.access").setLevel(logging.ERROR)
logging.getLogger("tornado.application").setLevel(logging.ERROR)
logging.getLogger("tornado.general").setLevel(logging.ERROR)

# API配置 - 姿态迁移
POSE_API_KEY = "c95f4c4d2703479abfbc55eefeb9bb71"
POSE_WEBAPP_ID = "1975745173911154689"
POSE_NODE_INFO = [
    {"nodeId": "245", "fieldName": "image", "fieldValue": "placeholder.png", "description": "角色图片"},
    {"nodeId": "244", "fieldName": "image", "fieldValue": "placeholder.png", "description": "姿势参考图"}
]

# API配置 - 图像优化
ENHANCE_API_KEY = "9394a5c6d9454cd2b31e24661dd11c3d"
ENHANCE_WEBAPP_ID = "1947599512657453057"
ENHANCE_NODE_INFO = [
    {"nodeId": "38", "fieldName": "image", "fieldValue": "placeholder.png", "description": "图片输入"},
    {"nodeId": "60", "fieldName": "text", "fieldValue": "8k, high quality, high detail", "description": "正向提示词补充"},
    {"nodeId": "4", "fieldName": "text", "fieldValue": "色调艳丽,过曝,静态,细节模糊不清,字幕,风格,作品,画作,画面,静止,整体发灰,最差质量,低质量,JPEG压缩残留,丑陋的,残缺的,多余的手指,画得不好的手部,画得不好的脸部,畸形的,毁容的,形态畸形的肢体,手指融合,静止不动的画面,悲乱的背景,三条腿,背景人很多,倒着走", "description": "反向提示词"}
]

# API配置 - 融图打光
LIGHTING_API_KEY = "c95f4c4d2703479abfbc55eefeb9bb71"
LIGHTING_WEBAPP_ID = "1985718229576425473"
LIGHTING_NODE_INFO = [
    {"nodeId": "437", "fieldName": "image", "fieldValue": "placeholder.png", "description": "image"}
]

# 系统配置 - 全局并发限制
MAX_CONCURRENT = 5  # 全局最大并发数
MAX_RETRIES = 3
POLL_INTERVAL = 4
MAX_POLL_COUNT = 240
AUTO_REFRESH_INTERVAL = 7
DISPLAY_TIMEOUT_MINUTES = 5
ACTUAL_TIMEOUT_MINUTES = 20

# 超时配置
UPLOAD_TIMEOUT = 120
RUN_TASK_TIMEOUT = 60  
STATUS_CHECK_TIMEOUT = 25
OUTPUT_FETCH_TIMEOUT = 90
IMAGE_DOWNLOAD_TIMEOUT = 120

# 错误关键词
CONCURRENT_LIMIT_ERRORS = [
    "concurrent limit", "too many requests", "rate limit",
    "队列已满", "并发限制", "服务忙碌", "CONCURRENT_LIMIT_EXCEEDED", "TOO_MANY_REQUESTS"
]

TIMEOUT_ERRORS = [
    "read timed out", "connection timeout", "timeout", "timed out"
]

# --- 2. CSS样式 ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%; border-radius: 6px; height: 2.5em;
        background-color: #0066cc; color: white; font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton>button:hover { 
        background-color: #0052a3; 
        transform: translateY(-1px);
    }
    .task-card {
        background: white; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #0066cc;
    }
    .pose-task-card { border-left: 4px solid #28a745; }
    .enhance-task-card { border-left: 4px solid #fd7e14; }
    .lighting-task-card { border-left: 4px solid #6f42c1; }
    .success-badge { color: #28a745; font-weight: 600; }
    .error-badge { color: #dc3545; font-weight: 600; }
    .processing-badge { color: #fd7e14; font-weight: 600; }
    .queued-badge { color: #6f42c1; font-weight: 600; }
    .metric-box {
        background: white; padding: 0.8rem; border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; margin-bottom: 0.3rem;
    }
    .compact-info { font-size: 0.85em; color: #6c757d; margin: 0.2rem 0; }
    .real-time { 
        font-family: 'Courier New', monospace; 
        color: #495057; 
        font-weight: 500;
        background-color: #f8f9fa;
        padding: 2px 6px;
        border-radius: 3px;
    }
    
    /* 统一的上传容器样式 */
    .upload-container {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        position: relative;
    }
    
    /* 不同功能的容器背景色 */
    .pose-container { 
        border-left: 4px solid #28a745;
        background: #f8fff9;
    }
    .enhance-container { 
        border-left: 4px solid #fd7e14;
        background: #fff8f0;
    }
    .lighting-container { 
        border-left: 4px solid #6f42c1;
        background: #f8f4ff;
    }
    
    /* 图像优化预览样式 */
    .image-preview-container {
        display: flex;
        justify-content: center;
        margin: 10px 0;
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .enhance-preview .stImage > div > img,
    .lighting-preview .stImage > div > img {
        max-height: 400px !important;
        max-width: 100% !important;
        height: auto !important;
        width: auto !important;
        object-fit: contain !important;
        border-radius: 8px;
    }
    
    .preview-caption {
        text-align: center;
        color: #666;
        font-size: 0.9em;
        margin: 5px 0;
        font-style: italic;
    }

    /* 文件信息显示样式 */
    .file-info {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        font-size: 0.9em;
        color: #495057;
    }
    
    .file-info .file-name {
        font-weight: 600;
        color: #212529;
        margin-bottom: 0.25rem;
    }
    
    .file-info .file-details {
        color: #6c757d;
        font-size: 0.85em;
    }

    /* 上传区域标题样式 */
    .upload-section-title {
        font-weight: 600;
        color: #495057;
        margin-bottom: 0.5rem;
        padding: 0.25rem 0;
        border-bottom: 1px solid #dee2e6;
    }
    
    /* 文件处理状态样式 */
    .file-processing {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        color: #856404;
        text-align: center;
    }
    
    .file-success {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 6px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        color: #155724;
        text-align: center;
    }
    
    /* 清空按钮样式 */
    .clear-button {
        margin-top: 1rem;
        text-align: center;
    }
    
    .clear-button button {
        background-color: #6c757d !important;
        color: white !important;
        border: none !important;
        padding: 0.4rem 1rem !important;
        border-radius: 6px !important;
        font-size: 0.9em !important;
    }
    
    .clear-button button:hover {
        background-color: #5a6268 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Session State管理（完全重新设计）---
def get_session_key():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"s_{int(time.time())}_{random.randint(100, 999)}"
    return st.session_state.session_id

def reset_function_state():
    """彻底重置当前功能的状态"""
    current_function = st.session_state.selected_function
    
    # 根据功能类型生成新的唯一key
    timestamp = int(time.time())
    random_suffix = random.randint(1000, 9999)
    
    if current_function == "姿态迁移":
        st.session_state.pose_key = f"pose_{timestamp}_{random_suffix}"
        # 清空姿态迁移相关的临时状态
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith('pose_files_')]
        for key in keys_to_clear:
            del st.session_state[key]
    elif current_function == "图像优化":
        st.session_state.enhance_key = f"enhance_{timestamp}_{random_suffix}"
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith('enhance_files_')]
        for key in keys_to_clear:
            del st.session_state[key]
    else:  # 融图打光
        st.session_state.lighting_key = f"lighting_{timestamp}_{random_suffix}"
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith('lighting_files_')]
        for key in keys_to_clear:
            del st.session_state[key]

def clear_all_upload_states():
    """切换功能时清理所有上传状态"""
    keys_to_remove = []
    for key in list(st.session_state.keys()):
        if any(prefix in key for prefix in [
            'uploader_', 'character_uploader_', 'reference_uploader_', 'lighting_uploader_',
            'pose_files_', 'enhance_files_', 'lighting_files_'
        ]):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
    
    # 重置所有功能的keys
    reset_function_state()

# 初始化Session State
if 'selected_function' not in st.session_state:
    st.session_state.selected_function = "姿态迁移"
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'task_counter' not in st.session_state:
    st.session_state.task_counter = 0
if 'download_clicked' not in st.session_state:
    st.session_state.download_clicked = {}
if 'task_queue' not in st.session_state:
    st.session_state.task_queue = []

# 初始化功能特定的keys
if 'pose_key' not in st.session_state:
    st.session_state.pose_key = "pose_default"
if 'enhance_key' not in st.session_state:
    st.session_state.enhance_key = "enhance_default"
if 'lighting_key' not in st.session_state:
    st.session_state.lighting_key = "lighting_default"

# --- 4. 任务类 ---
class TaskItem:
    def __init__(self, task_id, task_type, session_id, **kwargs):
        self.task_id = task_id
        self.task_type = task_type  # "pose" 或 "enhance" 或 "lighting"
        self.session_id = session_id
        
        # 姿态迁移专用属性
        if task_type == "pose":
            self.character_image_data = kwargs.get('character_image_data')
            self.character_image_name = kwargs.get('character_image_name')
            self.reference_image_data = kwargs.get('reference_image_data')
            self.reference_image_name = kwargs.get('reference_image_name')
            self.result_data_list = []
        
        # 图像优化和融图打光专用属性
        elif task_type in ["enhance", "lighting"]:
            self.file_data = kwargs.get('file_data')
            self.file_name = kwargs.get('file_name')
            self.result_data = None
        
        # 通用属性
        self.status = "QUEUED"
        self.progress = 0
        self.error_message = None
        self.api_task_id = None
        self.created_at = datetime.now()
        self.start_time = None
        self.elapsed_time = None
        self.retry_count = 0
        self.timeout_count = 0

# --- 5-8. 核心API函数、任务处理逻辑、队列管理、图片预览组件 ---
# （这些部分保持不变，为了节省空间我只显示关键修改）

def is_concurrent_limit_error(error_msg):
    error_lower = error_msg.lower()
    return any(keyword in error_lower for keyword in CONCURRENT_LIMIT_ERRORS)

def is_timeout_error(error_msg):
    error_lower = error_msg.lower()
    return any(keyword in error_lower for keyword in TIMEOUT_ERRORS)

def upload_file_with_retry(file_data, file_name, api_key, max_retries=3):
    for attempt in range(max_retries):
        try:
            url = 'https://www.runninghub.cn/task/openapi/upload'
            files = {'file': (file_name, file_data)}
            data = {'apiKey': api_key, 'fileType': 'image'}
            
            response = requests.post(url, files=files, data=data, timeout=UPLOAD_TIMEOUT)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 0:
                return result['data'] ['fileName']
            else:
                raise Exception(f"上传失败: {result.get('msg', '未知错误')}")
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)
                continue
            else:
                raise Exception(f"上传超时，已重试{max_retries}次")
        except Exception as e:
            if attempt < max_retries - 1 and is_timeout_error(str(e)):
                time.sleep((attempt + 1) * 2)
                continue
            else:
                raise

def run_task_with_retry(api_key, webapp_id, node_info_list, instance_type=None, max_retries=3):
    for attempt in range(max_retries):
        try:
            url = 'https://www.runninghub.cn/task/openapi/ai-app/run'
            headers = {'Host': 'www.runninghub.cn', 'Content-Type': 'application/json'}
            payload = {"apiKey": api_key, "webappId": webapp_id, "nodeInfoList": node_info_list}
            
            if instance_type:
                payload["instanceType"] = instance_type
            
            response = requests.post(url, headers=headers, json=payload, timeout=RUN_TASK_TIMEOUT)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"任务发起失败: {result.get('msg', '未知错误')}")
            return result['data'] ['taskId']
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 3)
                continue
            else:
                raise Exception(f"启动任务超时，已重试{max_retries}次")
        except Exception as e:
            if attempt < max_retries - 1 and is_timeout_error(str(e)):
                time.sleep((attempt + 1) * 3)
                continue
            else:
                raise

def get_task_status(api_key, task_id):
    try:
        url = 'https://www.runninghub.cn/task/openapi/status'
        response = requests.post(url, json={'apiKey': api_key, 'taskId': task_id}, timeout=STATUS_CHECK_TIMEOUT)
        response.raise_for_status()
        return response.json().get('data')
    except requests.exceptions.Timeout:
        return "CHECKING"
    except:
        return "UNKNOWN"

def fetch_task_outputs(api_key, task_id, task_type="pose"):
    try:
        url = 'https://www.runninghub.cn/task/openapi/outputs'
        response = requests.post(url, json={'apiKey': api_key, 'taskId': task_id}, timeout=OUTPUT_FETCH_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0 and data.get("data"):
            if task_type == "pose":
                file_urls = []
                for output_item in data["data"]:
                    file_url = output_item.get("fileUrl")
                    if file_url:
                        file_urls.append(file_url)
                if file_urls:
                    return file_urls
            else:
                file_url = data["data"] [0].get("fileUrl")
                if file_url:
                    return file_url
            
        raise Exception(f"获取结果失败: {data.get('msg', '未找到结果')}")
        
    except requests.exceptions.Timeout:
        raise Exception("获取结果超时，请稍后重试")

def download_result_image(url):
    try:
        response = requests.get(url, stream=True, timeout=IMAGE_DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        return response.content
    except requests.exceptions.Timeout:
        raise Exception("下载图片超时")

# 任务处理函数保持不变...
def process_pose_task(task):
    api_key = POSE_API_KEY
    webapp_id = POSE_WEBAPP_ID
    node_info = POSE_NODE_INFO

    try:
        task.progress = 10
        character_uploaded_filename = upload_file_with_retry(
            task.character_image_data, task.character_image_name, api_key)

        task.progress = 20
        reference_uploaded_filename = upload_file_with_retry(
            task.reference_image_data, task.reference_image_name, api_key)

        task.progress = 25
        node_info_list = copy.deepcopy(node_info)
        for node in node_info_list:
            if node["nodeId"] == "245":
                node["fieldValue"] = character_uploaded_filename
            elif node["nodeId"] == "244":
                node["fieldValue"] = reference_uploaded_filename

        task.progress = 35
        task.api_task_id = run_task_with_retry(api_key, webapp_id, node_info_list)

        poll_count = 0
        consecutive_timeouts = 0
        
        while poll_count < MAX_POLL_COUNT:
            time.sleep(POLL_INTERVAL)
            poll_count += 1

            status = get_task_status(api_key, task.api_task_id)
            task.progress = min(90, 35 + (55 * poll_count / MAX_POLL_COUNT))

            if status == "SUCCESS":
                break
            elif status == "FAILED":
                raise Exception("API任务处理失败")
            elif status in ["CHECKING", "UNKNOWN"]:
                consecutive_timeouts += 1
                if consecutive_timeouts > 3:
                    time.sleep(POLL_INTERVAL * 2)
                    consecutive_timeouts = 0
            else:
                consecutive_timeouts = 0

        if poll_count >= MAX_POLL_COUNT:
            raise Exception(f"任务处理超时 (>{ACTUAL_TIMEOUT_MINUTES}分钟)")

        task.progress = 95
        result_urls = fetch_task_outputs(api_key, task.api_task_id, "pose")
        
        task.result_data_list = []
        for i, url in enumerate(result_urls):
            image_data = download_result_image(url)
            task.result_data_list.append({
                'data': image_data,
                'filename': f"pose_result_{i+1}_{task.character_image_name}",
                'url': url
            })

        task.progress = 100
        task.status = "SUCCESS"

    except Exception as e:
        handle_task_error(task, e)

def process_enhance_task(task):
    api_key = ENHANCE_API_KEY
    webapp_id = ENHANCE_WEBAPP_ID
    node_info = ENHANCE_NODE_INFO

    try:
        task.progress = 15
        uploaded_filename = upload_file_with_retry(task.file_data, task.file_name, api_key)

        task.progress = 25
        node_info_list = copy.deepcopy(node_info)
        for node in node_info_list:
            if node["nodeId"] == "38":
                node["fieldValue"] = uploaded_filename

        task.progress = 35
        task.api_task_id = run_task_with_retry(api_key, webapp_id, node_info_list)

        poll_count = 0
        while poll_count < MAX_POLL_COUNT:
            time.sleep(POLL_INTERVAL)
            poll_count += 1

            status = get_task_status(api_key, task.api_task_id)
            task.progress = min(90, 35 + (55 * poll_count / MAX_POLL_COUNT))

            if status == "SUCCESS":
                break
            elif status == "FAILED":
                raise Exception("API任务处理失败")

        if poll_count >= MAX_POLL_COUNT:
            raise Exception(f"任务超时 (>{ACTUAL_TIMEOUT_MINUTES}分钟)")

        task.progress = 95
        result_url = fetch_task_outputs(api_key, task.api_task_id, "enhance")
        task.result_data = download_result_image(result_url)

        task.progress = 100
        task.status = "SUCCESS"

    except Exception as e:
        handle_task_error(task, e)

def process_lighting_task(task):
    api_key = LIGHTING_API_KEY
    webapp_id = LIGHTING_WEBAPP_ID
    node_info = LIGHTING_NODE_INFO

    try:
        task.progress = 15
        uploaded_filename = upload_file_with_retry(task.file_data, task.file_name, api_key)

        task.progress = 25
        node_info_list = copy.deepcopy(node_info)
        for node in node_info_list:
            if node["nodeId"] == "437":
                node["fieldValue"] = uploaded_filename

        task.progress = 35
        task.api_task_id = run_task_with_retry(api_key, webapp_id, node_info_list, instance_type="plus")

        poll_count = 0
        while poll_count < MAX_POLL_COUNT:
            time.sleep(POLL_INTERVAL)
            poll_count += 1

            status = get_task_status(api_key, task.api_task_id)
            task.progress = min(90, 35 + (55 * poll_count / MAX_POLL_COUNT))

            if status == "SUCCESS":
                break
            elif status == "FAILED":
                raise Exception("API任务处理失败")

        if poll_count >= MAX_POLL_COUNT:
            raise Exception(f"任务超时 (>{ACTUAL_TIMEOUT_MINUTES}分钟)")

        task.progress = 95
        result_url = fetch_task_outputs(api_key, task.api_task_id, "lighting")
        task.result_data = download_result_image(result_url)

        task.progress = 100
        task.status = "SUCCESS"

    except Exception as e:
        handle_task_error(task, e)

def handle_task_error(task, error):
    error_msg = str(error)
    task.elapsed_time = time.time() - task.start_time if task.start_time else 0

    is_timeout = is_timeout_error(error_msg)
    is_concurrent = is_concurrent_limit_error(error_msg)

    if is_timeout:
        task.timeout_count += 1
        
    if ((is_concurrent or is_timeout) and task.retry_count < MAX_RETRIES):
        task.retry_count += 1
        task.status = "QUEUED"
        task.progress = 0
        
        if is_timeout:
            delay = (task.timeout_count * 10) + random.randint(5, 15)
        else:
            delay = (2 ** task.retry_count) + random.randint(1, 3)
        
        time.sleep(delay)
        st.session_state.task_queue.append(task)
    else:
        task.status = "FAILED"
        task.error_message = error_msg[:150]

def process_single_task(task):
    task.status = "PROCESSING"
    task.start_time = time.time()

    if task.task_type == "pose":
        process_pose_task(task)
    elif task.task_type == "enhance":
        process_enhance_task(task)
    elif task.task_type == "lighting":
        process_lighting_task(task)
    
    if task.status == "SUCCESS":
        task.elapsed_time = time.time() - task.start_time

def get_stats():
    processing_count = sum(1 for t in st.session_state.tasks if t.status == "PROCESSING")
    queued_count = len(st.session_state.task_queue) + sum(1 for t in st.session_state.tasks if t.status == "QUEUED")
    success_count = sum(1 for t in st.session_state.tasks if t.status == "SUCCESS")
    failed_count = sum(1 for t in st.session_state.tasks if t.status == "FAILED")
    
    pose_count = sum(1 for t in st.session_state.tasks if t.task_type == "pose")
    enhance_count = sum(1 for t in st.session_state.tasks if t.task_type == "enhance")
    lighting_count = sum(1 for t in st.session_state.tasks if t.task_type == "lighting")
    
    return {
        'processing': processing_count,
        'queued': queued_count,
        'success': success_count,
        'failed': failed_count,
        'total': len(st.session_state.tasks),
        'pose': pose_count,
        'enhance': enhance_count,
        'lighting': lighting_count
    }

def start_new_tasks():
    stats = get_stats()
    available_slots = MAX_CONCURRENT - stats['processing']
    
    if available_slots <= 0:
        return
    
    for _ in range(min(available_slots, len(st.session_state.task_queue))):
        if st.session_state.task_queue:
            task = st.session_state.task_queue.pop(0)
            
            thread = threading.Thread(target=process_single_task, args=(task,))
            thread.daemon = True
            thread.start()

def show_image_preview_for_enhance(image_file, caption_text):
    if image_file:
        st.markdown('<div class="image-preview-container enhance-preview">', unsafe_allow_html=True)
        st.image(image_file, caption=caption_text, use_container_width=False)
        
        try:
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(image_file.getvalue()))
            width, height = img.size
            file_size = len(image_file.getvalue()) / 1024
            
            st.markdown(f'''
            <div class="preview-caption">
                📏 尺寸: {width} × {height} px | 📦 大小: {file_size:.1f} KB
            </div>
            ''', unsafe_allow_html=True)
            
        except Exception as e:
            file_size = len(image_file.getvalue()) / 1024
            st.markdown(f'''
            <div class="preview-caption">
                📦 大小: {file_size:.1f} KB
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_image_preview_for_lighting(image_file, caption_text):
    if image_file:
        st.markdown('<div class="image-preview-container lighting-preview">', unsafe_allow_html=True)
        st.image(image_file, caption=caption_text, use_container_width=False)
        
        try:
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(image_file.getvalue()))
            width, height = img.size
            file_size = len(image_file.getvalue()) / 1024
            
            st.markdown(f'''
            <div class="preview-caption">
                📏 尺寸: {width} × {height} px | 📦 大小: {file_size:.1f} KB
            </div>
            ''', unsafe_allow_html=True)
            
        except Exception as e:
            file_size = len(image_file.getvalue()) / 1024
            st.markdown(f'''
            <div class="preview-caption">
                📦 大小: {file_size:.1f} KB
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_file_info(image_file, file_type="image"):
    if image_file:
        try:
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(image_file.getvalue()))
            width, height = img.size
            file_size = len(image_file.getvalue()) / 1024
            
            st.markdown(f'''
            <div class="file-info">
                <div class="file-name">📄 {image_file.name}</div>
                <div class="file-details">
                    📏 尺寸: {width} × {height} px | 
                    📦 大小: {file_size:.1f} KB | 
                    🎨 格式: {image_file.type}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
        except Exception as e:
            file_size = len(image_file.getvalue()) / 1024
            st.markdown(f'''
            <div class="file-info">
                <div class="file-name">📄 {image_file.name}</div>
                <div class="file-details">
                    📦 大小: {file_size:.1f} KB | 
                    🎨 类型: {image_file.type}
                </div>
            </div>
            ''', unsafe_allow_html=True)

def create_download_buttons(task):
    if task.task_type == "pose" and task.result_data_list:
        st.markdown("### 📥 下载结果")
        
        if len(task.result_data_list) == 1:
            result = task.result_data_list[0]
            file_size = len(result['data']) / 1024
            
            st.download_button(
                label=f"📥 下载结果 ({file_size:.1f}KB)",
                data=result['data'],
                file_name=result['filename'],
                mime="image/png",
                key=f"download_{task.task_id}",
                use_container_width=True
            )
        else:
            cols = st.columns(min(len(task.result_data_list), 3))
            
            for i, result in enumerate(task.result_data_list):
                col_idx = i % len(cols)
                with cols[col_idx]:
                    file_size = len(result['data']) / 1024
                    
                    st.download_button(
                        label=f"📥 结果{i+1} ({file_size:.1f}KB)",
                        data=result['data'],
                        file_name=result['filename'],
                        mime="image/png",
                        key=f"download_{task.task_id}_{i}",
                        use_container_width=True
                    )
    
    elif task.task_type == "enhance" and task.result_data:
        file_size = len(task.result_data) / 1024
        
        st.download_button(
            label=f"📥 下载优化结果 ({file_size:.1f}KB)",
            data=task.result_data,
            file_name=f"optimized_{task.file_name}",
            mime="image/png",
            key=f"download_{task.task_id}",
            use_container_width=True
        )
    
    elif task.task_type == "lighting" and task.result_data:
        file_size = len(task.result_data) / 1024
        
        st.download_button(
            label=f"📥 下载打光结果 ({file_size:.1f}KB)",
            data=task.result_data,
            file_name=f"lighting_{task.file_name}",
            mime="image/png",
            key=f"download_{task.task_id}",
            use_container_width=True
        )

# --- 9. 重新设计的功能界面 ---
def render_pose_interface():
    """姿态迁移界面 - 使用会话状态跟踪文件"""
    st.markdown("### 🤸 姿态迁移")
    
    # 使用容器和状态管理来避免UI残留
    with st.container():
        st.markdown('<div class="upload-container pose-container">', unsafe_allow_html=True)
        
        # 检查是否有已处理的文件状态
        processing_key = f"pose_processing_{st.session_state.pose_key}"
        success_key = f"pose_success_{st.session_state.pose_key}"
        
        if st.session_state.get(success_key, False):
            st.markdown('<div class="file-success">✅ 任务已成功添加到处理队列！</div>', unsafe_allow_html=True)
            # 显示清空按钮
            st.markdown('<div class="clear-button">', unsafe_allow_html=True)
            if st.button("🗑️ 开始新任务", key=f"clear_pose_{st.session_state.pose_key}"):
                reset_function_state()
                del st.session_state[success_key]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.get(processing_key, False):
            st.markdown('<div class="file-processing">⏳ 正在处理文件，请稍后...</div>', unsafe_allow_html=True)
        
        else:
            # 正常的文件上传界面
            st.info("💡 需要同时上传角色图片和姿势参考图才能开始处理")
            
            # 角色图片上传
            st.markdown('<div class="upload-section-title">👤 角色图片</div>', unsafe_allow_html=True)
            character_image = st.file_uploader(
                "选择角色图片",
                type=['png', 'jpg', 'jpeg', 'webp'],
                accept_multiple_files=False,
                help="选择需要处理的角色图片",
                key=f"character_{st.session_state.pose_key}",
                label_visibility="collapsed"
            )
            
            if character_image:
                show_file_info(character_image, "character")

            # 姿势参考图上传
            st.markdown('<div class="upload-section-title">🤸 姿势参考图</div>', unsafe_allow_html=True)
            reference_image = st.file_uploader(
                "选择姿势参考图",
                type=['png', 'jpg', 'jpeg', 'webp'],
                accept_multiple_files=False,
                help="选择作为姿势参考的图片",
                key=f"reference_{st.session_state.pose_key}",
                label_visibility="collapsed"
            )
            
            if reference_image:
                show_file_info(reference_image, "reference")

            # 处理按钮
            if st.button("🚀 开始处理", use_container_width=True, type="primary", key=f"process_pose_{st.session_state.pose_key}"):
                if character_image and reference_image:
                    # 标记为处理中
                    st.session_state[processing_key] = True
                    
                    with st.spinner('添加任务到队列...'):
                        st.session_state.task_counter += 1
                        task = TaskItem(
                            st.session_state.task_counter, 
                            "pose",
                            get_session_key(),
                            character_image_data=character_image.getvalue(),
                            character_image_name=character_image.name,
                            reference_image_data=reference_image.getvalue(),
                            reference_image_name=reference_image.name
                        )
                        st.session_state.tasks.append(task)
                        st.session_state.task_queue.append(task)
                    
                    # 标记为成功，清除处理状态
                    del st.session_state[processing_key]
                    st.session_state[success_key] = True
                    st.rerun()
                else:
                    st.error("❌ 请同时上传角色图片和姿势参考图！")
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_enhance_interface():
    """图像优化界面 - 保留预览功能"""
    st.markdown("### 🎨 图像优化")
    
    with st.container():
        st.markdown('<div class="upload-container enhance-container">', unsafe_allow_html=True)
        
        processing_key = f"enhance_processing_{st.session_state.enhance_key}"
        success_key = f"enhance_success_{st.session_state.enhance_key}"
        
        if st.session_state.get(success_key, False):
            st.markdown('<div class="file-success">✅ 文件已成功添加到处理队列！</div>', unsafe_allow_html=True)
            st.markdown('<div class="clear-button">', unsafe_allow_html=True)
            if st.button("🗑️ 开始新任务", key=f"clear_enhance_{st.session_state.enhance_key}"):
                reset_function_state()
                del st.session_state[success_key]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.get(processing_key, False):
            st.markdown('<div class="file-processing">⏳ 正在处理文件，请稍后...</div>', unsafe_allow_html=True)
        
        else:
            st.info("💡 支持批量上传，自动加入处理队列")
            
            uploaded_files = st.file_uploader(
                "选择图片文件",
                type=['png', 'jpg', 'jpeg', 'webp'],
                accept_multiple_files=True,
                help="支持批量上传，自动加入处理队列",
                key=f"enhance_{st.session_state.enhance_key}"
            )

            if uploaded_files:
                if len(uploaded_files) == 1:
                    show_image_preview_for_enhance(uploaded_files[0], "图片预览")
                else:
                    st.markdown("**📋 已选择的文件：**")
                    for i, file in enumerate(uploaded_files, 1):
                        show_file_info(file, f"file_{i}")
                
                # 标记为处理中
                st.session_state[processing_key] = True
                
                with st.spinner(f'添加 {len(uploaded_files)} 个文件...'):
                    for file in uploaded_files:
                        st.session_state.task_counter += 1
                        task = TaskItem(
                            st.session_state.task_counter,
                            "enhance",
                            get_session_key(),
                            file_data=file.getvalue(),
                            file_name=file.name
                        )
                        st.session_state.tasks.append(task)
                        st.session_state.task_queue.append(task)

                del st.session_state[processing_key]
                st.session_state[success_key] = True
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_lighting_interface():
    """融图打光界面 - 保留预览功能"""
    st.markdown("### 💡 融图打光")
    
    with st.container():
        st.markdown('<div class="upload-container lighting-container">', unsafe_allow_html=True)
        
        processing_key = f"lighting_processing_{st.session_state.lighting_key}"
        success_key = f"lighting_success_{st.session_state.lighting_key}"
        
        if st.session_state.get(success_key, False):
            st.markdown('<div class="file-success">✅ 文件已成功添加到处理队列！</div>', unsafe_allow_html=True)
            st.markdown('<div class="clear-button">', unsafe_allow_html=True)
            if st.button("🗑️ 开始新任务", key=f"clear_lighting_{st.session_state.lighting_key}"):
                reset_function_state()
                del st.session_state[success_key]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.get(processing_key, False):
            st.markdown('<div class="file-processing">⏳ 正在处理文件，请稍后...</div>', unsafe_allow_html=True)
        
        else:
            st.info("💡 智能图像打光处理，提升图片光影效果")
            
            uploaded_files = st.file_uploader(
                "选择图片文件",
                type=['png', 'jpg', 'jpeg', 'webp'],
                accept_multiple_files=True,
                help="支持批量上传，自动加入处理队列",
                key=f"lighting_{st.session_state.lighting_key}"
            )

            if uploaded_files:
                if len(uploaded_files) == 1:
                    show_image_preview_for_lighting(uploaded_files[0], "图片预览")
                else:
                    st.markdown("**📋 已选择的文件：**")
                    for i, file in enumerate(uploaded_files, 1):
                        show_file_info(file, f"file_{i}")
                
                st.session_state[processing_key] = True
                
                with st.spinner(f'添加 {len(uploaded_files)} 个文件...'):
                    for file in uploaded_files:
                        st.session_state.task_counter += 1
                        task = TaskItem(
                            st.session_state.task_counter,
                            "lighting",
                            get_session_key(),
                            file_data=file.getvalue(),
                            file_name=file.name
                        )
                        st.session_state.tasks.append(task)
                        st.session_state.task_queue.append(task)

                del st.session_state[processing_key]
                st.session_state[success_key] = True
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- 10. 主界面 ---
def main():
    # 侧边栏功能选择
    with st.sidebar:
        st.markdown("## 🎨 功能选择")
        
        # 姿态迁移选项
        pose_selected = st.button(
            "🤸 姿态迁移", 
            use_container_width=True,
            type="primary" if st.session_state.selected_function == "姿态迁移" else "secondary"
        )
        if pose_selected and st.session_state.selected_function != "姿态迁移":
            st.session_state.selected_function = "姿态迁移"
            clear_all_upload_states()
            st.rerun()
        
        st.caption("角色图片 + 姿势参考图")
        
        # 图像优化选项
        enhance_selected = st.button(
            "🎨 图像优化", 
            use_container_width=True,
            type="primary" if st.session_state.selected_function == "图像优化" else "secondary"
        )
        if enhance_selected and st.session_state.selected_function != "图像优化":
            st.session_state.selected_function = "图像优化"
            clear_all_upload_states()
            st.rerun()
        
        st.caption("单图片智能优化")
        
        # 融图打光选项
        lighting_selected = st.button(
            "💡 融图打光", 
            use_container_width=True,
            type="primary" if st.session_state.selected_function == "融图打光" else "secondary"
        )
        if lighting_selected and st.session_state.selected_function != "融图打光":
            st.session_state.selected_function = "融图打光"
            clear_all_upload_states()
            st.rerun()
        
        st.caption("智能图像打光处理")
        
        st.divider()
        
        # 状态面板
        st.markdown("### 📊 系统状态")
        stats = get_stats()
        
        st.metric("处理中", f"{stats['processing']}/{MAX_CONCURRENT}")
        st.metric("队列中", stats['queued'])
        st.metric("已完成", stats['success'])
        st.metric("失败", stats['failed'])
        
        st.divider()
        
        st.markdown("### 📈 分类统计")
        st.metric("姿态迁移", stats['pose'])
        st.metric("图像优化", stats['enhance'])
        st.metric("融图打光", stats['lighting'])
        
        st.divider()
        st.caption(f"💡 全局并发限制: {MAX_CONCURRENT}")
        st.caption(f"🔄 自动刷新: {AUTO_REFRESH_INTERVAL}秒")
        st.caption("✅ 已彻底修复UI残留问题")

    # 主标题
    st.title("🎨 RunningHub AI - 智能图片处理工具")
    st.caption(f"当前模式: **{st.session_state.selected_function}** • 全局并发限制: {MAX_CONCURRENT}")
    
    # 显示功能状态
    if st.session_state.selected_function == "姿态迁移":
        st.info("ℹ️ 姿态迁移: 简洁模式 - 任务提交后显示"开始新任务"按钮来重置界面")
    elif st.session_state.selected_function == "图像优化":
        st.info("ℹ️ 图像优化: 完整模式 - 支持图片预览，任务提交后显示"开始新任务"按钮")
    else:
        st.info("ℹ️ 融图打光: 完整模式 - 支持图片预览，智能光影处理")
    
    st.divider()

    # 主界面布局
    left_col, right_col = st.columns([1.8, 3.2])

    # 左侧：功能界面
    with left_col:
        if st.session_state.selected_function == "姿态迁移":
            render_pose_interface()
        elif st.session_state.selected_function == "图像优化":
            render_enhance_interface()
        else:
            render_lighting_interface()

    # 右侧：任务列表（保持不变）
    with right_col:
        st.markdown("### 📋 任务列表")

        if not st.session_state.tasks:
            st.info("💡 暂无任务，请选择功能并上传文件开始处理")
        else:
            start_new_tasks()

            # 显示任务
            for task in reversed(st.session_state.tasks):
                with st.container():
                    task_card_class = ""
                    if task.task_type == "pose":
                        task_card_class = "pose-task-card"
                    elif task.task_type == "enhance":
                        task_card_class = "enhance-task-card"
                    elif task.task_type == "lighting":
                        task_card_class = "lighting-task-card"
                    
                    st.markdown(f'<div class="task-card {task_card_class}">', unsafe_allow_html=True)

                    # 任务头部
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        if task.task_type == "pose":
                            task_type_icon = "🤸"
                            task_type_name = "姿态迁移"
                        elif task.task_type == "enhance":
                            task_type_icon = "🎨"
                            task_type_name = "图像优化"
                        else:
                            task_type_icon = "💡"
                            task_type_name = "融图打光"
                        
                        if task.task_type == "pose":
                            st.markdown(f"**{task_type_icon} {task_type_name}** `#{task.task_id}`")
                            st.markdown(f'<div class="compact-info">👤 角色: {task.character_image_name}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="compact-info">🤸 参考: {task.reference_image_name}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f"**{task_type_icon} {task.file_name}** `#{task.task_id}`")
                        
                        if task.retry_count > 0:
                            st.markdown(f'<div class="compact-info">🔄 重试 {task.retry_count}/{MAX_RETRIES}</div>', unsafe_allow_html=True)
                        if task.timeout_count > 0:
                            st.markdown(f'<div class="compact-info">⏰ 超时 {task.timeout_count}次</div>', unsafe_allow_html=True)

                    with col2:
                        if task.status == "SUCCESS":
                            st.markdown('<span class="success-badge">✅ 完成</span>', unsafe_allow_html=True)
                        elif task.status == "FAILED":
                            st.markdown('<span class="error-badge">❌ 失败</span>', unsafe_allow_html=True)
                        elif task.status == "PROCESSING":
                            st.markdown('<span class="processing-badge">⚡ 处理中</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="queued-badge">⏳ 队列中</span>', unsafe_allow_html=True)

                    # 进度显示
                    if task.status == "PROCESSING":
                        st.progress(task.progress / 100, text=f"进度: {int(task.progress)}%")
                        
                        if task.start_time:
                            elapsed = time.time() - task.start_time
                            elapsed_str = f"{int(elapsed//60)}:{int(elapsed%60):02d}"
                            st.markdown(f'<div class="compact-info real-time">⏱️ 已用时: {elapsed_str}</div>', unsafe_allow_html=True)

                    elif task.status == "QUEUED":
                        st.markdown('<div class="compact-info">⏳ 等待处理...</div>', unsafe_allow_html=True)

                    # 结果处理
                    if task.status == "SUCCESS":
                        elapsed_str = f"{int(task.elapsed_time//60)}:{int(task.elapsed_time%60):02d}"
                        
                        if task.task_type == "pose":
                            result_count = len(task.result_data_list)
                            st.success(f"🎉 姿态迁移完成! 用时: {elapsed_str} | 生成了 {result_count} 个结果")
                        elif task.task_type == "enhance":
                            st.success(f"🎉 图像优化完成! 用时: {elapsed_str}")
                        else:
                            st.success(f"🎉 融图打光完成! 用时: {elapsed_str}")
                        
                        create_download_buttons(task)

                    elif task.status == "FAILED":
                        st.error(f"💥 处理失败")
                        if task.error_message:
                            if is_timeout_error(task.error_message):
                                st.warning(f"⏰ 超时错误: 已重试 {task.retry_count} 次")
                            st.markdown(f'<div class="compact-info">❌ 错误: {task.error_message}</div>', unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

            st.divider()

            # 操作按钮
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🗑️ 清空所有", use_container_width=True):
                    st.session_state.tasks = []
                    st.session_state.task_queue = []
                    st.session_state.download_clicked = {}
                    st.rerun()

            with col2:
                if st.button("🔄 重启失败", use_container_width=True):
                    failed_tasks = [t for t in st.session_state.tasks if t.status == "FAILED"]
                    for task in failed_tasks:
                        task.status = "QUEUED"
                        task.retry_count = 0
                        task.timeout_count = 0
                        task.error_message = None
                        task.progress = 0
                        st.session_state.task_queue.append(task)
                    if failed_tasks:
                        st.success(f"✅ 已重启 {len(failed_tasks)} 个失败任务")
                    else:
                        st.info("ℹ️ 没有失败的任务需要重启")
                    st.rerun()
            
            with col3:
                if st.button("🔄 强制刷新", use_container_width=True):
                    st.rerun()

    # 页脚
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #6c757d; padding: 15px;'>
        <b>🚀 RunningHub AI - 多功能整合版 v3.1 (UI修复版)</b><br>
        <small>彻底解决文件上传器UI残留问题 • 使用会话状态管理 • 手动重置界面</small>
    </div>
    """, unsafe_allow_html=True)

# --- 11. 应用入口 ---
if __name__ == "__main__":
    try:
        main()

        # 自动刷新逻辑
        has_active_tasks = any(t.status in ["PROCESSING", "QUEUED"] for t in st.session_state.tasks) or len(st.session_state.task_queue) > 0

        if has_active_tasks:
            time.sleep(AUTO_REFRESH_INTERVAL)
            st.rerun()

    except Exception as e:
        error_str = str(e).lower()
        if not any(kw in error_str for kw in ['websocket', 'tornado', 'streamlit', 'inotify', 'connection broken']):
            st.error(f"⚠️ 系统错误: {str(e)[:100]}...")
            st.info("系统将自动恢复...")
            time.sleep(5)
        st.rerun()
