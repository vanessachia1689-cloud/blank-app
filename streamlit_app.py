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
st.title("🎬 AI短剧剧本SOP【V-Team】")
st.markdown("⚠️ **机密系统：仅供TT-909 WORK内部项目组使用，请勿外传。**")
st.markdown("<br>", unsafe_allow_html=True) 

col_sub, col_clear = st.columns([4, 1])
with col_sub:
    st.subheader("📝 请填写剧本设定要素")
with col_clear:
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
        
        with st.spinner("后台引擎已点火，正在疯狂撰写中... (已开启防断线保护，可安心切换网页)"):
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
            
            # 使用 Session 保持更稳定的连接池
            with requests.Session() as session:
                try:
                    # 4小时超长超时保护
                    response = session.post(DIFY_API_URL, headers=headers, json=payload, stream=True, timeout=(300, 14400))
                    response.raise_for_status()
                    
                    st.markdown("### 📜 剧本流式输出实时预览")
                    st.divider()
                    
                    result_box = st.empty()
                    heartbeat_box = st.empty()
                    full_result = ""
                    workflow_finished_normally = False 
                    
                    # 为文字和雷达分别设置独立节流阀
                    last_text_update = time.time()
                    last_heartbeat_update = time.time()
                    last_save_time = time.time()
                    
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            if line.startswith('data:'):
                                data_str = line[5:].strip()
                                try:
                                    json_data = json.loads(data_str)
                                    event_type = json_data.get('event')
                                    
                                    # 📡 节点雷达
                                    if event_type == 'node_started':
                                        if time.time() - last_heartbeat_update > 1.0:
                                            node_title = json_data.get('data', {}).get('title', '未知节点')
                                            heartbeat_box.info(f"⚙️ Dify 底层节点运转中: 【{node_title}】... [时间: {time.strftime('%H:%M:%S')}]")
                                            last_heartbeat_update = time.time()
                                        continue
                                    
                                    # 💓 基础心跳
                                    elif event_type == 'ping':
                                        if time.time() - last_heartbeat_update > 2.0:
                                            heartbeat_box.caption(f"💓 网络通道保持连接中... [最近心跳: {time.strftime('%H:%M:%S')}]")
                                            last_heartbeat_update = time.time()
                                        continue
                                        
                                    # 📝 文本块输出
                                    elif event_type == 'text_chunk':
                                        chunk = json_data.get('data', {}).get('text', '')
                                        full_result += chunk
                                        
                                        current_time = time.time()
                                        # UI 渲染节流 (0.5秒)
                                        if current_time - last_text_update > 0.5:
                                            result_box.markdown(full_result + " ▌")
                                            last_text_update = current_time
                                            
                                        # 🛡️ 核心修改：实时存档防断线！每2秒写入一次 session_state
                                        if current_time - last_save_time > 2.0:
                                            st.session_state.final_script = full_result
                                            last_save_time = current_time
                                    
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
                    
                    # 🚨 捕获由于反向代理、浏览器休眠等原因造成的强制掐断
                    if not workflow_finished_normally:
                        st.warning("⚠️ 前台连接因休眠或网络波动断开，但这不影响大局！")
                        st.info("👉 Dify 后台大概率仍在继续写剧本。当前已为你保存了断线前的全部文本，完整结果请前往 Dify 工作流后台的【日志追踪】查看。")
                        if full_result:
                            st.session_state.final_script = full_result 

                except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError):
                    st.warning("⚠️ 提示：浏览器切后台导致数据流断开 (通常是休眠引起的)。别担心，Dify 后端仍在运行！")
                    if full_result:
                        st.session_state.final_script = full_result
                        result_box.markdown(full_result)
                except Exception as e:
                    st.error(f"连接失败，请检查 Dify API 或必填项是否填写完整: {e}")
                    if 'full_result' in locals() and full_result:
                        st.session_state.final_script = full_result

# --- 将提取区装入顶部的“空盒子”里 ---
if st.session_state.final_script:
    with top_extraction_area.container():
        st.success("✅ 剧本生成/阶段保存完毕！请点击下方黑框右上角的【两张纸】图标，一键复制后直接粘贴到飞书。")
        st.markdown("👇 **剧本一键提取区**")
        st.code(st.session_state.final_script, language="markdown")