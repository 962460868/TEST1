"""
图像对比滑块功能测试 - 6种不同实现方案
每个方案都是独立的，可以单独测试哪个在 Gradio 中能正常工作
"""

import gradio as gr
from PIL import Image
import io
import base64
import time

def image_to_base64(image):
    """将 PIL Image 转换为 base64 字符串"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# 创建两张测试图片
def create_test_images():
    """创建两张不同颜色的测试图片"""
    # 原图 - 蓝色
    original = Image.new('RGB', (800, 600), color='#3498db')
    # 优化图 - 绿色
    enhanced = Image.new('RGB', (800, 600), color='#2ecc71')
    return original, enhanced

original_img, enhanced_img = create_test_images()
original_b64 = image_to_base64(original_img)
enhanced_b64 = image_to_base64(enhanced_img)

# ========== 方案 1: 使用 HTML Range Input ==========
def create_comparison_v1():
    """方案1: 使用原生 HTML range input 控制"""
    unique_id = f"v1_{int(time.time() * 1000)}"

    html = f"""
    <div style="width: 100%; max-width: 800px; margin: 20px auto;">
        <h3>方案1: HTML Range Input</h3>
        <div id="container-{unique_id}" style="position: relative; width: 100%; height: 400px; overflow: hidden; border-radius: 8px;">
            <img src="{enhanced_b64}" style="position: absolute; width: 100%; height: 100%; object-fit: cover;">
            <div id="overlay-{unique_id}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; clip-path: inset(0 100% 0 0);">
                <img src="{original_b64}" style="width: 100%; height: 100%; object-fit: cover;">
            </div>
            <div id="divider-{unique_id}" style="position: absolute; top: 0; left: 0%; width: 3px; height: 100%; background: white; box-shadow: 0 0 5px rgba(0,0,0,0.5);"></div>
        </div>
        <input type="range" id="slider-{unique_id}" min="0" max="100" value="0"
               style="width: 100%; margin-top: 10px;">
        <p style="text-align: center; color: #666;">拖动滑块: 0% = 优化后 | 100% = 原图</p>
    </div>

    <script>
        (function() {{
            const slider = document.getElementById('slider-{unique_id}');
            const overlay = document.getElementById('overlay-{unique_id}');
            const divider = document.getElementById('divider-{unique_id}');

            if (slider && overlay && divider) {{
                slider.addEventListener('input', function() {{
                    const value = this.value;
                    const clipValue = 100 - value;
                    overlay.style.clipPath = `inset(0 ${{clipValue}}% 0 0)`;
                    divider.style.left = value + '%';
                }});
            }}
        }})();
    </script>
    """
    return html

# ========== 方案 2: 使用两个并排图片 + Opacity ==========
def create_comparison_v2():
    """方案2: 使用 opacity 而不是 clip-path"""
    unique_id = f"v2_{int(time.time() * 1000)}"

    html = f"""
    <div style="width: 100%; max-width: 800px; margin: 20px auto;">
        <h3>方案2: Opacity 控制</h3>
        <div style="position: relative; width: 100%; height: 400px; border-radius: 8px; overflow: hidden;">
            <img src="{enhanced_b64}" style="position: absolute; width: 100%; height: 100%; object-fit: cover;">
            <img id="top-{unique_id}" src="{original_b64}" style="position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0;">
        </div>
        <input type="range" id="slider-{unique_id}" min="0" max="100" value="0"
               style="width: 100%; margin-top: 10px;">
        <p style="text-align: center; color: #666;">拖动滑块: 0% = 优化后 | 100% = 原图</p>
    </div>

    <script>
        const slider2 = document.getElementById('slider-{unique_id}');
        const topImg2 = document.getElementById('top-{unique_id}');
        if (slider2 && topImg2) {{
            slider2.oninput = function() {{
                topImg2.style.opacity = this.value / 100;
            }};
        }}
    </script>
    """
    return html

# ========== 方案 3: 使用 iframe（完全隔离）==========
def create_comparison_v3():
    """方案3: 使用 iframe 完全隔离 JavaScript"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 20px; font-family: Arial; }}
            .container {{ position: relative; width: 100%%; max-width: 800px; height: 400px; margin: 0 auto; }}
            .container img {{ position: absolute; width: 100%%; height: 100%%; object-fit: cover; }}
            .overlay {{ position: absolute; top: 0; left: 0; width: 100%%; height: 100%%; clip-path: inset(0 100%% 0 0); }}
            .divider {{ position: absolute; top: 0; left: 0; width: 3px; height: 100%%; background: white; }}
            input[type="range"] {{ width: 100%%; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <h3>方案3: iframe 隔离</h3>
        <div class="container">
            <img src="{enhanced_b64}">
            <div class="overlay"><img src="{original_b64}"></div>
            <div class="divider"></div>
        </div>
        <input type="range" min="0" max="100" value="0" id="slider">
        <p style="text-align: center; color: #666;">拖动滑块对比</p>

        <script>
            const slider = document.getElementById('slider');
            const overlay = document.querySelector('.overlay');
            const divider = document.querySelector('.divider');

            slider.addEventListener('input', function() {{
                const value = this.value;
                overlay.style.clipPath = `inset(0 ${{100 - value}}% 0 0)`;
                divider.style.left = value + '%';
            }});
        </script>
    </body>
    </html>
    """

    iframe_html = f"""
    <div style="width: 100%; max-width: 800px; margin: 20px auto;">
        <iframe srcdoc='{html_content.replace("'", "&apos;")}'
                style="width: 100%; height: 500px; border: 1px solid #ddd; border-radius: 8px;">
        </iframe>
    </div>
    """
    return iframe_html

# ========== 方案 4: 纯 CSS（无 JavaScript）==========
def create_comparison_v4():
    """方案4: 纯 CSS 实现，使用 :hover"""
    unique_id = f"v4_{int(time.time() * 1000)}"

    html = f"""
    <div style="width: 100%; max-width: 800px; margin: 20px auto;">
        <h3>方案4: 纯 CSS（鼠标悬停）</h3>
        <div style="position: relative; width: 100%; height: 400px; border-radius: 8px; overflow: hidden;">
            <img src="{enhanced_b64}" style="width: 100%; height: 100%; object-fit: cover;">
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                        background: url('{original_b64}'); background-size: cover;
                        clip-path: inset(0 50% 0 0); transition: clip-path 0.3s ease;">
            </div>
        </div>
        <p style="text-align: center; color: #666;">鼠标移动到图片上（仅演示，无滑块）</p>
    </div>

    <style>
        #container-{unique_id}:hover .overlay-{unique_id} {{
            clip-path: inset(0 0% 0 0) !important;
        }}
    </style>
    """
    return html

# ========== 方案 5: 使用 data URI + 完整 HTML ==========
def create_comparison_v5():
    """方案5: 使用完整的 data URI 嵌入"""
    unique_id = f"v5_{int(time.time() * 1000)}"

    html = f"""
    <div style="width: 100%; max-width: 800px; margin: 20px auto;">
        <h3>方案5: Data URI 完整嵌入</h3>
        <div id="wrapper-{unique_id}">
            <div style="position: relative; width: 100%; height: 400px; border-radius: 8px; overflow: hidden; background: #f0f0f0;">
                <img src="{enhanced_b64}" style="width: 100%; height: 100%; object-fit: cover;">
                <div id="original-{unique_id}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
                    <img src="{original_b64}" style="width: 100%; height: 100%; object-fit: cover;">
                </div>
            </div>
            <input type="range" id="range-{unique_id}" min="0" max="100" value="0" style="width: 100%; margin-top: 10px;">
            <p style="text-align: center; color: #666;">拖动滑块</p>
        </div>
    </div>

    <script type="text/javascript">
    setTimeout(function() {{
        var range = document.getElementById('range-{unique_id}');
        var original = document.getElementById('original-{unique_id}');

        if (range && original) {{
            range.addEventListener('input', function() {{
                var width = this.value + '%';
                original.style.width = width;
                original.style.clipPath = 'inset(0 ' + (100 - this.value) + '% 0 0)';
            }});

            range.addEventListener('change', function() {{
                console.log('Slider value:', this.value);
            }});
        }}
    }}, 100);
    </script>
    """
    return html

# ========== 方案 6: 使用按钮切换 ==========
def create_comparison_v6():
    """方案6: 使用按钮切换（简单可靠）"""
    unique_id = f"v6_{int(time.time() * 1000)}"

    html = f"""
    <div style="width: 100%; max-width: 800px; margin: 20px auto;">
        <h3>方案6: 按钮切换</h3>
        <div style="position: relative; width: 100%; height: 400px; border-radius: 8px; overflow: hidden;">
            <img id="main-{unique_id}" src="{enhanced_b64}" style="width: 100%; height: 100%; object-fit: cover;">
        </div>
        <div style="margin-top: 10px; text-align: center;">
            <button onclick="document.getElementById('main-{unique_id}').src='{enhanced_b64}'"
                    style="padding: 10px 20px; margin: 5px; border-radius: 5px; border: 1px solid #ccc; background: #2ecc71; color: white; cursor: pointer;">
                显示优化后
            </button>
            <button onclick="document.getElementById('main-{unique_id}').src='{original_b64}'"
                    style="padding: 10px 20px; margin: 5px; border-radius: 5px; border: 1px solid #ccc; background: #3498db; color: white; cursor: pointer;">
                显示原图
            </button>
        </div>
        <p style="text-align: center; color: #666;">点击按钮切换图片</p>
    </div>
    """
    return html

# ========== 创建 Gradio 界面 ==========
def create_test_interface():
    with gr.Blocks(title="图像对比滑块 - 6种方案测试", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🧪 图像对比滑块功能测试

        ## 测试说明
        下面有 6 种不同的实现方案，请逐个测试，看哪个能正常工作：

        - **蓝色** = 原图
        - **绿色** = 优化后的图

        测试每个方案的滑块/按钮是否能正常切换显示两张图片。
        """)

        with gr.Tab("方案1: Range Input"):
            gr.Markdown("### ✅ 使用原生 HTML Range Input 控制")
            gr.HTML(create_comparison_v1())

        with gr.Tab("方案2: Opacity"):
            gr.Markdown("### ✅ 使用透明度控制")
            gr.HTML(create_comparison_v2())

        with gr.Tab("方案3: iframe"):
            gr.Markdown("### ✅ 使用 iframe 完全隔离")
            gr.HTML(create_comparison_v3())

        with gr.Tab("方案4: 纯 CSS"):
            gr.Markdown("### ✅ 纯 CSS，无 JavaScript")
            gr.HTML(create_comparison_v4())

        with gr.Tab("方案5: Data URI"):
            gr.Markdown("### ✅ 完整 Data URI 嵌入")
            gr.HTML(create_comparison_v5())

        with gr.Tab("方案6: 按钮切换"):
            gr.Markdown("### ✅ 最简单：按钮切换")
            gr.HTML(create_comparison_v6())

        gr.Markdown("""
        ---
        ## 📝 测试结果记录

        请测试每个方案，并记录结果：

        | 方案 | 是否工作 | 备注 |
        |------|---------|------|
        | 方案1: Range Input | ⬜ | |
        | 方案2: Opacity | ⬜ | |
        | 方案3: iframe | ⬜ | |
        | 方案4: 纯 CSS | ⬜ | |
        | 方案5: Data URI | ⬜ | |
        | 方案6: 按钮切换 | ⬜ | |

        找到能工作的方案后，我们将其集成到主应用中！
        """)

    return demo

if __name__ == "__main__":
    demo = create_test_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,  # 使用不同的端口，避免与主应用冲突
        share=False
    )
