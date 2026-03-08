import streamlit as st
import requests
import json
import time

# 你的专属 Dify API 密钥
DIFY_API_KEY = "app-VkFKu6BHzDKWekp9NOugxk2C"
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"

# 页面外观设置
st.set_page_config(page_title="AI短剧剧本生成器", page_icon="🎬", layout="centered")

# --- 必备护城河：装上“记忆芯片” ---
if "final_script" not in st.session_state:
    st.session_state.final_script = ""

st.title("🎬 AI短剧剧本SOP【V-Team】")
st.markdown("⚠️ **机密系统：仅供TT-909 WORK内部项目组使用，请勿外传。**")

st.subheader("📝 请填写剧本设定要素")

col1, col2 = st.columns(2)
with col1:
    drama_title = st.text_input("剧名 (drama_title):", placeholder="例如：My Zombie Bodyguard")
    story_genre = st.text_input("故事类型 (story_genre):", placeholder="例如：狼人/吸血鬼/复仇")
with col2:
    target_audience = st.text_input("目标受众 (target_audience):", placeholder="例如：18-35岁北美女性")

drama_story = st.text_area("三幕剧故事创意 (drama_story):", height=150)
story_background = st.text_area("故事背景 (story_background):", height=100)
tiktok_elements = st.text_area("TT核心爆点元素 (tiktok_elements):", height=100)
concept_breakdown = st.text_area("创意解析 (concept_breakdown):", height=100)

generate_btn = st.button("🚀 开始生成剧本 (流式不断线版)")

# --- 核心排版魔法：在这里提前放一个“空盒子”占位，确保提取区永远在顶部 ---
top_extraction_area = st.empty()

if generate_btn:
    if not drama_title or not drama_story:
        st.warning("导演，至少得填一下剧名和故事创意呀！")
    else:
        st.session_state.final_script = ""
        top_extraction_area.empty() # 重新生成时，先清空顶部的旧提取区
        
        with st.spinner("后台引擎已点火，正在疯狂撰写中... 只要进度条在转就不会断线！"):
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
                # --- 核心修改：强制设定双重超时，连接等5分钟，数据接收死等4小时 ---
                response = requests.post(DIFY_API_URL, headers=headers, json=payload, stream=True, timeout=(300, 14400))
                response.raise_for_status()
                
                # 提示流式输出正在进行
                st.markdown("### 📜 剧本流式输出实时预览 (生成完毕后将自动折叠)")
                st.divider()
                
                result_box = st.empty()
                heartbeat_box = st.empty() # 新增：心跳起搏器占位符
                full_result = ""
                
                # 捕获字块
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            data_str = decoded_line[5:].strip()
                            try:
                                json_data = json.loads(data_str)
                                
                                # 拦截 ping 事件，强行刷新前端 UI，防止 WebSocket 休眠断连
                                if json_data.get('event') == 'ping':
                                    heartbeat_box.caption(f"💓 引擎保持连接中... [最近心跳: {time.strftime('%H:%M:%S')}]")
                                    continue
                                    
                                elif json_data.get('event') == 'text_chunk':
                                    chunk = json_data.get('data', {}).get('text', '')
                                    full_result += chunk
                                    result_box.markdown(full_result + " ▌")
                                    
                                elif json_data.get('event') == 'workflow_finished':
                                    heartbeat_box.empty() # 生成完毕后，把心跳提示清空
                                    result_box.markdown(full_result)
                                    # 存入记忆芯片
                                    st.session_state.final_script = full_result
                                    
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                st.error(f"连接失败，请检查 Dify API 或必填项是否填写完整: {e}")

# --- 将提取区装入刚才顶部的“空盒子”里 ---
if st.session_state.final_script:
    with top_extraction_area.container():
        st.success("✅ 剧本已生成！请点击下方黑框右上角的【两张纸】图标，一键复制后直接粘贴到飞书即可。")
        st.markdown("👇 **剧本一键提取区**")
        st.code(st.session_state.final_script, language="markdown")