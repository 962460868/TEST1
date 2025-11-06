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

# API配置 - 溶图打光 (NEW)
# 注意：使用与姿态迁移相同的API Key
FUSION_WEBAPP_ID = "1985718229576425473"
FUSION_NODE_INFO = [
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
    .fusion-task-card { border-left: 4px solid #17a2b8; } /* NEW: 溶图打光样式 */
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
    
    /* 仅为图像优化保留虚线框样式 */
    .upload-container {
        border: 2px dashed #0066cc;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
    }
    
    /* 姿态迁移/溶图打光使用简洁样式（无虚线框） */
    .pose-upload-section {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* 图像优化预览样式（仅保留给图像优化使用） */
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
    
    .enhance-preview .stImage > div > img {
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

    /* 功能选择样式 */
    .function-selector {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .function-card {
        border: 2px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.2s ease;
        background: white;
    }
    
    .function-card:hover {
        border-color: #0066cc;
        box-shadow: 0 2px 8px rgba(0,102,204,0.1);
    }
    
    .function-card.active {
        border-color: #0066cc;
        background: #f8f9ff;
        box-shadow: 0 2px 8px rgba(0,102,204,0.15);
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
    
    /* 清空按钮样式 */
    .clear-button button {
        background-color: #6c757d !important;
        color: white !important;
    }
    
    .clear-button button:hover {
        background-color: #5a6268 !important;
    }
    
    /* 成功消息样式 */
    .clear-success {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 6px;
        border: 1px solid #c3e6cb;
        margin: 0.5rem 0;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Session State管理 ---
def get_session_key():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"s_{int(time.time())}_{random.randint(100, 999)}"
    return st.session_state.session_id

def clear_ui_state():
    """简化的UI状态清理，避免与Streamlit内部状态冲突"""
    # 仅增加key值来重置上传器，不删除其他session state
    st.session_state.file_uploader_key += 1
    st.session_state.upload_success = False
    # 设置延迟清空标记
    st.session_state.need_ui_refresh = True

def clear_pose_uploads_delayed():
    """
    延迟清空姿态迁移/溶图打光的上传文件，避免UI残留
    (此函数被 'pose' 和 'fusion' 共享)
    """
    # 标记需要清空，但不立即执行
    st.session_state.need_pose_clear = True
    st.session_state.clear_message = "已清空上传的图片!"

def handle_delayed_clear():
    """处理延迟清空操作"""
    if st.session_state.get('need_pose_clear', False):
        st.session_state.file_uploader_key += 1
        st.session_state.need_pose_clear = False
        # 清空消息将在下次刷新时显示
        
    if st.session_state.get('need_ui_refresh', False):
        st.session_state.need_ui_refresh = False

# 初始化Session State
if 'selected_function' not in st.session_state:
    st.session_state.selected_function = "溶图打光" # NEW: 默认功能
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'task_counter' not in st.session_state:
    st.session_state.task_counter = 0
if 'file_uploader_key' not in st.session_state:
    st.session_state.file_uploader_key = 0
if 'upload_success' not in st.session_state:
    st.session_state.upload_success = False
if 'download_clicked' not in st.session_state:
    st.session_state.download_clicked = {}
if 'task_queue' not in st.session_state:
    st.session_state.task_queue = []
if 'need_pose_clear' not in st.session_state:
    st.session_state.need_pose_clear = False
if 'clear_message' not in st.session_state:
    st.session_state.clear_message = ""
if 'need_ui_refresh' not in st.session_state:
    st.session_state.need_ui_refresh = False

# --- 4. 任务类 ---
class TaskItem:
    def __init__(self, task_id, task_type, session_id, **kwargs):
        self.task_id = task_id
        self.task_type = task_type  # "pose", "enhance", 或 "fusion"
        self.session_id = session_id
        
        # 姿态迁移专用属性
        if task_type == "pose":
            self.character_image_data = kwargs.get('character_image_data')
            self.character_image_name = kwargs.get('character_image_name')
            self.reference_image_data = kwargs.get('reference_image_data')
            self.reference_image_name = kwargs.get('reference_image_name')
            self.result_data_list = []
        
        # 图像优化或溶图打光专用属性 (UPDATED)
        elif task_type == "enhance" or task_type == "fusion":
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

# --- 5. 核心API函数 ---
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
                return result['data']['fileName']
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

def run_task_with_retry(api_key, webapp_id, node_info_list, max_retries=3):
    for attempt in range(max_retries):
        try:
            url = 'https://www.runninghub.cn/task/openapi/ai-app/run'
            headers = {'Host': 'www.runninghub.cn', 'Content-Type': 'application/json'}
            payload = {"apiKey": api_key, "webappId": webapp_id, "nodeInfoList": node_info_list}
            
            response = requests.post(url, headers=headers, json=payload, timeout=RUN_TASK_TIMEOUT)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"任务发起失败: {result.get('msg', '未知错误')}")
            return result['data']['taskId']
            
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
    """
    获取任务结果
    'pose' 返回 [url1, url2, ...]
    'enhance', 'fusion' 返回 "url"
    """
    try:
        url = 'https://www.runninghub.cn/task/openapi/outputs'
        response = requests.post(url, json={'apiKey': api_key, 'taskId': task_id}, timeout=OUTPUT_FETCH_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0 and data.get("data"):
            if task_type == "pose":
                # 姿态迁移 - 支持多个输出
                file_urls = []
                for output_item in data["data"]:
                    file_url = output_item.get("fileUrl")
                    if file_url:
                        file_urls.append(file_url)
                if file_urls:
                    return file_urls # 返回列表
            else:
                # 图像优化 / 溶图打光 - 单个输出 (UPDATED)
                file_url = data["data"][0].get("fileUrl")
                if file_url:
                    return file_url # 返回单个URL字符串
            
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

# --- 6. 任务处理逻辑 ---
def process_pose_task(task):
    """处理姿态迁移任务"""
    api_key = POSE_API_KEY
    webapp_id = POSE_WEBAPP_ID
    node_info = POSE_NODE_INFO

    try:
        # 上传角色图片
        task.progress = 10
        character_uploaded_filename = upload_file_with_retry(
            task.character_image_data, task.character_image_name, api_key)

        # 上传姿势参考图
        task.progress = 20
        reference_uploaded_filename = upload_file_with_retry(
            task.reference_image_data, task.reference_image_name, api_key)

        # 构建节点信息
        task.progress = 25
        node_info_list = copy.deepcopy(node_info)
        for node in node_info_list:
            if node["nodeId"] == "245":  # 角色图片
                node["fieldValue"] = character_uploaded_filename
            elif node["nodeId"] == "244":  # 姿势参考图
                node["fieldValue"] = reference_uploaded_filename

        task.progress = 35
        task.api_task_id = run_task_with_retry(api_key, webapp_id, node_info_list)

        # 轮询状态
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

        # 获取多个结果
        task.progress = 95
        result_urls = fetch_task_outputs(api_key, task.api_task_id, "pose") # 返回列表
        
        # 下载所有结果图片
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
    """处理图像优化任务"""
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
        result_url = fetch_task_outputs(api_key, task.api_task_id, "enhance") # 返回字符串
        task.result_data = download_result_image(result_url)

        task.progress = 100
        task.status = "SUCCESS"

    except Exception as e:
        handle_task_error(task, e)

def process_fusion_task(task):
    """处理溶图打光任务 (NEW)"""
    api_key = POSE_API_KEY # 使用与Pose相同的Key
    webapp_id = FUSION_WEBAPP_ID
    node_info = FUSION_NODE_INFO

    try:
        task.progress = 15
        uploaded_filename = upload_file_with_retry(task.file_data, task.file_name, api_key)

        task.progress = 25
        node_info_list = copy.deepcopy(node_info)
        for node in node_info_list:
            if node["nodeId"] == "437": # 对应节点
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
        result_url = fetch_task_outputs(api_key, task.api_task_id, "fusion") # 返回字符串
        task.result_data = download_result_image(result_url)

        task.progress = 100
        task.status = "SUCCESS"

    except Exception as e:
        handle_task_error(task, e)

def handle_task_error(task, error):
    """统一处理任务错误"""
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
    """处理单个任务的统一入口"""
    task.status = "PROCESSING"
    task.start_time = time.time()

    if task.task_type == "pose":
        process_pose_task(task)
    elif task.task_type == "enhance":
        process_enhance_task(task)
    elif task.task_type == "fusion": # NEW
        process_fusion_task(task)
    
    if task.status == "SUCCESS":
        task.elapsed_time = time.time() - task.start_time

# --- 7. 队列管理 ---
def get_stats():
    processing_count = sum(1 for t in st.session_state.tasks if t.status == "PROCESSING")
    queued_count = len(st.session_state.task_queue) + sum(1 for t in st.session_state.tasks if t.status == "QUEUED")
    success_count = sum(1 for t in st.session_state.tasks if t.status == "SUCCESS")
    failed_count = sum(1 for t in st.session_state.tasks if t.status == "FAILED")
    
    # 分类统计 (UPDATED)
    pose_count = sum(1 for t in st.session_state.tasks if t.task_type == "pose")
    enhance_count = sum(1 for t in st.session_state.tasks if t.task_type == "enhance")
    fusion_count = sum(1 for t in st.session_state.tasks if t.task_type == "fusion")
    
    return {
        'processing': processing_count,
        'queued': queued_count,
        'success': success_count,
        'failed': failed_count,
        'total': len(st.session_state.tasks),
        'pose': pose_count,
        'enhance': enhance_count,
        'fusion': fusion_count # NEW
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

# --- 8. 图片预览组件（仅用于图像优化）---
def show_image_preview_for_enhance(image_file, caption_text):
    """仅用于图像优化的图片预览"""
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

def show_file_info(image_file, file_type="image"):
    """显示文件信息（替代图片预览）"""
    if image_file:
        try:
            from PIL import Image
            import io
            
            # 尝试获取图片尺寸
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
            # 如果无法读取图片信息，显示基本信息
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

# --- 9. 下载按钮组件 ---
def create_download_buttons(task):
    """创建下载按钮 (UPDATED)"""
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
    
    elif (task.task_type == "enhance" or task.task_type == "fusion") and task.result_data:
        file_size = len(task.result_data) / 1024
        
        if task.task_type == "enhance":
            label = f"📥 下载优化结果 ({file_size:.1f}KB)"
            filename = f"optimized_{task.file_name}"
        else: # fusion
            label = f"📥 下载溶图结果 ({file_size:.1f}KB)"
            filename = f"fusion_{task.file_name}"

        st.download_button(
            label=label,
            data=task.result_data,
            file_name=filename,
            mime="image/png",
            key=f"download_{task.task_id}",
            use_container_width=True
        )

# --- 10. 功能界面 ---

def render_fusion_interface():
    """溶图打光界面 (NEW) - 使用延迟清空策略"""
    st.markdown("### 💡 溶图打光")
    st.info("💡 上传一张图片进行AI溶图打光处理")

    # 显示任务成功和清空成功的消息
    if st.session_state.upload_success:
        st.success("✅ 任务已添加到处理队列!")
        st.session_state.upload_success = False

    if st.session_state.clear_message:
        st.markdown(f'<div class="clear-success">✅ {st.session_state.clear_message}</div>', unsafe_allow_html=True)
        st.session_state.clear_message = ""

    # 图片上传（使用简洁样式）
    st.markdown('<div class="pose-upload-section">', unsafe_allow_html=True)
    st.markdown("**🖼️ 原始图片**")
    image_file = st.file_uploader(
        "选择图片",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=False,
        help="选择需要处理的图片",
        key=f"fusion_uploader_{st.session_state.file_uploader_key}"
    )
    
    # 显示文件信息（不显示图片预览）
    if image_file:
        show_file_info(image_file, "image")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # 按钮区域 - 开始处理和清空图片按钮并排
    col1, col2 = st.columns([3, 1])
    
    with col1:
        start_processing = st.button("🚀 开始处理", use_container_width=True, type="primary")
    
    with col2:
        st.markdown('<div class="clear-button">', unsafe_allow_html=True)
        clear_images = st.button("🗑️ 清空图片", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 处理按钮事件
    if clear_images:
        clear_pose_uploads_delayed()  # 使用共享的延迟清空策略
        st.rerun()
    
    if start_processing:
        if image_file:
            with st.spinner('添加任务到队列...'):
                st.session_state.task_counter += 1
                task = TaskItem(
                    st.session_state.task_counter, 
                    "fusion", # 任务类型
                    get_session_key(),
                    file_data=image_file.getvalue(), # 单文件
                    file_name=image_file.name
                )
                st.session_state.tasks.append(task)
                st.session_state.task_queue.append(task)

            # 使用延迟清空策略：先标记成功，延迟清空UI
            st.session_state.upload_success = True
            clear_pose_uploads_delayed() # 延迟清空文件上传器
            st.rerun()
        else:
            st.error("❌ 请上传一张图片！")

def render_pose_interface():
    """姿态迁移界面（使用延迟清空策略）"""
    st.markdown("### 🤸 姿态迁移")
    st.info("💡 需要同时上传角色图片和姿势参考图才能开始处理")

    # 显示任务成功和清空成功的消息
    if st.session_state.upload_success:
        st.success("✅ 任务已添加到处理队列!")
        st.session_state.upload_success = False

    if st.session_state.clear_message:
        st.markdown(f'<div class="clear-success">✅ {st.session_state.clear_message}</div>', unsafe_allow_html=True)
        st.session_state.clear_message = ""

    # 角色图片上传（使用简洁样式，移除虚线框）
    st.markdown('<div class="pose-upload-section">', unsafe_allow_html=True)
    st.markdown("**👤 角色图片**")
    character_image = st.file_uploader(
        "选择角色图片",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=False,
        help="选择需要处理的角色图片",
        key=f"character_uploader_{st.session_state.file_uploader_key}"
    )
    
    # 显示文件信息（不显示图片预览）
    if character_image:
        show_file_info(character_image, "character")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # 姿势参考图上传（使用简洁样式，移除虚线框）
    st.markdown('<div class="pose-upload-section">', unsafe_allow_html=True)
    st.markdown("**🤸 姿势参考图**")
    reference_image = st.file_uploader(
        "选择姿势参考图",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=False,
        help="选择作为姿势参考的图片",
        key=f"reference_uploader_{st.session_state.file_uploader_key}"
    )
    
    # 显示文件信息（不显示图片预览）
    if reference_image:
        show_file_info(reference_image, "reference")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # 按钮区域 - 开始处理和清空图片按钮并排
    col1, col2 = st.columns([3, 1])
    
    with col1:
        start_processing = st.button("🚀 开始处理", use_container_width=True, type="primary")
    
    with col2:
        st.markdown('<div class="clear-button">', unsafe_allow_html=True)
        clear_images = st.button("🗑️ 清空图片", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 处理按钮事件
    if clear_images:
        clear_pose_uploads_delayed()  # 使用延迟清空策略
        st.rerun()
    
    if start_processing:
        if character_image and reference_image:
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

            # 使用延迟清空策略：先标记成功，延迟清空UI
            st.session_state.upload_success = True
            # 延迟清空文件上传器
            clear_pose_uploads_delayed()
            st.rerun()
        else:
            st.error("❌ 请同时上传角色图片和姿势参考图！")

def render_enhance_interface():
    """图像优化界面（保留预览功能和虚线框）"""
    st.markdown("### 🎨 图像优化")
    st.info("💡 支持批量上传，自动加入处理队列")

    if st.session_state.upload_success:
        st.success("✅ 文件已添加到处理队列!")
        st.session_state.upload_success = False

    # 图像优化保留虚线框样式
    st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "选择图片文件",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=True,
        help="支持批量上传，自动加入处理队列",
        key=f"uploader_{st.session_state.file_uploader_key}"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # 图像优化保留预览功能
    if uploaded_files:
        if len(uploaded_files) == 1:
            # 单张图片显示预览
            show_image_preview_for_enhance(uploaded_files[0], "图片预览")
        else:
            # 多张图片显示列表信息
            st.markdown("**📋 已选择的文件：**")
            for i, file in enumerate(uploaded_files, 1):
                show_file_info(file, f"file_{i}")
        
        # 自动添加到队列
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

            st.session_state.upload_success = True
            st.session_state.file_uploader_key += 1
            st.rerun()

# --- 11. 主界面 ---
def main():
    # 处理延迟清空操作
    handle_delayed_clear()

    # 侧边栏功能选择 (UPDATED)
    with st.sidebar:
        st.markdown("## 🎨 功能选择")
        
        # 溶图打光选项 (NEW)
        fusion_selected = st.button(
            "💡 溶图打光", 
            use_container_width=True,
            type="primary" if st.session_state.selected_function == "溶图打光" else "secondary"
        )
        if fusion_selected and st.session_state.selected_function != "溶图打光":
            st.session_state.selected_function = "溶图打光"
            clear_ui_state()  # 清理UI状态
            st.rerun()
        
        st.caption("单图片智能打光")

        # 姿态迁移选项
        pose_selected = st.button(
            "🤸 姿态迁移", 
            use_container_width=True,
            type="primary" if st.session_state.selected_function == "姿态迁移" else "secondary"
        )
        if pose_selected and st.session_state.selected_function != "姿态迁移":
            st.session_state.selected_function = "姿态迁移"
            clear_ui_state()  # 清理UI状态
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
            clear_ui_state()  # 清理UI状态
            st.rerun()
        
        st.caption("单图片智能优化")
        
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
        st.metric("溶图打光", stats['fusion']) # NEW
        st.metric("姿态迁移", stats['pose'])
        st.metric("图像优化", stats['enhance'])
        
        st.divider()
        st.caption(f"💡 全局并发限制: {MAX_CONCURRENT}")
        st.caption(f"🔄 自动刷新: {AUTO_REFRESH_INTERVAL}秒")
        st.caption("✅ 已修复UI残留问题")

    # 主标题
    st.title("🎨 RunningHub AI - 智能图片处理工具")
    st.caption(f"当前模式: **{st.session_state.selected_function}** • 全局并发限制: {MAX_CONCURRENT}")
    
    # 显示功能状态 (UPDATED)
    if st.session_state.selected_function == "姿态迁移":
        st.info("ℹ️ 姿态迁移：延迟清空策略 + 简洁样式 + 清空按钮")
    elif st.session_state.selected_function == "溶图打光":
        st.info("ℹ️ 溶图打光：延迟清空策略 + 简洁样式 + 清空按钮")
    elif st.session_state.selected_function == "图像优化":
        st.info("ℹ️ 图像优化：自动清空策略 + 虚线框 + 预览")
    
    st.divider()

    # 主界面布局
    left_col, right_col = st.columns([1.8, 3.2])

    # 左侧：功能界面 (UPDATED)
    with left_col:
        if st.session_state.selected_function == "溶图打光":
            render_fusion_interface()
        elif st.session_state.selected_function == "姿态迁移":
            render_pose_interface()
        else:
            render_enhance_interface()

    # 右侧：任务列表
    with right_col:
        st.markdown("### 📋 任务列表")

        if not st.session_state.tasks:
            st.info("💡 暂无任务，请选择功能并上传文件开始处理")
        else:
            start_new_tasks()

            # 显示任务 (UPDATED)
            for task in reversed(st.session_state.tasks):
                with st.container():
                    
                    # 动态设置卡片样式
                    task_card_class = "task-card"
                    if task.task_type == "pose":
                        task_card_class = "pose-task-card"
                    elif task.task_type == "enhance":
                        task_card_class = "enhance-task-card"
                    elif task.task_type == "fusion":
                        task_card_class = "fusion-task-card"
                        
                    st.markdown(f'<div class="task-card {task_card_class}">', unsafe_allow_html=True)

                    # 任务头部
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        # 动态设置图标和名称
                        task_type_icon = "❓"
                        task_type_name = "未知"
                        if task.task_type == "pose":
                            task_type_icon = "🤸"
                            task_type_name = "姿态迁移"
                        elif task.task_type == "enhance":
                            task_type_icon = "🎨"
                            task_type_name = "图像优化"
                        elif task.task_type == "fusion":
                            task_type_icon = "💡"
                            task_type_name = "溶图打光"
                        
                        # 动态显示任务名称
                        if task.task_type == "pose":
                            st.markdown(f"**{task_type_icon} {task_type_name}** `#{task.task_id}`")
                            st.markdown(f'<div class="compact-info">👤 角色: {task.character_image_name}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="compact-info">🤸 参考: {task.reference_image_name}</div>', unsafe_allow_html=True)
                        else: # 适用于 enhance 和 fusion
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

                    # 结果处理 (UPDATED)
                    if task.status == "SUCCESS":
                        elapsed_str = f"{int(task.elapsed_time//60)}:{int(task.elapsed_time%60):02d}"
                        
                        if task.task_type == "pose":
                            result_count = len(task.result_data_list)
                            st.success(f"🎉 姿态迁移完成! 用时: {elapsed_str} | 生成了 {result_count} 个结果")
                        elif task.task_type == "enhance":
                            st.success(f"🎉 图像优化完成! 用时: {elapsed_str}")
                        elif task.task_type == "fusion":
                            st.success(f"🎉 溶图打光完成! 用时: {elapsed_str}")
                        
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
        <b>🚀 RunningHub AI - 多功能整合版 v2.3 (三功能版)</b><br>
        <small>溶图打光 + 姿态迁移 + 图像优化</small>
    </div>
    """, unsafe_allow_html=True)

# --- 12. 应用入口 ---
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
        # 过滤掉Streamlit内部的无害错误
        if not any(kw in error_str for kw in ['websocket', 'tornado', 'streamlit', 'inotify', 'connection broken']):
            st.error(f"⚠️ 系统错误: {str(e)[:100]}...")
            st.info("系统将自动恢复...")
            time.sleep(5)
        st.rerun()
