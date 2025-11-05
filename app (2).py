# --- 在Session State管理部分添加更多状态控制 ---
if 'previous_function' not in st.session_state:
    st.session_state.previous_function = None
if 'ui_cleared' not in st.session_state:
    st.session_state.ui_cleared = True
if 'function_change_counter' not in st.session_state:
    st.session_state.function_change_counter = 0

# --- 新增功能切换处理函数 ---
def handle_function_change():
    """处理功能切换，清理UI状态"""
    if st.session_state.previous_function != st.session_state.selected_function:
        # 功能发生切换，需要清理UI
        st.session_state.function_change_counter += 1
        st.session_state.file_uploader_key = st.session_state.function_change_counter * 1000
        st.session_state.upload_success = False
        st.session_state.ui_cleared = False
        st.session_state.previous_function = st.session_state.selected_function
        
        # 清理相关的session state
        keys_to_clear = []
        for key in st.session_state.keys():
            if any(pattern in key for pattern in ['uploader_', 'character_uploader_', 'reference_uploader_']):
                keys_to_clear.append(key)
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # 强制重新渲染
        st.rerun()

# --- 修改侧边栏功能选择部分 ---
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🎨 功能选择")
        
        # 姿态迁移选项
        pose_selected = st.button(
            "🤸 姿态迁移", 
            use_container_width=True,
            type="primary" if st.session_state.selected_function == "姿态迁移" else "secondary",
            key="pose_function_btn"
        )
        if pose_selected and st.session_state.selected_function != "姿态迁移":
            st.session_state.selected_function = "姿态迁移"
            handle_function_change()
        
        st.caption("角色图片 + 姿势参考图")
        
        # 图像优化选项
        enhance_selected = st.button(
            "🎨 图像优化", 
            use_container_width=True,
            type="primary" if st.session_state.selected_function == "图像优化" else "secondary",
            key="enhance_function_btn"
        )
        if enhance_selected and st.session_state.selected_function != "图像优化":
            st.session_state.selected_function = "图像优化"
            handle_function_change()
        
        st.caption("单图片智能优化")
        
        # 显示当前状态
        if not st.session_state.ui_cleared:
            st.info("🔄 正在切换功能...")
        
        st.divider()
        
        # 其余侧边栏内容保持不变...

# --- 修改姿态迁移界面函数 ---
def render_pose_interface():
    """姿态迁移界面 - 增强版本"""
    st.markdown("### 🤸 姿态迁移")
    st.info("💡 需要同时上传角色图片和姿势参考图才能开始处理")

    # 检查功能切换状态
    if st.session_state.selected_function != "姿态迁移":
        st.warning("⚠️ 正在切换到姿态迁移模式...")
        return

    if st.session_state.upload_success:
        st.success("✅ 任务已添加到处理队列!")
        st.session_state.upload_success = False

    # 生成唯一的key
    character_key = f"character_uploader_{st.session_state.file_uploader_key}_{st.session_state.function_change_counter}"
    reference_key = f"reference_uploader_{st.session_state.file_uploader_key}_{st.session_state.function_change_counter}"

    # 角色图片上传
    st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    st.markdown("**👤 角色图片**")
    character_image = st.file_uploader(
        "选择角色图片",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=False,
        help="选择需要处理的角色图片",
        key=character_key
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
        key=reference_key
    )
    if reference_image:
        show_image_preview(reference_image, "参考图预览", "reference_preview")
    st.markdown('</div>', unsafe_allow_html=True)

    # 开始处理按钮
    if st.button("🚀 开始处理", use_container_width=True, type="primary", key=f"pose_process_btn_{st.session_state.function_change_counter}"):
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

            st.session_state.upload_success = True
            st.session_state.file_uploader_key += 1
            st.rerun()
        else:
            st.error("❌ 请同时上传角色图片和姿势参考图！")

# --- 修改图像优化界面函数 ---
def render_enhance_interface():
    """图像优化界面 - 增强版本"""
    st.markdown("### 🎨 图像优化")
    st.info("💡 支持批量上传，自动加入处理队列")

    # 检查功能切换状态
    if st.session_state.selected_function != "图像优化":
        st.warning("⚠️ 正在切换到图像优化模式...")
        return

    if st.session_state.upload_success:
        st.success("✅ 文件已添加到处理队列!")
        st.session_state.upload_success = False

    # 生成唯一的key
    uploader_key = f"enhance_uploader_{st.session_state.file_uploader_key}_{st.session_state.function_change_counter}"

    uploaded_files = st.file_uploader(
        "选择图片文件",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=True,
        help="支持批量上传，自动加入处理队列",
        key=uploader_key
    )

    if uploaded_files:
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

# --- 修改主函数 ---
def main():
    # 处理功能切换
    handle_function_change()
    
    # 渲染侧边栏
    render_sidebar()

    # 主标题
    st.title("🎨 RunningHub AI - 智能图片处理工具")
    st.caption(f"当前模式: **{st.session_state.selected_function}** • 全局并发限制: {MAX_CONCURRENT}")
    st.divider()

    # 主界面布局
    left_col, right_col = st.columns([1.8, 3.2])

    # 左侧：功能界面
    with left_col:
        # 使用容器确保完整重新渲染
        with st.container():
            if st.session_state.selected_function == "姿态迁移":
                render_pose_interface()
            else:
                render_enhance_interface()

    # 右侧：任务列表 (保持原有逻辑)
    with right_col:
        st.markdown("### 📋 任务列表")

        if not st.session_state.tasks:
            st.info("💡 暂无任务，请选择功能并上传文件开始处理")
        else:
            # 其余任务列表逻辑保持不变...
            # (这里包含原有的任务显示和管理代码)
            pass

    # 页脚保持不变...

# --- 新增清理函数 (在操作按钮部分使用) ---
def clear_function_ui():
    """清理当前功能的UI状态"""
    st.session_state.function_change_counter += 1
    st.session_state.file_uploader_key = st.session_state.function_change_counter * 1000
    st.session_state.upload_success = False
    
    # 清理文件上传器相关的session state
    keys_to_clear = []
    for key in st.session_state.keys():
        if any(pattern in key for pattern in [
            'uploader_', 'character_uploader_', 'reference_uploader_',
            f'{st.session_state.selected_function.lower()}_uploader_'
        ]):
            keys_to_clear.append(key)
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# --- 在操作按钮部分添加UI清理按钮 ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🗑️ 清空所有", use_container_width=True):
        st.session_state.tasks = []
        st.session_state.task_queue = []
        st.session_state.download_clicked = {}
        clear_function_ui()
        st.rerun()

with col2:
    if st.button("🧹 清理界面", use_container_width=True):
        clear_function_ui()
        st.success("✅ 界面已清理")
        st.rerun()

with col3:
    if st.button("🔄 重启失败", use_container_width=True):
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

with col4:
    if st.button("🔄 强制刷新", use_container_width=True):
        st.rerun()
