#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像按钮切换性能测试 - 10种优化方案
测试端口：7864
目标：实现秒切换，无延迟
"""

import gradio as gr
import numpy as np
from PIL import Image
import io
import base64
from functools import lru_cache

# ============ 方案1：直接使用 NumPy 数组 ============
def create_test_images_1():
    """生成测试图片 - 返回 NumPy 数组"""
    # 创建原图（蓝色）
    original = np.zeros((400, 600, 3), dtype=np.uint8)
    original[:, :] = [100, 150, 255]  # 蓝色

    # 创建优化图（绿色）
    enhanced = np.zeros((400, 600, 3), dtype=np.uint8)
    enhanced[:, :] = [100, 255, 150]  # 绿色

    return original, enhanced

def process_1():
    original, enhanced = create_test_images_1()
    return enhanced, original, enhanced, "✅ 方案1：使用 NumPy 数组"

# ============ 方案2：小尺寸图片 ============
def create_test_images_2():
    """生成测试图片 - 小尺寸 800x600"""
    original = np.zeros((600, 800, 3), dtype=np.uint8)
    original[:, :] = [100, 150, 255]

    enhanced = np.zeros((600, 800, 3), dtype=np.uint8)
    enhanced[:, :] = [100, 255, 150]

    return original, enhanced

def process_2():
    original, enhanced = create_test_images_2()
    return enhanced, original, enhanced, "✅ 方案2：小尺寸图片 (800x600)"

# ============ 方案3：使用 update() 方法 ============
def process_3():
    original, enhanced = create_test_images_1()
    return enhanced, original, enhanced, "✅ 方案3：使用 gr.update() 方法"

def switch_to_enhanced_3(enhanced):
    return gr.update(value=enhanced)

def switch_to_original_3(original):
    return gr.update(value=original)

# ============ 方案4：预加载到两个 Image 组件 ============
def process_4():
    original, enhanced = create_test_images_1()
    # 返回值：enhanced显示, original隐藏显示, enhanced隐藏显示, 状态
    return enhanced, original, enhanced, "✅ 方案4：双 Image 组件预加载"

# ============ 方案5：使用字典存储 ============
def process_5():
    original, enhanced = create_test_images_1()
    state = {"original": original, "enhanced": enhanced}
    return enhanced, state, "✅ 方案5：字典存储状态"

def switch_5(state, img_type):
    if state and img_type in state:
        return state[img_type]
    return None

# ============ 方案6：限制最大分辨率 ============
def resize_if_large(img, max_size=1024):
    """限制图片最大尺寸"""
    if isinstance(img, np.ndarray):
        h, w = img.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            img_pil = Image.fromarray(img)
            img_pil = img_pil.resize((new_w, new_h), Image.LANCZOS)
            return np.array(img_pil)
    return img

def process_6():
    original, enhanced = create_test_images_1()
    original = resize_if_large(original, 1024)
    enhanced = resize_if_large(enhanced, 1024)
    return enhanced, original, enhanced, "✅ 方案6：限制最大分辨率 1024px"

# ============ 方案7：使用 Tabs 切换 ============
def process_7():
    original, enhanced = create_test_images_1()
    return original, enhanced, "✅ 方案7：使用 Tabs 切换显示"

# ============ 方案8：单个 State 存储列表 ============
def process_8():
    original, enhanced = create_test_images_1()
    return enhanced, [original, enhanced], "✅ 方案8：单个 State 存储列表"

def switch_8(images, index):
    if images and len(images) > index:
        return images[index]
    return None

# ============ 方案9：使用 Gallery 组件 ============
def process_9():
    original, enhanced = create_test_images_1()
    return [enhanced, original], "✅ 方案9：使用 Gallery 显示"

# ============ 方案10：极致优化（NumPy + 低分辨率 + update）============
def create_small_images():
    """生成小尺寸图片 - 400x300"""
    original = np.zeros((300, 400, 3), dtype=np.uint8)
    original[:, :] = [100, 150, 255]

    enhanced = np.zeros((300, 400, 3), dtype=np.uint8)
    enhanced[:, :] = [100, 255, 150]

    return original, enhanced

def process_10():
    original, enhanced = create_small_images()
    return enhanced, original, enhanced, "✅ 方案10：极致优化（400x300 + NumPy + update）"

def fast_switch_10(img):
    return gr.update(value=img)

# ============ 创建界面 ============
def create_interface():
    with gr.Blocks(title="图像按钮切换性能测试 - 10种方案") as demo:
        gr.Markdown("# 🚀 图像按钮切换性能测试 - 10种方案")
        gr.Markdown("**目标：点击按钮秒切换，无延迟**")
        gr.Markdown("**测试方法：** 点击'生成测试图片'后，使用按钮快速切换，观察响应速度")

        # ========== 方案1 ==========
        with gr.Tab("方案1️⃣ NumPy数组"):
            gr.Markdown("### 策略：直接使用 NumPy 数组，避免 PIL 转换")
            with gr.Row():
                with gr.Column():
                    btn_1 = gr.Button("🎯 生成测试图片", variant="primary")
                    status_1 = gr.Textbox(label="状态")
                with gr.Column():
                    output_1 = gr.Image(label="显示区域", show_label=True)
                    with gr.Row():
                        btn_enhanced_1 = gr.Button("🎨 显示优化后", variant="primary")
                        btn_original_1 = gr.Button("📷 显示原图")

            state_orig_1 = gr.State()
            state_enh_1 = gr.State()

            btn_1.click(process_1, outputs=[output_1, state_orig_1, state_enh_1, status_1])
            btn_enhanced_1.click(lambda x: x, inputs=[state_enh_1], outputs=[output_1])
            btn_original_1.click(lambda x: x, inputs=[state_orig_1], outputs=[output_1])

        # ========== 方案2 ==========
        with gr.Tab("方案2️⃣ 小尺寸"):
            gr.Markdown("### 策略：使用较小的图片尺寸 (800x600)")
            with gr.Row():
                with gr.Column():
                    btn_2 = gr.Button("🎯 生成测试图片", variant="primary")
                    status_2 = gr.Textbox(label="状态")
                with gr.Column():
                    output_2 = gr.Image(label="显示区域", show_label=True)
                    with gr.Row():
                        btn_enhanced_2 = gr.Button("🎨 显示优化后", variant="primary")
                        btn_original_2 = gr.Button("📷 显示原图")

            state_orig_2 = gr.State()
            state_enh_2 = gr.State()

            btn_2.click(process_2, outputs=[output_2, state_orig_2, state_enh_2, status_2])
            btn_enhanced_2.click(lambda x: x, inputs=[state_enh_2], outputs=[output_2])
            btn_original_2.click(lambda x: x, inputs=[state_orig_2], outputs=[output_2])

        # ========== 方案3 ==========
        with gr.Tab("方案3️⃣ gr.update()"):
            gr.Markdown("### 策略：使用 gr.update() 方法更新组件")
            with gr.Row():
                with gr.Column():
                    btn_3 = gr.Button("🎯 生成测试图片", variant="primary")
                    status_3 = gr.Textbox(label="状态")
                with gr.Column():
                    output_3 = gr.Image(label="显示区域", show_label=True)
                    with gr.Row():
                        btn_enhanced_3 = gr.Button("🎨 显示优化后", variant="primary")
                        btn_original_3 = gr.Button("📷 显示原图")

            state_orig_3 = gr.State()
            state_enh_3 = gr.State()

            btn_3.click(process_3, outputs=[output_3, state_orig_3, state_enh_3, status_3])
            btn_enhanced_3.click(switch_to_enhanced_3, inputs=[state_enh_3], outputs=[output_3])
            btn_original_3.click(switch_to_original_3, inputs=[state_orig_3], outputs=[output_3])

        # ========== 方案4 ==========
        with gr.Tab("方案4️⃣ 双Image预加载"):
            gr.Markdown("### 策略：使用两个 Image 组件预加载，通过 visible 切换")
            with gr.Row():
                with gr.Column():
                    btn_4 = gr.Button("🎯 生成测试图片", variant="primary")
                    status_4 = gr.Textbox(label="状态")
                    with gr.Row():
                        btn_show_enh_4 = gr.Button("🎨 显示优化后", variant="primary")
                        btn_show_orig_4 = gr.Button("📷 显示原图")
                with gr.Column():
                    img_enh_4 = gr.Image(label="优化后", show_label=True, visible=True)
                    img_orig_4 = gr.Image(label="原图", show_label=True, visible=False)

            btn_4.click(
                lambda: create_test_images_1(),
                outputs=[img_enh_4, img_orig_4]
            ).then(
                lambda: "✅ 方案4：双 Image 组件预加载",
                outputs=[status_4]
            )

            btn_show_enh_4.click(
                lambda: [gr.update(visible=True), gr.update(visible=False)],
                outputs=[img_enh_4, img_orig_4]
            )
            btn_show_orig_4.click(
                lambda: [gr.update(visible=False), gr.update(visible=True)],
                outputs=[img_enh_4, img_orig_4]
            )

        # ========== 方案5 ==========
        with gr.Tab("方案5️⃣ 字典存储"):
            gr.Markdown("### 策略：使用字典存储状态")
            with gr.Row():
                with gr.Column():
                    btn_5 = gr.Button("🎯 生成测试图片", variant="primary")
                    status_5 = gr.Textbox(label="状态")
                with gr.Column():
                    output_5 = gr.Image(label="显示区域", show_label=True)
                    with gr.Row():
                        btn_enhanced_5 = gr.Button("🎨 显示优化后", variant="primary")
                        btn_original_5 = gr.Button("📷 显示原图")

            state_5 = gr.State()

            btn_5.click(process_5, outputs=[output_5, state_5, status_5])
            btn_enhanced_5.click(
                lambda s: switch_5(s, "enhanced"),
                inputs=[state_5],
                outputs=[output_5]
            )
            btn_original_5.click(
                lambda s: switch_5(s, "original"),
                inputs=[state_5],
                outputs=[output_5]
            )

        # ========== 方案6 ==========
        with gr.Tab("方案6️⃣ 限制分辨率"):
            gr.Markdown("### 策略：限制最大分辨率为 1024px")
            with gr.Row():
                with gr.Column():
                    btn_6 = gr.Button("🎯 生成测试图片", variant="primary")
                    status_6 = gr.Textbox(label="状态")
                with gr.Column():
                    output_6 = gr.Image(label="显示区域", show_label=True)
                    with gr.Row():
                        btn_enhanced_6 = gr.Button("🎨 显示优化后", variant="primary")
                        btn_original_6 = gr.Button("📷 显示原图")

            state_orig_6 = gr.State()
            state_enh_6 = gr.State()

            btn_6.click(process_6, outputs=[output_6, state_orig_6, state_enh_6, status_6])
            btn_enhanced_6.click(lambda x: x, inputs=[state_enh_6], outputs=[output_6])
            btn_original_6.click(lambda x: x, inputs=[state_orig_6], outputs=[output_6])

        # ========== 方案7 ==========
        with gr.Tab("方案7️⃣ Tabs切换"):
            gr.Markdown("### 策略：使用 Tabs 组件切换显示")
            btn_7 = gr.Button("🎯 生成测试图片", variant="primary")
            status_7 = gr.Textbox(label="状态")

            with gr.Tabs():
                with gr.Tab("🎨 优化后"):
                    output_enh_7 = gr.Image(label="优化后", show_label=False)
                with gr.Tab("📷 原图"):
                    output_orig_7 = gr.Image(label="原图", show_label=False)

            btn_7.click(process_7, outputs=[output_orig_7, output_enh_7, status_7])

        # ========== 方案8 ==========
        with gr.Tab("方案8️⃣ 列表存储"):
            gr.Markdown("### 策略：单个 State 存储列表")
            with gr.Row():
                with gr.Column():
                    btn_8 = gr.Button("🎯 生成测试图片", variant="primary")
                    status_8 = gr.Textbox(label="状态")
                with gr.Column():
                    output_8 = gr.Image(label="显示区域", show_label=True)
                    with gr.Row():
                        btn_enhanced_8 = gr.Button("🎨 显示优化后", variant="primary")
                        btn_original_8 = gr.Button("📷 显示原图")

            state_8 = gr.State()

            btn_8.click(process_8, outputs=[output_8, state_8, status_8])
            btn_enhanced_8.click(lambda s: switch_8(s, 1), inputs=[state_8], outputs=[output_8])
            btn_original_8.click(lambda s: switch_8(s, 0), inputs=[state_8], outputs=[output_8])

        # ========== 方案9 ==========
        with gr.Tab("方案9️⃣ Gallery组件"):
            gr.Markdown("### 策略：使用 Gallery 组件显示")
            gr.Markdown("**说明：** 第一张是优化后，第二张是原图")
            btn_9 = gr.Button("🎯 生成测试图片", variant="primary")
            status_9 = gr.Textbox(label="状态")
            gallery_9 = gr.Gallery(label="图片对比", columns=2, rows=1, height="auto")

            btn_9.click(process_9, outputs=[gallery_9, status_9])

        # ========== 方案10 ==========
        with gr.Tab("方案🔟 极致优化"):
            gr.Markdown("### 策略：组合优化（400x300 + NumPy + gr.update）")
            with gr.Row():
                with gr.Column():
                    btn_10 = gr.Button("🎯 生成测试图片", variant="primary")
                    status_10 = gr.Textbox(label="状态")
                with gr.Column():
                    output_10 = gr.Image(label="显示区域", show_label=True)
                    with gr.Row():
                        btn_enhanced_10 = gr.Button("🎨 显示优化后", variant="primary")
                        btn_original_10 = gr.Button("📷 显示原图")

            state_orig_10 = gr.State()
            state_enh_10 = gr.State()

            btn_10.click(process_10, outputs=[output_10, state_orig_10, state_enh_10, status_10])
            btn_enhanced_10.click(fast_switch_10, inputs=[state_enh_10], outputs=[output_10])
            btn_original_10.click(fast_switch_10, inputs=[state_orig_10], outputs=[output_10])

        # ========== 测试说明 ==========
        with gr.Accordion("📖 测试说明", open=False):
            gr.Markdown("""
            ## 测试方法

            1. **选择一个方案标签页**
            2. **点击"生成测试图片"按钮**
            3. **快速点击"显示优化后"和"显示原图"按钮**
            4. **观察切换速度**：
               - ✅ **成功**：切换立即响应，无延迟
               - ❌ **失败**：切换有明显延迟（>0.5秒）

            ## 方案说明

            | 方案 | 策略 | 预期效果 |
            |------|------|----------|
            | 1️⃣ | 使用 NumPy 数组 | 避免 PIL 转换开销 |
            | 2️⃣ | 小尺寸图片 (800x600) | 减少数据传输量 |
            | 3️⃣ | gr.update() 方法 | 优化更新机制 |
            | 4️⃣ | 双 Image 预加载 | 通过 visible 切换，无需重新加载 |
            | 5️⃣ | 字典存储 | 统一状态管理 |
            | 6️⃣ | 限制分辨率 1024px | 平衡质量和性能 |
            | 7️⃣ | Tabs 切换 | 利用 Gradio 原生切换 |
            | 8️⃣ | 列表存储 | 简化状态管理 |
            | 9️⃣ | Gallery 组件 | 同时显示两张图 |
            | 🔟 | 极致优化 | 多种优化组合 |

            ## 评估标准

            - **响应速度**：按钮点击后的显示速度
            - **稳定性**：是否每次都能正常切换
            - **用户体验**：操作是否流畅自然

            ## 注意事项

            - 测试使用的是简单的纯色图片
            - 实际应用中图片可能更大更复杂
            - 选择最快最稳定的方案
            """)

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7864,
        share=False,
        show_error=True
    )
    print("\n✅ 测试服务器启动成功！")
    print("📍 访问地址：http://43.154.84.14:7864")
    print("🎯 测试目标：找到秒切换、无延迟的方案\n")
