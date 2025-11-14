#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像队列UI优化测试 - 10种方案
测试端口：7865
目标：解决图像对比卡顿、刷新闪烁、按钮无响应问题
"""

import gradio as gr
import numpy as np
from PIL import Image
import io
import base64
import uuid
import os
import tempfile
from pathlib import Path

# 创建临时目录
TEMP_DIR = Path(tempfile.mkdtemp())

# 模拟队列数据
def create_test_images(count=3):
    """生成测试图片数据"""
    results = []
    for i in range(count):
        # 创建原图（蓝色）
        original = np.zeros((400, 600, 3), dtype=np.uint8)
        original[:, :] = [100 + i*20, 150 + i*10, 255 - i*30]

        # 创建优化图（绿色）
        enhanced = np.zeros((400, 600, 3), dtype=np.uint8)
        enhanced[:, :] = [100 + i*15, 255 - i*20, 150 + i*25]

        results.append({
            "id": f"test_{i+1}",
            "original": original,
            "enhanced": enhanced,
            "status": "completed"
        })

    return results

# ========== 方案1：Gallery画廊组件 ==========
def method1_generate():
    """方案1：使用Gallery组件显示所有图片"""
    results = create_test_images(3)
    images = []
    labels = []

    for item in results:
        # 添加原图
        images.append(item["original"])
        labels.append(f"#{item['id']} - 原图")

        # 添加优化图
        images.append(item["enhanced"])
        labels.append(f"#{item['id']} - 优化后")

    return images

# ========== 方案2：Accordion折叠面板 ==========
def method2_generate():
    """方案2：每个结果一个折叠面板"""
    results = create_test_images(3)
    return results

# ========== 方案3：使用Tabs标签页 ==========
def method3_generate():
    """方案3：每个结果一个Tab"""
    results = create_test_images(3)
    outputs = []
    for item in results:
        outputs.extend([item["original"], item["enhanced"]])
    return outputs

# ========== 方案4：Radio选择器 ==========
def method4_switch(image_id, view_type, queue_data):
    """方案4：使用Radio切换原图/优化图"""
    if not queue_data or image_id >= len(queue_data):
        return None

    item = queue_data[image_id]
    if view_type == "原图":
        return item["original"]
    else:
        return item["enhanced"]

def method4_generate():
    """生成队列数据"""
    results = create_test_images(3)
    return results

# ========== 方案5：独立显示区域 ==========
def method5_show_original(idx, queue_data):
    """方案5：点击查看原图"""
    if queue_data and idx < len(queue_data):
        return queue_data[idx]["original"]
    return None

def method5_show_enhanced(idx, queue_data):
    """方案5：显示优化图"""
    if queue_data and idx < len(queue_data):
        return queue_data[idx]["enhanced"]
    return None

def method5_generate():
    """生成队列"""
    return create_test_images(3)

# ========== 方案6：降低刷新频率 ==========
def method6_render_static_html(queue_data):
    """方案6：生成静态HTML，降低刷新频率"""
    if not queue_data:
        return "<div style='text-align:center; padding:40px; color:#888;'>暂无图片</div>"

    html = "<div style='display: flex; flex-direction: column; gap: 20px;'>"

    for item in queue_data:
        # 只显示优化图，原图通过hover显示
        enhanced_img = Image.fromarray(item["enhanced"])
        buffer = io.BytesIO()
        enhanced_img.save(buffer, format='PNG')
        enhanced_b64 = base64.b64encode(buffer.getvalue()).decode()

        html += f"""
        <div style='border: 2px solid #32CD32; border-radius: 8px; padding: 15px; background: #f9f9f9;'>
            <div style='font-weight: bold; margin-bottom: 10px;'>🔖 {item['id']}</div>
            <img src='data:image/png;base64,{enhanced_b64}'
                 style='max-width: 100%; height: auto; border-radius: 4px;' />
            <div style='margin-top: 10px; font-size: 14px; color: #666;'>
                ✅ 已完成优化 | 原图尺寸: 600x400
            </div>
        </div>
        """

    html += "</div>"
    return html

def method6_generate():
    """生成队列"""
    return create_test_images(3)

# ========== 方案7：使用临时文件URL ==========
def method7_generate():
    """方案7：保存为临时文件，使用URL"""
    results = create_test_images(3)
    file_paths = []

    for item in results:
        # 保存原图
        orig_img = Image.fromarray(item["original"])
        orig_path = TEMP_DIR / f"{item['id']}_original.png"
        orig_img.save(orig_path)

        # 保存优化图
        enh_img = Image.fromarray(item["enhanced"])
        enh_path = TEMP_DIR / f"{item['id']}_enhanced.png"
        enh_img.save(enh_path)

        file_paths.append({
            "id": item["id"],
            "original": str(orig_path),
            "enhanced": str(enh_path)
        })

    return file_paths

def method7_render(file_paths):
    """渲染文件路径为HTML"""
    if not file_paths:
        return "<div style='text-align:center; padding:40px; color:#888;'>暂无图片</div>"

    html = "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;'>"

    for item in file_paths:
        html += f"""
        <div style='border: 2px solid #32CD32; border-radius: 8px; padding: 10px; background: #fff;'>
            <div style='font-weight: bold; margin-bottom: 10px;'>#{item['id']}</div>
            <div style='font-size: 12px; color: #666;'>
                ✅ 已保存到临时文件<br>
                📂 {item['enhanced']}
            </div>
        </div>
        """

    html += "</div>"
    return html

# ========== 方案8：分页显示 ==========
def method8_generate(page=1, per_page=2):
    """方案8：分页显示结果"""
    all_results = create_test_images(5)  # 生成5个结果

    start = (page - 1) * per_page
    end = start + per_page

    current_page = all_results[start:end]
    total_pages = (len(all_results) + per_page - 1) // per_page

    return current_page, f"第 {page}/{total_pages} 页"

# ========== 方案9：DataFrame列表 ==========
def method9_generate():
    """方案9：使用文本列表，点击查看大图"""
    results = create_test_images(3)

    # 创建DataFrame数据
    data = []
    for item in results:
        data.append([
            item['id'],
            "已完成",
            "600x400",
            "点击查看"
        ])

    return data, results

def method9_show(evt: gr.SelectData, queue_data):
    """点击行显示图片"""
    if queue_data and evt.index[0] < len(queue_data):
        item = queue_data[evt.index[0]]
        return item["original"], item["enhanced"]
    return None, None

# ========== 方案10：极简模式 ==========
def method10_generate():
    """方案10：只显示最新结果，其他折叠"""
    results = create_test_images(5)

    # 最新的
    latest = results[-1]

    # 历史记录（只显示信息）
    history_html = "<div style='margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px;'>"
    history_html += "<div style='font-weight: bold; margin-bottom: 10px;'>📜 历史记录</div>"

    for item in results[:-1]:
        history_html += f"""
        <div style='padding: 8px; border-bottom: 1px solid #ddd;'>
            🔖 {item['id']} - ✅ 已完成
        </div>
        """

    history_html += "</div>"

    return latest["original"], latest["enhanced"], history_html

# ========== 创建界面 ==========
def create_interface():
    with gr.Blocks(title="图像队列UI优化测试", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🚀 图像队列UI优化测试 - 10种方案")
        gr.Markdown("**目标**：解决图像对比卡顿、刷新闪烁、按钮无响应问题")

        with gr.Tabs():
            # ========== 方案1 ==========
            with gr.Tab("方案1️⃣ Gallery画廊"):
                gr.Markdown("### 策略：使用Gradio原生Gallery组件")
                gr.Markdown("优点：原生支持，无刷新问题；缺点：原图和优化图分开显示")

                btn1 = gr.Button("生成测试结果", variant="primary")
                gallery1 = gr.Gallery(label="处理结果", columns=2, rows=3, height="auto")

                btn1.click(method1_generate, outputs=[gallery1])

            # ========== 方案2 ==========
            with gr.Tab("方案2️⃣ Accordion折叠"):
                gr.Markdown("### 策略：每个结果一个折叠面板，默认只展开最新")
                gr.Markdown("优点：节省空间，按需展开；缺点：需要手动展开查看")

                btn2 = gr.Button("生成测试结果", variant="primary")

                with gr.Accordion("🔖 test_1", open=False):
                    with gr.Row():
                        img2_1_orig = gr.Image(label="原图", show_label=True)
                        img2_1_enh = gr.Image(label="优化后", show_label=True)

                with gr.Accordion("🔖 test_2", open=False):
                    with gr.Row():
                        img2_2_orig = gr.Image(label="原图", show_label=True)
                        img2_2_enh = gr.Image(label="优化后", show_label=True)

                with gr.Accordion("🔖 test_3", open=True):
                    with gr.Row():
                        img2_3_orig = gr.Image(label="原图", show_label=True)
                        img2_3_enh = gr.Image(label="优化后", show_label=True)

                def update_accordion():
                    results = method2_generate()
                    outputs = []
                    for item in results:
                        outputs.extend([item["original"], item["enhanced"]])
                    return outputs

                btn2.click(
                    update_accordion,
                    outputs=[img2_1_orig, img2_1_enh, img2_2_orig, img2_2_enh, img2_3_orig, img2_3_enh]
                )

            # ========== 方案3 ==========
            with gr.Tab("方案3️⃣ Tabs标签页"):
                gr.Markdown("### 策略：每个结果一个Tab标签页")
                gr.Markdown("优点：清晰分离，无干扰；缺点：占用水平空间")

                btn3 = gr.Button("生成测试结果", variant="primary")

                with gr.Tabs():
                    with gr.Tab("🔖 test_1"):
                        with gr.Row():
                            img3_1_orig = gr.Image(label="原图", show_label=True)
                            img3_1_enh = gr.Image(label="优化后", show_label=True)

                    with gr.Tab("🔖 test_2"):
                        with gr.Row():
                            img3_2_orig = gr.Image(label="原图", show_label=True)
                            img3_2_enh = gr.Image(label="优化后", show_label=True)

                    with gr.Tab("🔖 test_3"):
                        with gr.Row():
                            img3_3_orig = gr.Image(label="原图", show_label=True)
                            img3_3_enh = gr.Image(label="优化后", show_label=True)

                btn3.click(
                    method3_generate,
                    outputs=[img3_1_orig, img3_1_enh, img3_2_orig, img3_2_enh, img3_3_orig, img3_3_enh]
                )

            # ========== 方案4 ==========
            with gr.Tab("方案4️⃣ Radio切换"):
                gr.Markdown("### 策略：使用Radio选择查看原图或优化图")
                gr.Markdown("优点：单一显示区，响应快；缺点：无法同时对比")

                btn4 = gr.Button("生成测试结果", variant="primary")
                queue4 = gr.State()

                with gr.Row():
                    with gr.Column(scale=1):
                        image_selector = gr.Radio(
                            choices=["图片1", "图片2", "图片3"],
                            value="图片1",
                            label="选择图片"
                        )
                        view_type = gr.Radio(
                            choices=["原图", "优化后"],
                            value="优化后",
                            label="查看"
                        )

                    with gr.Column(scale=3):
                        display4 = gr.Image(label="显示区域", show_label=True)

                def on_generate4():
                    data = method4_generate()
                    return data, data[0]["enhanced"]

                def on_switch4(img_id, view, queue):
                    idx = ["图片1", "图片2", "图片3"].index(img_id)
                    return method4_switch(idx, view, queue)

                btn4.click(on_generate4, outputs=[queue4, display4])
                image_selector.change(on_switch4, inputs=[image_selector, view_type, queue4], outputs=[display4])
                view_type.change(on_switch4, inputs=[image_selector, view_type, queue4], outputs=[display4])

            # ========== 方案5 ==========
            with gr.Tab("方案5️⃣ 独立显示"):
                gr.Markdown("### 策略：左侧列表，右侧显示原图和优化图")
                gr.Markdown("优点：布局清晰，易于对比；缺点：需要选择")

                btn5 = gr.Button("生成测试结果", variant="primary")
                queue5 = gr.State()

                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("#### 结果列表")
                        btn5_1 = gr.Button("📷 图片1")
                        btn5_2 = gr.Button("📷 图片2")
                        btn5_3 = gr.Button("📷 图片3")

                    with gr.Column(scale=4):
                        with gr.Row():
                            img5_orig = gr.Image(label="原图", show_label=True)
                            img5_enh = gr.Image(label="优化后", show_label=True)

                btn5.click(method5_generate, outputs=[queue5])
                btn5_1.click(lambda q: (method5_show_original(0, q), method5_show_enhanced(0, q)),
                            inputs=[queue5], outputs=[img5_orig, img5_enh])
                btn5_2.click(lambda q: (method5_show_original(1, q), method5_show_enhanced(1, q)),
                            inputs=[queue5], outputs=[img5_orig, img5_enh])
                btn5_3.click(lambda q: (method5_show_original(2, q), method5_show_enhanced(2, q)),
                            inputs=[queue5], outputs=[img5_orig, img5_enh])

            # ========== 方案6 ==========
            with gr.Tab("方案6️⃣ 降低刷新"):
                gr.Markdown("### 策略：生成静态HTML，降低刷新频率（10秒）")
                gr.Markdown("优点：减少刷新卡顿；缺点：更新不及时")

                btn6 = gr.Button("生成测试结果", variant="primary")
                queue6 = gr.State()
                display6 = gr.HTML(value="<div style='text-align:center; padding:40px; color:#888;'>暂无图片</div>")

                def on_generate6():
                    data = method6_generate()
                    html = method6_render_static_html(data)
                    return data, html

                btn6.click(on_generate6, outputs=[queue6, display6])

            # ========== 方案7 ==========
            with gr.Tab("方案7️⃣ 文件URL"):
                gr.Markdown("### 策略：保存为临时文件，使用文件URL而非base64")
                gr.Markdown("优点：避免base64编码，HTML更小；缺点：需要文件管理")

                btn7 = gr.Button("生成测试结果", variant="primary")

                with gr.Row():
                    img7_1 = gr.Image(label="test_1 - 优化后", show_label=True)
                    img7_2 = gr.Image(label="test_2 - 优化后", show_label=True)
                    img7_3 = gr.Image(label="test_3 - 优化后", show_label=True)

                def on_generate7():
                    file_paths = method7_generate()
                    images = []
                    for item in file_paths:
                        images.append(item["enhanced"])
                    return images

                btn7.click(on_generate7, outputs=[img7_1, img7_2, img7_3])

            # ========== 方案8 ==========
            with gr.Tab("方案8️⃣ 分页显示"):
                gr.Markdown("### 策略：分页显示结果，每页2个")
                gr.Markdown("优点：减少单页加载量；缺点：需要翻页")

                page_num = gr.State(value=1)
                queue8 = gr.State()

                with gr.Row():
                    prev_btn = gr.Button("⬅️ 上一页")
                    page_info = gr.Textbox(label="页码", value="第 1/3 页", interactive=False)
                    next_btn = gr.Button("➡️ 下一页")

                with gr.Row():
                    img8_1_orig = gr.Image(label="原图", show_label=True)
                    img8_1_enh = gr.Image(label="优化后", show_label=True)

                with gr.Row():
                    img8_2_orig = gr.Image(label="原图", show_label=True)
                    img8_2_enh = gr.Image(label="优化后", show_label=True)

                def show_page(page):
                    current, info = method8_generate(page, 2)
                    outputs = [page, info]
                    for item in current:
                        outputs.extend([item["original"], item["enhanced"]])
                    # 如果当前页不足2个，填充None
                    while len(outputs) < 6:
                        outputs.append(None)
                    return outputs

                def next_page(page):
                    return show_page(min(page + 1, 3))

                def prev_page(page):
                    return show_page(max(page - 1, 1))

                demo.load(show_page, inputs=[page_num],
                         outputs=[page_num, page_info, img8_1_orig, img8_1_enh, img8_2_orig, img8_2_enh])
                next_btn.click(next_page, inputs=[page_num],
                              outputs=[page_num, page_info, img8_1_orig, img8_1_enh, img8_2_orig, img8_2_enh])
                prev_btn.click(prev_page, inputs=[page_num],
                              outputs=[page_num, page_info, img8_1_orig, img8_1_enh, img8_2_orig, img8_2_enh])

            # ========== 方案9 ==========
            with gr.Tab("方案9️⃣ DataFrame列表"):
                gr.Markdown("### 策略：使用DataFrame显示列表，点击查看大图")
                gr.Markdown("优点：轻量级列表；缺点：需要点击查看")

                btn9 = gr.Button("生成测试结果", variant="primary")
                queue9 = gr.State()

                dataframe9 = gr.Dataframe(
                    headers=["ID", "状态", "尺寸", "操作"],
                    datatype=["str", "str", "str", "str"],
                    label="处理结果列表"
                )

                with gr.Row():
                    img9_orig = gr.Image(label="原图", show_label=True)
                    img9_enh = gr.Image(label="优化后", show_label=True)

                def on_generate9():
                    data, queue = method9_generate()
                    return data, queue

                btn9.click(on_generate9, outputs=[dataframe9, queue9])
                dataframe9.select(method9_show, inputs=[queue9], outputs=[img9_orig, img9_enh])

            # ========== 方案10 ==========
            with gr.Tab("方案🔟 极简模式"):
                gr.Markdown("### 策略：只显示最新结果，历史记录折叠")
                gr.Markdown("优点：界面简洁，性能最优；缺点：历史查看不便")

                btn10 = gr.Button("生成测试结果", variant="primary")

                gr.Markdown("#### 📊 最新结果")
                with gr.Row():
                    img10_orig = gr.Image(label="原图", show_label=True)
                    img10_enh = gr.Image(label="优化后", show_label=True)

                history10 = gr.HTML(value="<div style='text-align:center; padding:20px; color:#888;'>暂无历史</div>")

                btn10.click(method10_generate, outputs=[img10_orig, img10_enh, history10])

        # ========== 测试说明 ==========
        with gr.Accordion("📖 测试说明", open=False):
            gr.Markdown("""
            ## 测试方法

            1. **逐个测试每个方案**
            2. **观察以下指标**：
               - 🚀 响应速度：点击按钮后的响应时间
               - 🎨 刷新流畅度：是否有闪烁、黑白切换
               - 🖱️ 交互性：按钮是否可点击
               - 📊 多结果表现：多个结果时的性能
               - 💡 用户体验：操作是否方便直观

            ## 方案对比

            | 方案 | 主要策略 | 适用场景 |
            |------|----------|----------|
            | 1️⃣ | Gallery画廊 | 需要快速浏览所有结果 |
            | 2️⃣ | Accordion折叠 | 结果较多，节省空间 |
            | 3️⃣ | Tabs标签页 | 结果较少，详细对比 |
            | 4️⃣ | Radio切换 | 单一视图，快速切换 |
            | 5️⃣ | 独立显示 | 需要详细对比原图和优化图 |
            | 6️⃣ | 降低刷新 | 减少刷新导致的卡顿 |
            | 7️⃣ | 文件URL | 大图片，避免base64 |
            | 8️⃣ | 分页显示 | 结果很多，分批查看 |
            | 9️⃣ | DataFrame列表 | 轻量级列表展示 |
            | 🔟 | 极简模式 | 关注最新结果，性能优先 |

            ## 评估标准

            - ⭐⭐⭐⭐⭐ 完美：无卡顿，响应快，交互好
            - ⭐⭐⭐⭐ 优秀：轻微延迟，基本流畅
            - ⭐⭐⭐ 良好：有延迟但可接受
            - ⭐⭐ 一般：明显卡顿
            - ⭐ 差：严重卡顿或无法使用

            ## 推荐顺序

            1. **先测试方案1、4、5、7** - 这些使用Gradio原生组件，理论上最稳定
            2. **再测试方案2、3、8、10** - 这些有特定的布局优化
            3. **最后测试方案6、9** - 这些是特殊策略

            测试完成后，请告知哪个方案表现最好！
            """)

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7865,
        share=False,
        show_error=True
    )
    print("\n✅ UI优化测试服务器启动成功！")
    print("📍 访问地址：http://43.154.84.14:7865")
    print("🎯 测试目标：找到最流畅、无卡顿的UI方案\n")
