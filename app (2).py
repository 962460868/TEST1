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
    page_title="RunningHub AI - 智能图片优化工具",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 配置日志，减少噪音
logging.getLogger("tornado.access").setLevel(logging.ERROR)
logging.getLogger("tornado.application").setLevel(logging.ERROR)
logging.getLogger("tornado.general").setLevel(logging.ERROR)

# 更新API配置
API_KEY = "c95f4c4d2703479abfbc55eefeb9bb71"
WEBAPP_ID = "1975745173911154689"
NODE_INFO = [
    {"nodeId": "245", "fieldName": "image", "fieldValue": "placeholder.png", "description": "图片"},
    {"nodeId": "244", "fieldName": "image", "fieldValue": "placeholder.png", "description": "姿势参考图"}
]

# 系统配置 - 增加超时时间
MAX_CONCURRENT = 3  # 减少并发数避免资源冲突
MAX_RETRIES = 3
POLL_INTERVAL = 5  # 增加轮询间隔
MAX_POLL_COUNT = 240  # 20分钟超时
AUTO_REFRESH_INTERVAL = 8
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
    .upload-container {
        border: 2px dashed #0066cc;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
    }
    
    /* 图片预览样式控制 */
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
    
    /* 控制预览图片尺寸 */
    .stImage > div > img {
        max-height: 400px !important;
        max-width: 100% !important;
        height: auto !important;
        width: auto !important;
        object-fit: contain !important;
        border-radius: 8px;
    }
    
    /* 专门为上传预览区域的图片设置样式 */
    .upload-container .stImage > div > img {
        max-height: 400px !important;
        max-width: 100% !important;
        height: auto !important;
        width: auto !important;
        object-fit: contain !important;
        border-radius: 6px;
        display: block;
        margin: 0 auto;
    }
    
    .result-images {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 10px;
        margin: 10px 0;
    }
    .result-item {
        border: 1px solid #ddd;
        border-radius: 6px;
        overflow: hidden;
        background: white;
    }
    
    /* 预览图片标题样式 */
    .preview-caption {
        text-align: center;
        color: #666;
        font-size: 0.9em;
        margin: 5px 0;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Session State管理 ---
def get_session_key():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"s_{int(time.time())}_{random.randint(100, 999)}"
    return st.session_state.session_id

# 初始化Session State
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

# --- 4. 任务类 ---
class TaskItem:
    def __init__(self, task_id, character_image_data, character_image_name, reference_image_data, reference_image_name, session_id):
        self.task_id = task_id
        self.character_image_data = character_image_data  # 角色图片数据
        self.character_image_name = character_image_name  # 角色图片名称
        self.reference_image_data = reference_image_data
        self.reference_image_name = reference_image_name
        self.session_id = session_id
        self.status = "QUEUED"
        self.progress = 0
        self.result_data_list = []  # 修改为列表，支持多个结果
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

def fetch_task_outputs(api_key, task_id):
    """获取任务结果 - 修改为支持多个输出"""
    try:
        url = 'https://www.runninghub.cn/task/openapi/outputs'
        response = requests.post(url, json={'apiKey': api_key, 'taskId': task_id}, timeout=OUTPUT_FETCH_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0 and data.get("data"):
            file_urls = []
            for output_item in data["data"]:
                file_url = output_item.get("fileUrl")
                if file_url:
                    file_urls.append(file_url)
            
            if file_urls:
                return file_urls
            
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
def process_single_task(task, api_key, webapp_id, node_info):
    """处理单个任务"""
    task.status = "PROCESSING"
    task.start_time = time.time()

    try:
        # 上传角色图片
        task.progress = 10
        character_uploaded_filename = upload_file_with_retry(task.character_image_data, task.character_image_name, api_key)

        # 上传姿势参考图
        task.progress = 20
        reference_uploaded_filename = upload_file_with_retry(task.reference_image_data, task.reference_image_name, api_key)

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
        # 获取多个结果
        result_urls = fetch_task_outputs(api_key, task.api_task_id)
        
        # 下载所有结果图片
        task.result_data_list = []
        for i, url in enumerate(result_urls):
            image_data = download_result_image(url)
            task.result_data_list.append({
                'data': image_data,
                'filename': f"result_{i+1}_{task.character_image_name}",
                'url': url
            })

        task.progress = 100
        task.status = "SUCCESS"
        task.elapsed_time = time.time() - task.start_time

    except Exception as e:
        error_msg = str(e)
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

# --- 7. 队列管理 ---
def get_stats():
    processing_count = sum(1 for t in st.session_state.tasks if t.status == "PROCESSING")
    queued_count = len(st.session_state.task_queue) + sum(1 for t in st.session_state.tasks if t.status == "QUEUED")
    success_count = sum(1 for t in st.session_state.tasks if t.status == "SUCCESS")
    failed_count = sum(1 for t in st.session_state.tasks if t.status == "FAILED")
    
    return {
        'processing': processing_count,
        'queued': queued_count,
        'success': success_count,
        'failed': failed_count,
        'total': len(st.session_state.tasks)
    }

def start_new_tasks():
    stats = get_stats()
    available_slots = MAX_CONCURRENT - stats['processing']
    
    if available_slots <= 0:
        return
    
    for _ in range(min(available_slots, len(st.session_state.task_queue))):
        if st.session_state.task_queue:
            task = st.session_state.task_queue.pop(0)
            
            thread = threading.Thread(
                target=process_single_task,
                args=(task, API_KEY, WEBAPP_ID, NODE_INFO)
            )
            thread.daemon = True
            thread.start()

# --- 8. 图片预览组件 ---
def show_image_preview(image_file, caption_text, container_key):
    """显示尺寸受控的图片预览"""
    if image_file:
        # 使用HTML容器来更好地控制样式
        st.markdown(f'<div class="image-preview-container">', unsafe_allow_html=True)
        
        # 显示图片，Streamlit会自动应用CSS样式
        st.image(image_file, caption=caption_text, use_container_width=False)
        
        # 显示图片信息
        try:
            from PIL import Image
            import io
            
            # 获取图片尺寸信息
            img = Image.open(io.BytesIO(image_file.getvalue()))
            width, height = img.size
            file_size = len(image_file.getvalue()) / 1024  # KB
            
            st.markdown(f'''
            <div class="preview-caption">
                📏 尺寸: {width} × {height} px | 📦 大小: {file_size:.1f} KB
            </div>
            ''', unsafe_allow_html=True)
            
        except Exception as e:
            # 如果无法获取图片信息，只显示文件大小
            file_size = len(image_file.getvalue()) / 1024
            st.markdown(f'''
            <div class="preview-caption">
                📦 大小: {file_size:.1f} KB
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- 9. 下载按钮组件 ---
def create_download_buttons(task):
    """创建多个下载按钮"""
    if not task.result_data_list:
        return
        
    st.markdown("### 📥 下载结果")
    
    # 如果只有一个结果，显示单个下载按钮
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
        # 多个结果，显示网格布局
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

# --- 10. 主界面 ---
def main():
    st.title("🎨 RunningHub AI - 智能图片优化工具")
    st.caption("双图片处理模式 • 角色图片 + 姿势参考图 • 支持多结果输出")

    st.info(f"⏱️ 预计处理时间: {DISPLAY_TIMEOUT_MINUTES}分钟 | 🔄 刷新间隔: {AUTO_REFRESH_INTERVAL}秒 | 📊 最大并发: {MAX_CONCURRENT}")
    st.divider()

    # 主界面布局
    left_col, right_col = st.columns([1.8, 3.2])

    # 左侧：上传和状态
    with left_col:
        st.markdown("### 📁 双图片上传")
        
        st.info("💡 需要同时上传角色图片和姿势参考图才能开始处理")

        if st.session_state.upload_success:
            st.success("✅ 任务已添加到处理队列!")
            st.session_state.upload_success = False

        # 角色图片上传
        st.markdown('<div class="upload-container">', unsafe_allow_html=True)
        st.markdown("**👤 角色图片**")
        character_image = st.file_uploader(
            "选择角色图片",
            type=['png', 'jpg', 'jpeg', 'webp'],
            accept_multiple_files=False,
            help="选择需要处理的角色图片",
            key=f"character_uploader_{st.session_state.file_uploader_key}"
        )
        if character_image:
            show_image_preview(character_image, "角色图片预览", "character_preview")
        st.markdown('</div>', unsafe_allow_html=True)

        # 姿势参考图上传
        st.markdown('<div class="upload-container">', unsafe_allow_html=True)
        st.markdown("**🤸 姿势参考图**")
        reference_image = st.file_uploader(
            "选择姿势参考图",
            type=['png', 'jpg', 'jpeg', 'webp'],
            accept_multiple_files=False,
            help="选择作为姿势参考的图片",
            key=f"reference_uploader_{st.session_state.file_uploader_key}"
        )
        if reference_image:
            show_image_preview(reference_image, "参考图预览", "reference_preview")
        st.markdown('</div>', unsafe_allow_html=True)

        # 开始处理按钮
        if st.button("🚀 开始处理", use_container_width=True, type="primary"):
            if character_image and reference_image:
                with st.spinner('添加任务到队列...'):
                    st.session_state.task_counter += 1
                    task = TaskItem(
                        st.session_state.task_counter, 
                        character_image.getvalue(), 
                        character_image.name,
                        reference_image.getvalue(),
                        reference_image.name,
                        get_session_key()
                    )
                    st.session_state.tasks.append(task)
                    st.session_state.task_queue.append(task)

                st.session_state.upload_success = True
                st.session_state.file_uploader_key += 1
                st.rerun()
            else:
                st.error("❌ 请同时上传角色图片和姿势参考图！")

        st.divider()

        # 状态面板
        with st.expander("📊 系统状态", expanded=True):
            stats = get_stats()

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown(f'<div class="metric-box"><h4 style="margin:0;color:#6f42c1">{stats["queued"]}</h4><p style="margin:0;font-size:11px">队列</p></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-box"><h4 style="margin:0;color:#28a745">{stats["success"]}</h4><p style="margin:0;font-size:11px">完成</p></div>', unsafe_allow_html=True)

            with c2:
                st.markdown(f'<div class="metric-box"><h4 style="margin:0;color:#fd7e14">{stats["processing"]}/{MAX_CONCURRENT}</h4><p style="margin:0;font-size:11px">处理中</p></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-box"><h4 style="margin:0;color:#dc3545">{stats["failed"]}</h4><p style="margin:0;font-size:11px">失败</p></div>', unsafe_allow_html=True)

            with c3:
                st.markdown(f'<div class="metric-box"><h4 style="margin:0;color:#6c757d">{stats["total"]}</h4><p style="margin:0;font-size:11px">总数</p></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-box"><h4 style="margin:0;color:#0066cc">{len(st.session_state.task_queue)}</h4><p style="margin:0;font-size:11px">等待</p></div>', unsafe_allow_html=True)

    # 右侧：任务列表
    with right_col:
        st.markdown("### 📋 任务列表")

        if not st.session_state.tasks:
            st.info("💡 暂无任务，请上传双图片开始处理")
        else:
            start_new_tasks()

            # 显示任务
            for task in reversed(st.session_state.tasks):
                with st.container():
                    st.markdown('<div class="task-card">', unsafe_allow_html=True)

                    # 任务头部
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.markdown(f"**角色: {task.character_image_name}** `#{task.task_id}`")
                        st.markdown(f'<div class="compact-info">👤 角色: {task.character_image_name}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="compact-info">🤸 参考: {task.reference_image_name}</div>', unsafe_allow_html=True)
                        
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
                    if task.status == "SUCCESS" and task.result_data_list:
                        elapsed_str = f"{int(task.elapsed_time//60)}:{int(task.elapsed_time%60):02d}"
                        result_count = len(task.result_data_list)
                        st.success(f"🎉 处理完成! 用时: {elapsed_str} | 生成了 {result_count} 个结果")
                        
                        # 显示多个下载按钮
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
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🗑️ 清空任务", use_container_width=True):
                    st.session_state.tasks = []
                    st.session_state.task_queue = []
                    st.session_state.download_clicked = {}
                    st.rerun()

            with col2:
                if st.button("🔄 重新启动队列", use_container_width=True):
                    failed_tasks = [t for t in st.session_state.tasks if t.status == "FAILED"]
                    for task in failed_tasks:
                        task.status = "QUEUED"
                        task.retry_count = 0
                        task.timeout_count = 0
                        task.error_message = None
                        task.progress = 0
                        st.session_state.task_queue.append(task)
                    st.success(f"✅ 已重启 {len(failed_tasks)} 个失败任务")
                    st.rerun()

    # 页脚
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #6c757d; padding: 15px;'>
        <b>🚀 RunningHub AI - 双图片处理版 v2.3</b><br>
        <small>角色图片 + 姿势参考图 • 优化预览尺寸 • 支持多结果输出</small>
    </div>
    """, unsafe_allow_html=True)

# --- 11. 应用入口 ---
if __name__ == "__main__":
    try:
        main()

        has_active_tasks = any(t.status in ["PROCESSING", "QUEUED"] for t in st.session_state.tasks) or len(st.session_state.task_queue) > 0

        if has_active_tasks:
            time.sleep(AUTO_REFRESH_INTERVAL)
            st.rerun()

    except Exception as e:
        error_str = str(e).lower()
        if not any(kw in error_str for kw in ['websocket', 'tornado', 'streamlit', 'inotify']):
            st.error(f"⚠️ 系统错误: {str(e)[:100]}...")
            st.info("系统将自动恢复...")
            time.sleep(5)
        st.rerun()
