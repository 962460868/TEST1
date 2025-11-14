"""
图像对比滑块功能测试 - 10种全新方案
基于第一轮测试结果：只有按钮切换能工作，JavaScript 被严重限制
这次尝试更多创新方法，包括使用 Gradio 原生组件
"""

import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import time
import numpy as np

def image_to_base64(image):
    """将 PIL Image 转换为 base64 字符串"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# 创建测试图片
def create_test_images():
    """创建两张不同颜色的测试图片"""
    original = Image.new('RGB', (800, 600), color='#3498db')
    enhanced = Image.new('RGB', (800, 600), color='#2ecc71')

    # 添加文字标识
    draw_orig = ImageDraw.Draw(original)
    draw_enh = ImageDraw.Draw(enhanced)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        font = ImageFont.load_default()

    draw_orig.text((300, 270), "原图", fill='white', font=font)
    draw_enh.text((280, 270), "优化后", fill='white', font=font)

    return original, enhanced

original_img, enhanced_img = create_test_images()
original_b64 = image_to_base64(original_img)
enhanced_b64 = image_to_base64(enhanced_img)

# ========== 方案7: 使用 Gradio Slider 组件 ==========
def create_comparison_v7():
    """方案7: 使用 Gradio 原生 Slider 控制图片显示"""

    def update_image(slider_value):
        """根据滑块值返回对应的图片"""
        if slider_value < 50:
            # 显示优化后的图
            return enhanced_img
        else:
            # 显示原图
            return original_img

    with gr.Blocks() as demo:
        gr.Markdown("### 方案7: Gradio Slider 切换")

        with gr.Row():
            with gr.Column():
                slider = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=0,
                    step=1,
                    label="拖动滑块: 0-49=优化后 | 50-100=原图"
                )
            with gr.Column():
                output_img = gr.Image(value=enhanced_img, label="显示图片")

        slider.change(fn=update_image, inputs=[slider], outputs=[output_img])

    return demo

# ========== 方案8: 使用 Gradio Slider 生成混合图 ==========
def create_comparison_v8():
    """方案8: 使用 Slider 生成半透明混合图"""

    def blend_images(alpha):
        """根据 alpha 值混合两张图片"""
        alpha_val = alpha / 100.0
        # 将 PIL 图转为 numpy 数组
        orig_array = np.array(original_img)
        enh_array = np.array(enhanced_img)

        # 混合
        blended = (1 - alpha_val) * enh_array + alpha_val * orig_array
        blended = blended.astype(np.uint8)

        return Image.fromarray(blended)

    with gr.Blocks() as demo:
        gr.Markdown("### 方案8: Alpha 混合（渐变效果）")

        with gr.Row():
            slider = gr.Slider(
                minimum=0,
                maximum=100,
                value=0,
                label="0=优化后 | 100=原图"
            )

        output_img = gr.Image(value=enhanced_img, label="混合结果")

        slider.change(fn=blend_images, inputs=[slider], outputs=[output_img])

    return demo

# ========== 方案9: 使用 Gradio Radio 按钮 ==========
def create_comparison_v9():
    """方案9: 使用 Radio 单选按钮"""

    def switch_image(choice):
        if choice == "优化后":
            return enhanced_img
        else:
            return original_img

    with gr.Blocks() as demo:
        gr.Markdown("### 方案9: Radio 单选按钮")

        with gr.Row():
            radio = gr.Radio(
                choices=["优化后", "原图"],
                value="优化后",
                label="选择要查看的图片"
            )
            output_img = gr.Image(value=enhanced_img, label="显示图片")

        radio.change(fn=switch_image, inputs=[radio], outputs=[output_img])

    return demo

# ========== 方案10: 使用 Gradio Checkbox 切换 ==========
def create_comparison_v10():
    """方案10: 使用 Checkbox 切换"""

    def toggle_image(checked):
        if checked:
            return original_img
        else:
            return enhanced_img

    with gr.Blocks() as demo:
        gr.Markdown("### 方案10: Checkbox 切换")

        with gr.Row():
            checkbox = gr.Checkbox(
                label="显示原图（不勾选显示优化后）",
                value=False
            )
            output_img = gr.Image(value=enhanced_img, label="显示图片")

        checkbox.change(fn=toggle_image, inputs=[checkbox], outputs=[output_img])

    return demo

# ========== 方案11: 左右并排对比 ==========
def create_comparison_v11():
    """方案11: 左右并排显示，无需切换"""

    with gr.Blocks() as demo:
        gr.Markdown("### 方案11: 左右并排对比（最直观）")

        with gr.Row():
            gr.Image(value=original_img, label="📷 原图")
            gr.Image(value=enhanced_img, label="✨ 优化后")

        gr.Markdown("💡 两张图同时显示，方便直接对比")

    return demo

# ========== 方案12: 上下堆叠对比 ==========
def create_comparison_v12():
    """方案12: 上下堆叠显示"""

    with gr.Blocks() as demo:
        gr.Markdown("### 方案12: 上下堆叠对比")

        with gr.Column():
            gr.Image(value=original_img, label="📷 原图")
            gr.Image(value=enhanced_img, label="✨ 优化后")

        gr.Markdown("💡 上下对比，适合查看整体效果")

    return demo

# ========== 方案13: 使用 Gallery 画廊模式 ==========
def create_comparison_v13():
    """方案13: 使用 Gradio Gallery 组件"""

    with gr.Blocks() as demo:
        gr.Markdown("### 方案13: Gallery 画廊模式")

        gallery = gr.Gallery(
            value=[original_img, enhanced_img],
            label="点击图片查看大图",
            columns=2,
            height="auto"
        )

        gr.Markdown("💡 点击图片可以放大查看")

    return demo

# ========== 方案14: 使用按钮 + 动画过渡 ==========
def create_comparison_v14():
    """方案14: 按钮切换 + 状态显示"""

    current_state = {"showing": "enhanced"}

    def toggle_with_status():
        if current_state["showing"] == "enhanced":
            current_state["showing"] = "original"
            return original_img, "当前显示: 📷 原图", "切换到优化后"
        else:
            current_state["showing"] = "enhanced"
            return enhanced_img, "当前显示: ✨ 优化后", "切换到原图"

    with gr.Blocks() as demo:
        gr.Markdown("### 方案14: 按钮切换 + 状态提示")

        status_text = gr.Markdown("当前显示: ✨ 优化后")
        output_img = gr.Image(value=enhanced_img, label="")
        toggle_btn = gr.Button("切换到原图", variant="primary")

        toggle_btn.click(
            fn=toggle_with_status,
            inputs=[],
            outputs=[output_img, status_text, toggle_btn]
        )

    return demo

# ========== 方案15: 使用 Slider 生成分割图 ==========
def create_comparison_v15():
    """方案15: Slider 控制生成左右分割的对比图"""

    def create_split_image(split_position):
        """创建左右分割的对比图"""
        width, height = original_img.size
        split_x = int(width * split_position / 100)

        # 创建新图片
        result = Image.new('RGB', (width, height))

        # 左边显示原图
        left_part = original_img.crop((0, 0, split_x, height))
        result.paste(left_part, (0, 0))

        # 右边显示优化图
        right_part = enhanced_img.crop((split_x, 0, width, height))
        result.paste(right_part, (split_x, 0))

        # 画分割线
        draw = ImageDraw.Draw(result)
        draw.line([(split_x, 0), (split_x, height)], fill='white', width=3)

        return result

    with gr.Blocks() as demo:
        gr.Markdown("### 方案15: 动态生成分割对比图 ⭐")
        gr.Markdown("💡 这个方案最接近滑动对比效果！")

        slider = gr.Slider(
            minimum=0,
            maximum=100,
            value=50,
            label="拖动滑块调整分割位置 | 左边=原图 | 右边=优化后"
        )

        output_img = gr.Image(value=create_split_image(50), label="对比效果")

        slider.change(fn=create_split_image, inputs=[slider], outputs=[output_img])

    return demo

# ========== 方案16: 使用多个按钮精确控制 ==========
def create_comparison_v16():
    """方案16: 多个按钮精确控制分割位置"""

    def create_split(position):
        width, height = original_img.size
        split_x = int(width * position)

        result = Image.new('RGB', (width, height))

        left_part = original_img.crop((0, 0, split_x, height))
        result.paste(left_part, (0, 0))

        right_part = enhanced_img.crop((split_x, 0, width, height))
        result.paste(right_part, (split_x, 0))

        draw = ImageDraw.Draw(result)
        draw.line([(split_x, 0), (split_x, height)], fill='white', width=3)

        return result

    with gr.Blocks() as demo:
        gr.Markdown("### 方案16: 多按钮精确控制")

        with gr.Row():
            btn_0 = gr.Button("100% 原图")
            btn_25 = gr.Button("75% 原图")
            btn_50 = gr.Button("50/50")
            btn_75 = gr.Button("25% 原图")
            btn_100 = gr.Button("100% 优化")

        output_img = gr.Image(value=create_split(0.5), label="对比效果")

        btn_0.click(fn=lambda: create_split(1.0), outputs=[output_img])
        btn_25.click(fn=lambda: create_split(0.75), outputs=[output_img])
        btn_50.click(fn=lambda: create_split(0.5), outputs=[output_img])
        btn_75.click(fn=lambda: create_split(0.25), outputs=[output_img])
        btn_100.click(fn=lambda: create_split(0.0), outputs=[output_img])

    return demo

# ========== 保留的方案6: 按钮切换（已验证能工作）==========
def create_comparison_v6_working():
    """方案6: 简单按钮切换（已验证可用）"""

    def show_original():
        return original_img

    def show_enhanced():
        return enhanced_img

    with gr.Blocks() as demo:
        gr.Markdown("### 方案6: 按钮切换 ✅（已验证）")
        gr.Markdown("💡 这个方案已验证能工作！")

        with gr.Row():
            btn_enhanced = gr.Button("显示优化后", variant="primary")
            btn_original = gr.Button("显示原图")

        output_img = gr.Image(value=enhanced_img, label="当前图片")

        btn_enhanced.click(fn=show_enhanced, outputs=[output_img])
        btn_original.click(fn=show_original, outputs=[output_img])

    return demo

# ========== 创建测试界面 ==========
def create_test_interface():
    with gr.Blocks(title="图像对比 - 10种新方案测试", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🧪 图像对比功能测试 - 第二轮（10种新方案）

        ## 📊 第一轮测试结果
        - ✅ **方案6（按钮切换）能工作**
        - ❌ 其他5种方案失败（JavaScript 被限制）

        ## 🎯 新策略
        这次使用 **Gradio 原生组件**，避免依赖 JavaScript：
        - 使用 Gradio 的 Slider、Radio、Checkbox 等组件
        - 使用 Python 后端动态生成图片
        - 不依赖 HTML + JavaScript

        ## 🎨 测试图片说明
        - **蓝色 + "原图"文字** = 原图
        - **绿色 + "优化后"文字** = 优化后的图

        ---
        """)

        with gr.Tab("✅ 方案6: 按钮切换（已验证）"):
            create_comparison_v6_working()

        with gr.Tab("方案7: Gradio Slider"):
            gr.Markdown("使用 Gradio 原生 Slider 控制图片切换")
            create_comparison_v7()

        with gr.Tab("方案8: Alpha 混合"):
            gr.Markdown("使用 Slider 控制透明度混合")
            create_comparison_v8()

        with gr.Tab("方案9: Radio 按钮"):
            gr.Markdown("使用单选按钮切换")
            create_comparison_v9()

        with gr.Tab("方案10: Checkbox"):
            gr.Markdown("使用复选框切换")
            create_comparison_v10()

        with gr.Tab("方案11: 左右并排"):
            gr.Markdown("两张图同时显示，最直观")
            create_comparison_v11()

        with gr.Tab("方案12: 上下堆叠"):
            gr.Markdown("上下对比显示")
            create_comparison_v12()

        with gr.Tab("方案13: Gallery 画廊"):
            gr.Markdown("使用 Gradio Gallery 组件")
            create_comparison_v13()

        with gr.Tab("方案14: 按钮+状态"):
            gr.Markdown("按钮切换 + 状态提示")
            create_comparison_v14()

        with gr.Tab("⭐ 方案15: 分割图"):
            gr.Markdown("**推荐方案**：动态生成左右分割的对比图")
            create_comparison_v15()

        with gr.Tab("方案16: 多按钮"):
            gr.Markdown("多个按钮精确控制分割位置")
            create_comparison_v16()

        gr.Markdown("""
        ---
        ## 📝 测试结果记录

        | 方案 | 是否工作 | 用户体验 | 备注 |
        |------|---------|---------|------|
        | 方案6: 按钮切换 | ✅ 已验证 | ⭐⭐⭐ | 简单可靠 |
        | 方案7: Gradio Slider | ⬜ | | |
        | 方案8: Alpha 混合 | ⬜ | | |
        | 方案9: Radio 按钮 | ⬜ | | |
        | 方案10: Checkbox | ⬜ | | |
        | 方案11: 左右并排 | ⬜ | | |
        | 方案12: 上下堆叠 | ⬜ | | |
        | 方案13: Gallery | ⬜ | | |
        | 方案14: 按钮+状态 | ⬜ | | |
        | 方案15: 分割图 ⭐ | ⬜ | | 最推荐 |
        | 方案16: 多按钮 | ⬜ | | |

        ## 🎯 重点测试
        - **方案15（分割图）** - 最接近滑动对比效果
        - **方案8（Alpha混合）** - 渐变效果
        - **方案11（左右并排）** - 最直观

        测试完成后，告诉我哪个方案最好！
        """)

    return demo

if __name__ == "__main__":
    demo = create_test_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7862,  # 使用7862端口，避免冲突
        share=False
    )
