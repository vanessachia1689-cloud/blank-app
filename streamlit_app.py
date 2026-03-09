import streamlit as st
import requests
import json
import time

# 你的专属 Dify API 密钥
DIFY_API_KEY = "app-VkFKu6BHzDKWekp9NOugxk2C"
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"

# 页面外观设置
st.set_page_config(page_title="AI短剧剧本生成器", page_icon="🎬", layout="centered")

# --- 必备护城河：装上“记忆芯片”并绑定输入框 ---
keys_to_init = [
    "final_script", "drama_title", "story_genre", "target_audience",
    "drama_story", "story_background", "tiktok_elements", "concept_breakdown"
]
for key in keys_to_init:
    if key not in st.session_state:
        st.session_state[key] = ""

# 🧹 一键清空回调函数
def clear_form():
    for key in keys_to_init:
        st.session_state[key] = ""

# ================= UI 布局与标题 =================
# 核心修改：让主标题独占整行，恢复大气排版
st.title("🎬 AI短剧剧本SOP【V-Team】")
st.markdown("⚠️ **机密系统：仅供TT-909 WORK内部项目组使用，请勿外传。**")
st.markdown("<br>", unsafe_allow_html=True) # 增加一点垂直留白让视觉更舒服

# 核心修改：将小标题和清空按钮并排放在一起
col_sub, col_clear = st.columns([4, 1])
with col_sub:
    st.subheader("📝 请填写剧本设定要素")
with col_clear:
    # 按钮靠右对齐，与小标题同行
    st.button("🗑️ 一键清空", on_click=clear_form, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    drama_title = st.text_input("剧名 (drama_title):", key="drama_title", placeholder="例如：My Zombie Bodyguard")
    story_genre = st.text_input("故事类型 (story_genre):", key="story_genre", placeholder="例如：狼人/吸血鬼/复仇")
with col2:
    target_audience = st.text_input("目标受众 (target_audience):", key="target_audience", placeholder="例如：18-35岁北美女性")

drama_story = st.text_area("三幕剧故事创意 (drama_story):", key="drama_story", height=150)
story_background = st.text_area("故事背景 (story_background):", key="story_background", height=100)
tiktok_elements = st.text_area("TT核心爆点元素 (tiktok_elements):", key="tiktok_elements", height=100)
concept_breakdown = st.text_area("创意解析 (concept_breakdown):", key="concept_breakdown", height=100)

generate_btn = st.button("🚀 开始生成S级爆款剧本！")

# --- 核心排版魔法：提取区占位 ---
top_extraction_area = st.empty()

if generate_btn:
    if not drama_title or not drama_story:
        st.warning("导演，至少得填一下剧名和故事创意呀！")
    else:
        st.session_state.final_script = ""
        top_extraction_area.empty() 
        
        with st.spinner("后台引擎已点火，正在疯狂撰写中... 预计耗时较长，请保持网页常亮勿切后台！"):
            headers = {
                "Authorization": f"Bearer {DIFY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": {
                    "drama_title": drama_title,
                    "drama_story": drama_story,
                    "story_genre": story_genre,
                    "target_audience": target_audience,
                    "story_background": story_background,
                    "tiktok_elements": tiktok_elements,
                    "concept_breakdown": concept_breakdown
                },
                "response_mode": "streaming",
                "user": "Vanessa-Team" 
            }
            
            try:
                # 4小时超长超时保护
                response = requests.post(DIFY_API_URL, headers=headers, json=payload, stream=True, timeout=(300, 14400))
                response.raise_for_status()
                
                st.markdown("### 📜 剧本流式输出实时预览")
                st.divider()
                
                result_box = st.empty()
                heartbeat_box = st.empty()
                full_result = ""
                workflow_finished_normally = False 
                
                # ⏱️ 渲染节流阀时间戳
                last_update_time = time.time()
                
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            data_str = decoded_line[5:].strip()
                            try:
                                json_data = json.loads(data_str)
                                event_type = json_data.get('event')
                                
                                # 📡 节点雷达
                                if event_type == 'node_started':
                                    node_title = json_data.get('data', {}).get('title', '未知节点')
                                    heartbeat_box.info(f"⚙️ Dify 底层节点运转中: 【{node_title}】... [时间: {time.strftime('%H:%M:%S')}]")
                                    continue
                                
                                # 💓 基础心跳
                                elif event_type == 'ping':
                                    heartbeat_box.caption(f"💓 网络通道保持连接中... [最近心跳: {time.strftime('%H:%M:%S')}]")
                                    continue
                                    
                                # 📝 文本块输出 (加入神级节流阀)
                                elif event_type == 'text_chunk':
                                    chunk = json_data.get('data', {}).get('text', '')
                                    full_result += chunk
                                    
                                    # 核心优化：每隔 0.5 秒才刷新一次前端 UI，防止超长文本把浏览器卡崩溃导致断连！
                                    if time.time() - last_update_time > 0.5:
                                        result_box.markdown(full_result + " ▌")
                                        last_update_time = time.time()
                                
                                # ❌ 捕获后台报错
                                elif event_type == 'error':
                                    error_msg = json_data.get('message', '未知错误')
                                    st.error(f"❌ Dify 后台发生错误: {error_msg}")
                                    workflow_finished_normally = True 
                                    break
                                    
                                # ✅ 完美结束
                                elif event_type == 'workflow_finished':
                                    heartbeat_box.empty() 
                                    result_box.markdown(full_result) # 结束时做一次最终的完整渲染
                                    st.session_state.final_script = full_result
                                    workflow_finished_normally = True
                                    break 
                                    
                            except json.JSONDecodeError:
                                continue
                
                # 🚨 捕获由于反向代理等原因造成的强杀
                if not workflow_finished_normally:
                    st.error("⚠️ 警告：连接被异常切断！")
                    st.info("👉 别慌！如果是文本太长导致的超时，Dify 后台此刻**很可能仍在继续写剧本**。\n\n请前往 Dify 工作流后台的【日志追踪】页面查看最终结果。")
                    if full_result:
                        st.session_state.final_script = full_result 

            except requests.exceptions.ChunkedEncodingError:
                st.error("⚠️ 警告：数据流被服务器强制掐断！(这通常是由于生成时间过长，代理服务器断开了连接)。请去 Dify 后台拿结果！")
                if full_result:
                    st.session_state.final_script = full_result
            except Exception as e:
                st.error(f"连接失败，请检查 Dify API 或必填项是否填写完整: {e}")

# --- 将提取区装入顶部的“空盒子”里 ---
if st.session_state.final_script:
    with top_extraction_area.container():
        st.success("✅ 剧本生成已完成！请点击下方黑框右上角的【两张纸】图标，一键复制后直接粘贴到飞书。")
        st.markdown("👇 **剧本一键提取区**")
        st.code(st.session_state.final_script, language="markdown")