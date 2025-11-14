import gradio as gr
import requests
import time
from datetime import datetime
import threading
import copy
import random
import logging
from PIL import Image
import io
import base64

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

def process_enhance(image, version):
    """图像优化处理 - 返回原图和优化后的图片（使用Tabs切换）"""
    if image is None:
        return None, None, "❌ 请上传图片"

    try:
        # 保存原图（用于对比）
        original_img = Image.fromarray(image)

        # 转换图片格式
        img = Image.fromarray(image)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # 根据版本选择配置
        if version == "WAN 2.1":
            webapp_id = ENHANCE_WEBAPP_ID_V2_1
            node_info = ENHANCE_NODE_INFO_V2_1
            image_node_id = "38"
        else:  # WAN 2.2
            webapp_id = ENHANCE_WEBAPP_ID_V2_2
            node_info = ENHANCE_NODE_INFO_V2_2
            image_node_id = "14"

        # 上传文件
        yield None, None, f"⏳ 正在上传图片 [{version}]..."
        uploaded_filename = upload_file_with_retry(img_byte_arr, "input.png", ENHANCE_API_KEY)

        # 构建节点信息
        node_info_list = copy.deepcopy(node_info)
        for node in node_info_list:
            if node["nodeId"] == image_node_id:
                node["fieldValue"] = uploaded_filename

        # 启动任务
        yield None, None, f"⏳ 正在启动图像优化任务 [{version}]..."
        task_id = run_task_with_retry(ENHANCE_API_KEY, webapp_id, node_info_list)

        # 轮询状态
        poll_count = 0
        while poll_count < MAX_POLL_COUNT:
            time.sleep(POLL_INTERVAL)
            poll_count += 1
            status = get_task_status(ENHANCE_API_KEY, task_id)

            progress = min(90, 35 + (55 * poll_count / MAX_POLL_COUNT))
            yield None, None, f"⏳ 处理中 [{version}]... {int(progress)}%"

            if status == "SUCCESS":
                break
            elif status == "FAILED":
                raise Exception("API任务处理失败")

        if poll_count >= MAX_POLL_COUNT:
            raise Exception("任务超时")

        # 获取结果
        yield None, None, "⏳ 正在下载结果..."
        result_url = fetch_task_outputs(ENHANCE_API_KEY, task_id, "enhance")
        result_data = download_result_image(result_url)

        # 转换为图片
        result_image = Image.open(io.BytesIO(result_data))

        # 返回：原图、优化图、状态信息（使用Tabs切换查看）
        yield original_img, result_image, f"✅ 图像优化完成 [{version}]！点击上方标签页切换查看原图和优化效果"

    except Exception as e:
        yield None, None, f"❌ 处理失败: {str(e)}"

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

            # 图像优化
            with gr.Tab("🎨 图像优化"):
                with gr.Row():
                    with gr.Column(scale=2):
                        enhance_version = gr.Radio(
                            choices=["WAN 2.2", "WAN 2.1"],
                            value="WAN 2.2",
                            label="选择模型版本"
                        )
                        enhance_input = gr.Image(label="上传需要优化的图片", type="numpy")
                        enhance_btn = gr.Button("开始图像优化", variant="primary", size="lg")
                        enhance_status = gr.Textbox(label="处理状态", interactive=False)

                    with gr.Column(scale=3):
                        gr.Markdown("### 📊 优化效果对比")
                        gr.Markdown("*点击标签页切换查看原图和优化后的效果*")

                        # 使用 Tabs 切换显示
                        with gr.Tabs():
                            with gr.Tab("📷 原图"):
                                enhance_original = gr.Image(label="原图", show_label=False)
                            with gr.Tab("🎨 优化后"):
                                enhance_enhanced = gr.Image(label="优化后", show_label=False)

                # 处理优化
                enhance_btn.click(
                    fn=process_enhance,
                    inputs=[enhance_input, enhance_version],
                    outputs=[enhance_original, enhance_enhanced, enhance_status]
                )

        gr.Markdown("""
        ---
        ### 💡 使用说明
        - **去水印**：智能去除图片中的水印，保持图片主体完整
        - **溶图打光**：智能溶图打光处理，提升图片光影效果
        - **姿态迁移**：需要同时上传角色图片和姿势参考图
        - **图像优化**：支持 WAN 2.1 和 WAN 2.2 两个模型版本
          - 🎨 处理完成后，默认显示优化后的效果
          - 🔄 使用"显示优化后"和"显示原图"按钮切换查看对比
          - 📥 右键点击图片可以保存到本地
        """)

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
