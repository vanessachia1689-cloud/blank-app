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

generate_btn = st.button("🚀 开始生成剧本 (终极防断线版)")

# --- 核心排版魔法：在这里提前放一个“空盒子”占位，确保提取区永远在顶部 ---
top_extraction_area = st.empty()

if generate_btn:
    if not drama_title or not drama_story:
        st.warning("导演，至少得填一下剧名和故事创意呀！")
    else:
        st.session_state.final_script = ""
        top_extraction_area.empty() # 重新生成时，先清空顶部的旧提取区
        
        with st.spinner("后台引擎已点火，正在疯狂撰写中... 预计耗时较长，请耐心等待！"):
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
                heartbeat_box = st.empty() # 心跳与节点雷达占位符
                full_result = ""
                
                # 标记是否正常走完了整个流程
                workflow_finished_normally = False 
                
                # 捕获字块与节点事件
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            data_str = decoded_line[5:].strip()
                            try:
                                json_data = json.loads(data_str)
                                event_type = json_data.get('event')
                                
                                # 📡 节点雷达：播报 Dify 正在后台干什么
                                if event_type == 'node_started':
                                    node_title = json_data.get('data', {}).get('title', '未知节点')
                                    heartbeat_box.info(f"⚙️ Dify 底层节点运转中: 【{node_title}】... [时间: {time.strftime('%H:%M:%S')}]")
                                    continue
                                
                                # 💓 基础心跳
                                elif event_type == 'ping':
                                    heartbeat_box.caption(f"💓 网络通道保持连接中... [最近心跳: {time.strftime('%H:%M:%S')}]")
                                    continue
                                    
                                # 📝 文本块输出
                                elif event_type == 'text_chunk':
                                    chunk = json_data.get('data', {}).get('text', '')
                                    full_result += chunk
                                    result_box.markdown(full_result + " ▌")
                                
                                # ❌ 捕获后台报错
                                elif event_type == 'error':
                                    error_msg = json_data.get('message', '未知错误')
                                    st.error(f"❌ Dify 后台发生错误: {error_msg}")
                                    workflow_finished_normally = True # 标记为已处理结束，避免误报网络断连
                                    break
                                    
                                # ✅ 完美结束
                                elif event_type == 'workflow_finished':
                                    heartbeat_box.empty() 
                                    result_box.markdown(full_result)
                                    st.session_state.final_script = full_result
                                    workflow_finished_normally = True
                                    break # 结束循环
                                    
                            except json.JSONDecodeError:
                                continue
                
                # 🚨 如果循环结束了，但没有收到 finished 信号，说明遭遇了“网络静默强杀”
                if not workflow_finished_normally:
                    st.error("⚠️ 警告：连接被网络运营商或路由器异常切断！")
                    st.info("👉 别慌！Dify 后台此刻**很可能仍在继续写剧本**。由于耗时过长，这条网页连接被强行掐断了。\n\n请不要关闭此页面，直接前往 Dify 工作流后台的【日志追踪】页面查看最终结果。")
                    if full_result:
                        st.session_state.final_script = full_result # 把断线前已生成的部分也存下来

            except Exception as e:
                st.error(f"连接失败，请检查 Dify API 或必填项是否填写完整: {e}")

# --- 将提取区装入刚才顶部的“空盒子”里 ---
if st.session_state.final_script:
    with top_extraction_area.container():
        st.success("✅ 剧本生成已完成（或已中断）！请点击下方黑框右上角的【两张纸】图标，一键复制后直接粘贴到飞书。")
        st.markdown("👇 **剧本一键提取区**")
        st.code(st.session_state.final_script, language="markdown")