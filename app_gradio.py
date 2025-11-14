import gradio as gr
import requests
import time
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import random
import logging
from PIL import Image
import io
import base64
import uuid

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- API配置 ---
# 去水印
WATERMARK_API_KEY = "9394a5c6d9454cd2b31e24661dd11c3d"
WATERMARK_WEBAPP_ID = "1986469254155403266"
WATERMARK_NODE_INFO = [
    {"nodeId": "191", "fieldName": "image", "fieldValue": "placeholder.jpg", "description": "image"}
]

# 溶图打光
LIGHTING_API_KEY = "9394a5c6d9454cd2b31e24661dd11c3d"
LIGHTING_WEBAPP_ID = "1985718229576425473"
LIGHTING_NODE_INFO = [
    {"nodeId": "437", "fieldName": "image", "fieldValue": "placeholder.png", "description": "image"}
]

# 姿态迁移
POSE_API_KEY = "9394a5c6d9454cd2b31e24661dd11c3d"
POSE_WEBAPP_ID = "1975745173911154689"
POSE_NODE_INFO = [
    {"nodeId": "245", "fieldName": "image", "fieldValue": "placeholder.png", "description": "角色图片"},
    {"nodeId": "244", "fieldName": "image", "fieldValue": "placeholder.png", "description": "姿势参考图"}
]

# 图像优化 WAN 2.2
ENHANCE_API_KEY = "9394a5c6d9454cd2b31e24661dd11c3d"
ENHANCE_WEBAPP_ID_V2_2 = "1986501194824773634"
ENHANCE_NODE_INFO_V2_2 = [
    {"nodeId": "14", "fieldName": "image", "fieldValue": "placeholder.jpg", "description": "image"}
]

# 图像优化 WAN 2.1
ENHANCE_WEBAPP_ID_V2_1 = "1947599512657453057"
ENHANCE_NODE_INFO_V2_1 = [
    {"nodeId": "38", "fieldName": "image", "fieldValue": "placeholder.png", "description": "图片输入"},
    {"nodeId": "60", "fieldName": "text", "fieldValue": "8k, high quality, high detail", "description": "正向提示词补充"},
    {"nodeId": "4", "fieldName": "text", "fieldValue": "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走", "description": "反向提示词"}
]

# 系统配置
MAX_RETRIES = 3
POLL_INTERVAL = 4
MAX_POLL_COUNT = 240
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

