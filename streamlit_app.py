import streamlit as st
import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 你的专属 Dify API 密钥
DIFY_API_KEY = "app-VkFKu6BHzDKWekp9NOugxk2C"
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"

# 页面外观设置
st.set_page_config(page_title="AI短剧剧本生成器", page_icon="🎬", layout="centered")

# --- 必备护城河：装上“记忆芯片”并绑定输入框 ---
# 【修改点】增加了 character_ecosystem
keys_to_init = [
    "final_script", "drama_title", "story_genre", "target_audience",
    "story_background", "character_ecosystem", "drama_story", 
    "tiktok_elements", "concept_breakdown"
]
for key in keys_to_init:
    if key not in st.session_state:
        st.session_state[key] = ""

# 🧹 一键清空回调函数
def clear_form():
    for key in keys_to_init:
        if key in st.session_state:
            del st.session_state[key]

# ================= UI 布局与标题 =================
st.title("🎬 AI短剧剧本SOP【V-Team】")
st.markdown("⚠️ **机密系统：仅供TT-909 WORK内部项目组使用，请勿外传。**")
st.markdown("<br>", unsafe_allow_html=True) 

col_sub, col_clear = st.columns([4, 1])
with col_sub:
    st.subheader("📝 请填写剧本设定要素")
with col_clear:
    st.button("🗑️ 一键清空", on_click=clear_form, use_container_width=True)

# 【修改点】严格按照要求的 8 个字段顺序重新排版，并更新了 Label 名称
col1, col2 = st.columns(2)
with col1:
    drama_title = st.text_input("创意名称 (drama_title):", key="drama_title", placeholder="例如：My Zombie Bodyguard")
    target_audience = st.text_input("受众 (target_audience):", key="target_audience", placeholder="例如：18-35岁北美女性")
with col2:
    story_genre = st.text_input("故事类型 (story_genre):", key="story_genre", placeholder="例如：狼人/吸血鬼/复仇")

# 文本域按从上到下的逻辑顺序排列
story_background = st.text_area("故事背景 (story_background):", key="story_background", height=100)
character_ecosystem = st.text_area("人物小传及羁绊 (character_ecosystem):", key="character_ecosystem", height=150)
drama_story = st.text_area("三幕格式创意 (drama_story):", key="drama_story", height=150)
tiktok_elements = st.text_area("提取的TikTok爆款元素 (tiktok_elements):", key="tiktok_elements", height=100)
concept_breakdown = st.text_area("创意解析 (concept_breakdown):", key="concept_breakdown", height=100)

generate_btn = st.button("🚀 开始生成S级爆款剧本！")

# --- 核心排版魔法：提取区占位 ---
top_extraction_area = st.empty()

if generate_btn:
    if not drama_title or not drama_story:
        st.warning("导演，至少得填一下创意名称和三幕格式创意呀！")
    else:
        st.session_state.final_script = ""
        top_extraction_area.empty() 
        
        with st.spinner("后台引擎已点火，正在疯狂撰写中... (剧本全集+质检数据量极大，请耐心等待)"):
            headers = {
                "Authorization": f"Bearer {DIFY_API_KEY}",
                "Content-Type": "application/json",
                "Connection": "keep-alive" 
            }
            
            # 【修改点】向 Dify 发送的 payload 中加入新增的 character_ecosystem 变量，顺序与 UI 保持一致
            payload = {
                "inputs": {
                    "drama_title": drama_title,
                    "story_genre": story_genre,
                    "target_audience": target_audience,
                    "story_background": story_background,
                    "character_ecosystem": character_ecosystem,
                    "drama_story": drama_story,
                    "tiktok_elements": tiktok_elements,
                    "concept_breakdown": concept_breakdown
                },
                "response_mode": "streaming",
                "user": "Vanessa-Team" 
            }
            
            # --- 核心升级：装载底层重试与保活适配器 ---
            session = requests.Session()
            retry = Retry(connect=5, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            try:
                # 发起请求
                response = session.post(DIFY_API_URL, headers=headers, json=payload, stream=True, timeout=(300, 14400))
                response.raise_for_status()
                
                st.markdown("### 📜 剧本流式输出实时预览")
                st.divider()
                
                # UI 组件占位
                run_id_box = st.empty()
                heartbeat_box = st.empty()
                result_box = st.empty()
                
                full_result = ""
                workflow_finished_normally = False 
                
                # 节流阀
                last_text_update = time.time()
                last_heartbeat_update = time.time()
                last_save_time = time.time()
                
                # 优化：增加 chunk_size=1 防止本地 socket 缓冲假死
                for line in response.iter_lines(decode_unicode=True, chunk_size=1):
                    if line:
                        if line.startswith('data:'):
                            data_str = line[5:].strip()
                            try:
                                json_data = json.loads(data_str)
                                event_type = json_data.get('event')
                                
                                # 💎 杀手锏 1：捕获任务 ID
                                if event_type == 'workflow_started':
                                    workflow_run_id = json_data.get('workflow_run_id', '未知')
                                    run_id_box.success(f"🔖 任务追踪防丢编号: **{workflow_run_id}** (如果前台断线，去 Dify 后台【日志】搜此号即可无损提取完整剧本！)")
                                
                                # 📡 节点雷达
                                elif event_type == 'node_started':
                                    if time.time() - last_heartbeat_update > 1.0:
                                        node_title = json_data.get('data', {}).get('title', '未知节点')
                                        heartbeat_box.info(f"⚙️ 底层节点: 【{node_title}】运转中... (如遇卡顿，是大模型在深度阅读几万字上下文，请勿刷新) [时间: {time.strftime('%H:%M:%S')}]")
                                        last_heartbeat_update = time.time()
                                
                                # 💓 基础心跳
                                elif event_type == 'ping':
                                    if time.time() - last_heartbeat_update > 2.0:
                                        heartbeat_box.caption(f"💓 服务器通信保持中... [最近心跳: {time.strftime('%H:%M:%S')}]")
                                        last_heartbeat_update = time.time()
                                    
                                # 📝 文本块输出
                                elif event_type == 'text_chunk':
                                    chunk = json_data.get('data', {}).get('text', '')
                                    full_result += chunk
                                    
                                    current_time = time.time()
                                    # UI 渲染节流 (0.5秒)
                                    if current_time - last_text_update > 0.5:
                                        result_box.markdown(full_result + " ▌")
                                        last_text_update = current_time
                                        
                                    # 实时存档！每2秒写入一次 session_state
                                    if current_time - last_save_time > 2.0:
                                        st.session_state.final_script = full_result
                                        last_save_time = current_time
                                
                                # ❌ 捕获后台报错
                                elif event_type == 'error':
                                    error_msg = json_data.get('message', '未知错误')
                                    st.error(f"❌ Dify 内部发生错误: {error_msg}")
                                    workflow_finished_normally = True 
                                    break
                                    
                                # ✅ 完美结束
                                elif event_type == 'workflow_finished':
                                    heartbeat_box.empty() 
                                    result_box.markdown(full_result)
                                    st.session_state.final_script = full_result
                                    workflow_finished_normally = True
                                    break 
                                    
                            except json.JSONDecodeError:
                                continue
                
                # 🚨 捕获由于服务器硬超时造成的强杀
                if not workflow_finished_normally:
                    st.warning("⚠️ 前台展示连接已被云网关强制断开（由于总运行时间触及15分钟物理极限）！")
                    st.info("👉 **别慌！剧本并没有丢失！** Dify 后台其实仍在继续为你完成最终的质检和资料生成。请等待 3-5 分钟后，前往 Dify 后台的【日志追踪】，凭顶部的“任务追踪防丢编号”直接复制最终成果。已为你保存断线前的进度在下方。")
                    if full_result:
                        st.session_state.final_script = full_result 

            except requests.exceptions.ReadTimeout:
                st.error("⏳ 触发读取超时！大模型阅读2万字上下文耗时过久，未能及时传回数据。请去 Dify 后台提取。")
                if 'full_result' in locals() and full_result:
                    st.session_state.final_script = full_result
            except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError):
                st.warning("🔌 触发网关强制熔断！大模型节点运行时间过长，触碰了云端 15 分钟的存活死线。")
                st.info("👉 Dify 后台引擎仍在无头运行，请稍后前往 Dify 日志中获取最终资料包！")
                if 'full_result' in locals() and full_result:
                    st.session_state.final_script = full_result
                    result_box.markdown(full_result)
            except Exception as e:
                st.error(f"连接异常: {e}")
                if 'full_result' in locals() and full_result:
                    st.session_state.final_script = full_result
            finally:
                session.close()

# --- 将提取区装入顶部的“空盒子”里 ---
if st.session_state.final_script:
    with top_extraction_area.container():
        st.success("✅ 当前截获的内容已保存！如果内容不完整（比如缺少末尾资料库），说明触碰了物理超时，请去 Dify 后台取件！")
        st.markdown("👇 **剧本一键提取区**")
        st.code(st.session_state.final_script, language="markdown")