# --- 辅助函数 ---
def image_to_base64(image):
    """将 PIL Image 转换为 base64 字符串"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def create_comparison_html(original_image, enhanced_image):
    """创建图像对比滑块的 HTML - 纯 JavaScript 实现，无需外部库"""
    original_b64 = image_to_base64(original_image)
    enhanced_b64 = image_to_base64(enhanced_image)

    # 生成唯一 ID 避免多个实例冲突
    unique_id = f"comp_{int(time.time() * 1000)}"

    html = f"""
    <div class="comparison-wrapper-{unique_id}" style="width: 100%; max-width: 1000px; margin: 20px auto; padding: 20px; background: #f8f9fa; border-radius: 12px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
        <div class="comparison-container-{unique_id}" style="position: relative; width: 100%; overflow: hidden; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); user-select: none;">
            <!-- 优化后的图片（底层，完整显示）-->
            <img src="{enhanced_b64}" alt="优化后" style="display: block; width: 100%; height: auto; border-radius: 8px;">

            <!-- 原图（顶层，通过 clip-path 控制显示区域）-->
            <div class="original-overlay-{unique_id}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; overflow: hidden; clip-path: inset(0 100% 0 0);">
                <img src="{original_b64}" alt="原图" style="display: block; width: 100%; height: auto; border-radius: 8px;">
            </div>

            <!-- 分割线和滑块 -->
            <div class="slider-line-{unique_id}" style="position: absolute; top: 0; left: 0%; width: 3px; height: 100%; background: white; box-shadow: 0 0 10px rgba(0,0,0,0.5); cursor: ew-resize; z-index: 10;">
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 40px; height: 40px; background: white; border-radius: 50%; box-shadow: 0 2px 8px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;">
                    <div style="width: 0; height: 0; border-top: 8px solid transparent; border-bottom: 8px solid transparent; border-right: 8px solid #666; margin-right: 2px;"></div>
                    <div style="width: 0; height: 0; border-top: 8px solid transparent; border-bottom: 8px solid transparent; border-left: 8px solid #666; margin-left: 2px;"></div>
                </div>
            </div>

            <!-- 标签 -->
            <div style="position: absolute; top: 20px; left: 20px; padding: 10px 20px; background: rgba(0, 0, 0, 0.75); color: white; border-radius: 6px; font-size: 15px; font-weight: 600; z-index: 5; backdrop-filter: blur(4px);">
                📷 原图
            </div>
            <div style="position: absolute; top: 20px; right: 20px; padding: 10px 20px; background: rgba(0, 0, 0, 0.75); color: white; border-radius: 6px; font-size: 15px; font-weight: 600; z-index: 5; backdrop-filter: blur(4px);">
                ✨ 优化后
            </div>
        </div>

        <!-- 提示信息 -->
        <div style="text-align: center; margin-top: 20px; padding: 15px; background: white; border-radius: 8px; color: #495057; font-size: 14px; line-height: 1.6; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
            <div style="margin-bottom: 10px;">
                💡 <strong style="color: #0066cc;">使用说明</strong>：拖动中间的滑块可以对比原图和优化后的效果
            </div>
            <div>
                ⬅️ <strong style="color: #0066cc;">向左滑动</strong>：查看原图 |
                ➡️ <strong style="color: #0066cc;">向右滑动</strong>：查看优化后 |
                默认显示优化后的效果
            </div>
            <div style="margin-top: 15px;">
                <a href="{enhanced_b64}" download="optimized_image.png" style="display: inline-block; padding: 10px 24px; background: #0066cc; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; transition: all 0.3s;">
                    📥 下载优化后的图片
                </a>
            </div>
        </div>
    </div>

    <script>
    (function() {{
        const container = document.querySelector('.comparison-container-{unique_id}');
        const overlay = document.querySelector('.original-overlay-{unique_id}');
        const sliderLine = document.querySelector('.slider-line-{unique_id}');

        if (!container || !overlay || !sliderLine) return;

        let isDragging = false;

        // 初始化位置（默认显示优化后，即原图被完全裁剪）
        function setPosition(percentage) {{
            percentage = Math.max(0, Math.min(100, percentage));
            const clipPercentage = 100 - percentage;
            overlay.style.clipPath = `inset(0 ${{clipPercentage}}% 0 0)`;
            sliderLine.style.left = percentage + '%';
        }}

        // 设置初始位置为 0%（完全显示优化后的图）
        setPosition(0);

        function handleMove(e) {{
            if (!isDragging && e.type !== 'click') return;

            const rect = container.getBoundingClientRect();
            let x;

            if (e.type.includes('touch')) {{
                x = e.touches[0].clientX;
            }} else {{
                x = e.clientX;
            }}

            const percentage = ((x - rect.left) / rect.width) * 100;
            setPosition(percentage);
        }}

        // 鼠标事件
        sliderLine.addEventListener('mousedown', (e) => {{
            isDragging = true;
            e.preventDefault();
        }});

        document.addEventListener('mousemove', handleMove);

        document.addEventListener('mouseup', () => {{
            isDragging = false;
        }});

        // 触摸事件（移动端支持）
        sliderLine.addEventListener('touchstart', (e) => {{
            isDragging = true;
            e.preventDefault();
        }});

        document.addEventListener('touchmove', handleMove);

        document.addEventListener('touchend', () => {{
            isDragging = false;
        }});

        // 点击容器直接跳转
        container.addEventListener('click', handleMove);

        // 键盘支持
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowLeft') {{
                const currentLeft = parseFloat(sliderLine.style.left) || 0;
                setPosition(currentLeft - 5);
            }} else if (e.key === 'ArrowRight') {{
                const currentLeft = parseFloat(sliderLine.style.left) || 0;
                setPosition(currentLeft + 5);
            }}
        }});
    }})();
    </script>
    """

    return html

# --- 核心API函数 ---
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

def run_task_with_retry(api_key, webapp_id, node_info_list, max_retries=3, instance_type=None):
    for attempt in range(max_retries):
        try:
            url = 'https://www.runninghub.cn/task/openapi/ai-app/run'
            headers = {'Host': 'www.runninghub.cn', 'Content-Type': 'application/json'}
            payload = {
                "apiKey": api_key,
                "webappId": webapp_id,
                "nodeInfoList": node_info_list
            }

            if instance_type:
                payload["instanceType"] = instance_type

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

def fetch_task_outputs(api_key, task_id, task_type="watermark"):
    """获取任务结果"""
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
                file_url = data["data"][0].get("fileUrl")
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

# --- 处理函数 ---
def process_watermark(image):
    """去水印处理"""
    if image is None:
        return None, "❌ 请上传图片"

    try:
        # 转换图片格式
        img = Image.fromarray(image)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # 上传文件
        yield None, "⏳ 正在上传图片..."
        uploaded_filename = upload_file_with_retry(img_byte_arr, "input.png", WATERMARK_API_KEY)

        # 构建节点信息
        node_info_list = copy.deepcopy(WATERMARK_NODE_INFO)
        for node in node_info_list:
            if node["nodeId"] == "191":
                node["fieldValue"] = uploaded_filename

        # 启动任务
        yield None, "⏳ 正在启动去水印任务..."
        task_id = run_task_with_retry(WATERMARK_API_KEY, WATERMARK_WEBAPP_ID, node_info_list)

        # 轮询状态
        poll_count = 0
        while poll_count < MAX_POLL_COUNT:
            time.sleep(POLL_INTERVAL)
            poll_count += 1
            status = get_task_status(WATERMARK_API_KEY, task_id)

            progress = min(90, 35 + (55 * poll_count / MAX_POLL_COUNT))
            yield None, f"⏳ 处理中... {int(progress)}%"

            if status == "SUCCESS":
                break
            elif status == "FAILED":
                raise Exception("API任务处理失败")

        if poll_count >= MAX_POLL_COUNT:
            raise Exception("任务超时")

        # 获取结果
        yield None, "⏳ 正在下载结果..."
        result_url = fetch_task_outputs(WATERMARK_API_KEY, task_id, "watermark")
        result_data = download_result_image(result_url)

        # 转换为图片
        result_image = Image.open(io.BytesIO(result_data))

        yield result_image, "✅ 去水印完成！"

    except Exception as e:
        yield None, f"❌ 处理失败: {str(e)}"

def process_lighting(image):
    """溶图打光处理"""
    if image is None:
        return None, "❌ 请上传图片"

    try:
        # 转换图片格式
        img = Image.fromarray(image)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # 上传文件
        yield None, "⏳ 正在上传图片..."
        uploaded_filename = upload_file_with_retry(img_byte_arr, "input.png", LIGHTING_API_KEY)

        # 构建节点信息
        node_info_list = copy.deepcopy(LIGHTING_NODE_INFO)
        for node in node_info_list:
            if node["nodeId"] == "437":
                node["fieldValue"] = uploaded_filename

        # 启动任务
        yield None, "⏳ 正在启动溶图打光任务..."
        task_id = run_task_with_retry(LIGHTING_API_KEY, LIGHTING_WEBAPP_ID, node_info_list, instance_type="plus")

        # 轮询状态
        poll_count = 0
        while poll_count < MAX_POLL_COUNT:
            time.sleep(POLL_INTERVAL)
            poll_count += 1
            status = get_task_status(LIGHTING_API_KEY, task_id)

            progress = min(90, 35 + (55 * poll_count / MAX_POLL_COUNT))
            yield None, f"⏳ 处理中... {int(progress)}%"

            if status == "SUCCESS":
                break
            elif status == "FAILED":
                raise Exception("API任务处理失败")

        if poll_count >= MAX_POLL_COUNT:
            raise Exception("任务超时")

        # 获取结果
        yield None, "⏳ 正在下载结果..."
        result_url = fetch_task_outputs(LIGHTING_API_KEY, task_id, "lighting")
        result_data = download_result_image(result_url)

        # 转换为图片
        result_image = Image.open(io.BytesIO(result_data))

        yield result_image, "✅ 溶图打光完成！"

    except Exception as e:
        yield None, f"❌ 处理失败: {str(e)}"

def process_pose(character_image, reference_image):
    """姿态迁移处理"""
    if character_image is None or reference_image is None:
        return None, "❌ 请同时上传角色图片和姿势参考图"

    try:
        # 转换角色图片
        char_img = Image.fromarray(character_image)
        char_byte_arr = io.BytesIO()
        char_img.save(char_byte_arr, format='PNG')
        char_byte_arr = char_byte_arr.getvalue()

        # 转换参考图片
        ref_img = Image.fromarray(reference_image)
        ref_byte_arr = io.BytesIO()
        ref_img.save(ref_byte_arr, format='PNG')
        ref_byte_arr = ref_byte_arr.getvalue()

        # 上传角色图片
        yield None, "⏳ 正在上传角色图片..."
        char_filename = upload_file_with_retry(char_byte_arr, "character.png", POSE_API_KEY)

        # 上传参考图片
        yield None, "⏳ 正在上传姿势参考图..."
        ref_filename = upload_file_with_retry(ref_byte_arr, "reference.png", POSE_API_KEY)

        # 构建节点信息
        node_info_list = copy.deepcopy(POSE_NODE_INFO)
        for node in node_info_list:
            if node["nodeId"] == "245":
                node["fieldValue"] = char_filename
            elif node["nodeId"] == "244":
                node["fieldValue"] = ref_filename

        # 启动任务
        yield None, "⏳ 正在启动姿态迁移任务..."
        task_id = run_task_with_retry(POSE_API_KEY, POSE_WEBAPP_ID, node_info_list)

        # 轮询状态
        poll_count = 0
        while poll_count < MAX_POLL_COUNT:
            time.sleep(POLL_INTERVAL)
            poll_count += 1
            status = get_task_status(POSE_API_KEY, task_id)

            progress = min(90, 35 + (55 * poll_count / MAX_POLL_COUNT))
            yield None, f"⏳ 处理中... {int(progress)}%"

            if status == "SUCCESS":
                break
            elif status == "FAILED":
                raise Exception("API任务处理失败")

        if poll_count >= MAX_POLL_COUNT:
            raise Exception("任务超时")

        # 获取结果
        yield None, "⏳ 正在下载结果..."
        result_urls = fetch_task_outputs(POSE_API_KEY, task_id, "pose")

        # 下载第一个结果（如果有多个结果，取第一个）
        if result_urls:
            result_data = download_result_image(result_urls[0])
            result_image = Image.open(io.BytesIO(result_data))
            yield result_image, f"✅ 姿态迁移完成！生成了 {len(result_urls)} 个结果"
        else:
            raise Exception("未找到结果")

    except Exception as e:
        yield None, f"❌ 处理失败: {str(e)}"

# --- 队列管理（支持5并发） ---
# 全局队列和处理标志
enhance_queue_global = []
processing_lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=5)  # 5并发
active_tasks = set()  # 跟踪活跃任务

# --- 风格提示词预设 ---
STYLE_PROMPTS = {
    "默认": {
        "positive": "",
        "negative": ""
    },
    "写实": {
        "positive": "photorealistic, 8k uhd, raw photo, dslr, soft lighting, high quality, film grain, Fujifilm XT3, sharp focus, detailed skin texture, volumetric fog, cinematic composition, (specific lighting: natural light/golden hour/studio lighting), shot on 35mm/50mm/85mm lens, bokeh, ultra detailed, professional photography",
        "negative": "cartoon, cg, 3d render, unreal, anime, illustration, painting, sketch, drawing, artwork, low quality, blurry, pixelated, jpeg artifacts, bad anatomy, deformed, mutated, disfigured, poorly drawn face, extra limbs, duplicate, worst quality, watermark, signature, text"
    },
    "3D卡通": {
        "positive": "3d render, pixar style, disney style, octane render, blender, unreal engine 5, cute character design, stylized, volumetric lighting, soft shadows, vibrant colors, high detail, 8k, cartoon aesthetic, smooth surfaces, professional 3d artwork, trending on artstation, perfect topology, clean geometry",
        "negative": "realistic, photorealistic, real photo, photograph, 2d, flat, sketch, low poly, low quality, blurry, pixelated, bad anatomy, deformed, poorly modeled, bad topology, artifacts, glitches, worst quality, low detail, amateur, noise, grain, dirty render"
    },
    "二次元": {
        "positive": "(masterpiece:1.2), (best quality:1.2), (ultra detailed:1.2), anime style, illustration, high resolution, perfect anatomy, beautiful detailed eyes, detailed face, vibrant colors, soft shading, cel shading, clean lineart, smooth lines, depth of field, bokeh effect, official art, trending on pixiv, by (artist style if needed)",
        "negative": "realistic, photorealistic, 3d, cg render, low quality, worst quality, normal quality, bad anatomy, bad hands, bad fingers, extra fingers, missing fingers, poorly drawn hands, poorly drawn face, deformed, ugly, mutated, disfigured, fused fingers, extra limbs, duplicate, blurry, pixelated, jpeg artifacts, watermark, signature, username, text, out of frame, cropped"
    }
}

def add_to_queue(files, version, style, queue_state):
    """添加文件到队列（自动触发）"""
    global enhance_queue_global

    if not files:
        return None, queue_state, render_queue_dataframe(queue_state), "⚠️ 未选择文件"

    # 初始化队列
    if queue_state is None:
        queue_state = []

    # 添加新文件到队列
    for file in files:
        file_id = str(uuid.uuid4())[:8]
        item = {
            "id": file_id,
            "file": file,
            "version": version,
            "style": style,  # 添加风格参数
            "status": "pending",
            "original": None,
            "enhanced": None,
            "error": None
        }
        queue_state.append(item)
        enhance_queue_global.append(item)

    # 启动后台处理（如果未在处理中）
    start_background_processing()

    # 清空文件选择器并更新显示
    return None, queue_state, render_queue_dataframe(queue_state), f"📋 已添加 {len(files)} 个文件到队列"

def start_background_processing():
    """启动后台处理线程（支持5并发）"""
    global active_tasks

    with processing_lock:
        # 获取所有待处理的任务
        pending_tasks = [task for task in enhance_queue_global if task["status"] == "pending"]

        # 计算可以启动的新任务数量
        available_slots = 5 - len(active_tasks)

        # 提交新任务到线程池
        for task in pending_tasks[:available_slots]:
            if task["id"] not in active_tasks:
                active_tasks.add(task["id"])
                logger.info(f"🚀 提交任务到线程池: {task['id']} (当前活跃: {len(active_tasks)}/5)")
                executor.submit(process_single_item_wrapper, task)

def process_single_item_wrapper(item):
    """包装器：处理单个任务并更新活跃任务集"""
    global active_tasks

    try:
        process_single_item(item)
    except Exception as e:
        logger.error(f"处理任务失败: {e}")
        item["status"] = "error"
        item["error"] = str(e)
    finally:
        # 任务完成后从活跃集合中移除
        with processing_lock:
            active_tasks.discard(item["id"])

        # 尝试启动下一个任务
        start_background_processing()

def process_single_item(item):
    """处理单个图片优化任务"""
    try:
        # 更新状态为处理中
        item["status"] = "processing"
        logger.info(f"📝 任务 {item['id']} 状态: pending -> processing")

        # 读取图片文件
        img_data = item["file"]
        img = Image.open(io.BytesIO(img_data))

        # 保存原图（转为PNG）
        original_buffer = io.BytesIO()
        img.save(original_buffer, format='PNG')
        item["original"] = original_buffer.getvalue()

        # 根据版本选择配置
        version = item["version"]
        if version == "WAN 2.1":
            webapp_id = ENHANCE_WEBAPP_ID_V2_1
            node_info = ENHANCE_NODE_INFO_V2_1
            image_node_id = "38"
        else:  # WAN 2.2
            webapp_id = ENHANCE_WEBAPP_ID_V2_2
            node_info = ENHANCE_NODE_INFO_V2_2
            image_node_id = "14"

        # 上传文件
        logger.info(f"⬆️ 任务 {item['id']} 开始上传文件到API")
        uploaded_filename = upload_file_with_retry(item["original"], f"input_{item['id']}.png", ENHANCE_API_KEY)

        # 构建节点信息
        node_info_list = copy.deepcopy(node_info)
        for node in node_info_list:
            if node["nodeId"] == image_node_id:
                node["fieldValue"] = uploaded_filename

        # 添加风格提示词（如果不是默认风格）
        style = item.get("style", "默认")
        if style != "默认" and style in STYLE_PROMPTS:
            prompts = STYLE_PROMPTS[style]

            # 添加正向提示词（nodeId 60）
            if prompts["positive"]:
                node_info_list.append({
                    "nodeId": "60",
                    "fieldName": "text",
                    "fieldValue": prompts["positive"],
                    "description": "正向提示词补充"
                })

            # 添加反向提示词（nodeId 4）
            if prompts["negative"]:
                node_info_list.append({
                    "nodeId": "4",
                    "fieldName": "text",
                    "fieldValue": prompts["negative"],
                    "description": "反向提示词"
                })

            logger.info(f"🎨 任务 {item['id']} 应用风格: {style}")

        # 启动任务
        logger.info(f"🎬 任务 {item['id']} 提交API处理请求 [{version}]")
        task_id = run_task_with_retry(ENHANCE_API_KEY, webapp_id, node_info_list)

        # 轮询状态
        poll_count = 0
        while poll_count < MAX_POLL_COUNT:
            time.sleep(POLL_INTERVAL)
            poll_count += 1
            status = get_task_status(ENHANCE_API_KEY, task_id)

            if status == "SUCCESS":
                break
            elif status == "FAILED":
                raise Exception("API任务处理失败")

        if poll_count >= MAX_POLL_COUNT:
            raise Exception("任务超时")

        # 获取结果
        logger.info(f"⬇️ 任务 {item['id']} 开始下载结果")
        result_url = fetch_task_outputs(ENHANCE_API_KEY, task_id, "enhance")
        result_data = download_result_image(result_url)

        # 保存优化后的图片（PNG格式）
        result_image = Image.open(io.BytesIO(result_data))
        enhanced_buffer = io.BytesIO()
        result_image.save(enhanced_buffer, format='PNG')
        item["enhanced"] = enhanced_buffer.getvalue()

        # 更新状态为完成
        item["status"] = "completed"
        logger.info(f"✅ 任务 {item['id']} 完成！状态: processing -> completed")

    except Exception as e:
        item["status"] = "error"
        item["error"] = str(e)
        logger.error(f"❌ 任务 {item['id']} 失败: {str(e)}")
        raise

def get_queue_status(queue_state):
    """获取队列状态（定时刷新）"""
    if queue_state is None:
        return queue_state, []
    return queue_state, render_queue_dataframe(queue_state)

def render_queue_dataframe(queue_state):
    """渲染队列为DataFrame数据"""
    if not queue_state:
        return []

    # 状态映射
    status_text = {
        "pending": "⏳ 等待中",
        "processing": "🔄 处理中",
        "completed": "✅ 已完成",
        "error": "❌ 失败"
    }

    # 生成DataFrame数据
    data = []
    for item in queue_state:
        # 显示模型版本
        model_version = item.get("version", "---")

        data.append([
            item["id"],
            status_text.get(item["status"], "未知"),
            model_version,
            "点击查看" if item["status"] == "completed" else "---"
        ])

    return data

def show_selected_image(evt: gr.SelectData, queue_state):
    """点击DataFrame行显示图片（统一高度800px）"""
    if not queue_state or evt.index[0] >= len(queue_state):
        return None, None

    item = queue_state[evt.index[0]]

    if item["status"] == "completed" and item["original"] and item["enhanced"]:
        # 转换为PIL Image
        original_img = Image.open(io.BytesIO(item["original"]))
        enhanced_img = Image.open(io.BytesIO(item["enhanced"]))

        # 统一高度到800px，保持宽高比
        target_height = 800

        # 调整原图大小
        orig_width, orig_height = original_img.size
        if orig_height != target_height:
            scale = target_height / orig_height
            new_width = int(orig_width * scale)
            original_img = original_img.resize((new_width, target_height), Image.LANCZOS)

        # 调整优化图大小
        enh_width, enh_height = enhanced_img.size
        if enh_height != target_height:
            scale = target_height / enh_height
            new_width = int(enh_width * scale)
            enhanced_img = enhanced_img.resize((new_width, target_height), Image.LANCZOS)

        return original_img, enhanced_img

    return None, None

def clear_queue():
    """清空队列"""
    global enhance_queue_global
    enhance_queue_global = []
    return None, [], "✅ 队列已清空"

# --- Gradio界面 ---
def create_interface():
    with gr.Blocks(title="RunningHub AI - 智能图片处理工具", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎨 RunningHub AI - 智能图片处理工具

        提供多种AI图片处理功能：去水印、溶图打光、姿态迁移、图像优化
        """)

        with gr.Tabs():
            # 去水印
            with gr.Tab("🚿 去水印"):
                with gr.Row():
                    with gr.Column():
                        watermark_input = gr.Image(label="上传需要去水印的图片", type="numpy")
                        watermark_btn = gr.Button("开始去水印", variant="primary")
                    with gr.Column():
                        watermark_output = gr.Image(label="去水印结果")
                        watermark_status = gr.Textbox(label="状态", interactive=False)

                watermark_btn.click(
                    fn=process_watermark,
                    inputs=[watermark_input],
                    outputs=[watermark_output, watermark_status]
                )

            # 溶图打光
            with gr.Tab("✨ 溶图打光"):
                with gr.Row():
                    with gr.Column():
                        lighting_input = gr.Image(label="上传需要溶图打光的图片", type="numpy")
                        lighting_btn = gr.Button("开始溶图打光", variant="primary")
                    with gr.Column():
                        lighting_output = gr.Image(label="溶图打光结果")
                        lighting_status = gr.Textbox(label="状态", interactive=False)

                lighting_btn.click(
                    fn=process_lighting,
                    inputs=[lighting_input],
                    outputs=[lighting_output, lighting_status]
                )

            # 姿态迁移
            with gr.Tab("🤸 姿态迁移"):
                with gr.Row():
                    with gr.Column():
                        pose_char_input = gr.Image(label="角色图片", type="numpy")
                        pose_ref_input = gr.Image(label="姿势参考图", type="numpy")
                        pose_btn = gr.Button("开始姿态迁移", variant="primary")
                    with gr.Column():
                        pose_output = gr.Image(label="姿态迁移结果")
                        pose_status = gr.Textbox(label="状态", interactive=False)

                pose_btn.click(
                    fn=process_pose,
                    inputs=[pose_char_input, pose_ref_input],
                    outputs=[pose_output, pose_status]
                )

            # 图像优化（队列上传 - 自动处理 + DataFrame列表）
            with gr.Tab("🎨 图像优化"):
                with gr.Row():
                    # 左侧：上传和控制区（缩小占比）
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 上传图片")
                        gr.Markdown("*拖拽或点击选择，自动进入队列*")
                        enhance_version = gr.Radio(
                            choices=["WAN 2.2", "WAN 2.1"],
                            value="WAN 2.2",
                            label="模型版本"
                        )
                        enhance_style = gr.Radio(
                            choices=["默认", "写实", "3D卡通", "二次元"],
                            value="默认",
                            label="风格"
                        )
                        enhance_files = gr.File(
                            label="选择图片（支持多选）",
                            file_count="multiple",
                            file_types=["image"],
                            type="binary"
                        )
                        clear_btn = gr.Button("🗑️ 清空队列", size="sm")

                        gr.Markdown("---")
                        enhance_status = gr.Textbox(label="状态", interactive=False, lines=2)

                    # 右侧：队列展示区
                    with gr.Column(scale=4):
                        gr.Markdown("### 📊 处理队列")
                        queue_display = gr.Dataframe(
                            headers=["ID", "状态", "模型", "操作"],
                            datatype=["str", "str", "str", "str"],
                            label="队列列表（点击行查看详情）",
                            interactive=False
                        )

                        gr.Markdown("#### 🖼️ 图片查看（点击列表行查看，Tabs切换对比）")
                        with gr.Tabs():
                            with gr.Tab("📷 原图"):
                                enhance_original = gr.Image(label="原图", show_label=False, height=600)
                            with gr.Tab("🎨 优化后"):
                                enhance_enhanced = gr.Image(label="优化后", show_label=False, height=600)

                # 隐藏的队列状态
                queue_state = gr.State(value=None)

                # 自动处理：文件上传时自动添加到队列
                enhance_files.upload(
                    fn=add_to_queue,
                    inputs=[enhance_files, enhance_version, enhance_style, queue_state],
                    outputs=[enhance_files, queue_state, queue_display, enhance_status]
                )

                # 点击列表行显示图片
                queue_display.select(
                    fn=show_selected_image,
                    inputs=[queue_state],
                    outputs=[enhance_original, enhance_enhanced]
                )

                # 清空队列
                clear_btn.click(
                    fn=clear_queue,
                    outputs=[queue_state, queue_display, enhance_status]
                )

                # 定时刷新队列显示（0.5秒更新一次，更及时）
                timer = gr.Timer(value=0.5, active=True)
                timer.tick(
                    fn=get_queue_status,
                    inputs=[queue_state],
                    outputs=[queue_state, queue_display]
                )

        gr.Markdown("""
        ---
        ### 💡 使用说明
        - **去水印**：智能去除图片中的水印，保持图片主体完整
        - **溶图打光**：智能溶图打光处理，提升图片光影效果
        - **姿态迁移**：需要同时上传角色图片和姿势参考图
        - **图像优化**：支持队列上传和批量处理（DataFrame列表 + Tabs切换）
          - 📤 支持多图片同时上传（拖拽或点击选择）
          - 🔄 自动队列处理，无需等待上一张完成
          - 📊 轻量级列表展示，实时显示处理状态
          - 🖱️ 点击列表行查看图片详情
          - 📷 通过Tabs切换查看原图和优化后的对比
          - 💾 图片固定高度600px，宽度按比例缩放
          - 📥 右键点击图片可保存，格式为PNG
          - 🗑️ 可随时清空队列重新开始
        """)

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
