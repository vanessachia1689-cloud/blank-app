import streamlit as st
import requests
import json

# 你的专属 Dify API 密钥
DIFY_API_KEY = "app-VkFKu6BHzDKWekp9NOugxk2C"
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"

# 页面外观设置
st.set_page_config(page_title="北美短剧剧本生成器", page_icon="🎬", layout="centered")
st.title("🎬 北美短剧剧本流水线")
st.markdown("⚠️ **机密系统：仅供内部项目组使用，请勿外传。**")

st.subheader("📝 请填写剧本设定要素")

# --- 核心修改1：根据 Dify 后台变量，增加对应的用户输入区 ---
# 使用两列排版，让短文本输入框更紧凑
col1, col2 = st.columns(2)
with col1:
    # 对应 Dify 里的短文本输入 (T图标)
    drama_title = st.text_input("剧名 (drama_title):", placeholder="例如：My Zombie Bodyguard")
    story_genre = st.text_input("故事类型 (story_genre):", placeholder="例如：狼人/吸血鬼/复仇")
with col2:
    target_audience = st.text_input("目标受众 (target_audience):", placeholder="例如：18-35岁北美女性")

# 对应 Dify 里的长文本/段落输入 (多行图标)
drama_story = st.text_area("三幕剧故事创意 (drama_story):", height=150)
story_background = st.text_area("故事背景 (story_background):", height=100)
tiktok_elements = st.text_area("TT核心爆点元素 (tiktok_elements):", height=100)
concept_breakdown = st.text_area("创意解析 (concept_breakdown):", height=100)

if st.button("🚀 开始生成剧本 (流式不断线版)"):
    # 简单的空值校验，防止有人啥都没填就点发送
    if not drama_title or not drama_story:
        st.warning("导演，至少得填一下剧名和故事创意呀！")
    else:
        # 建立防断线的流式连接
        with st.spinner("后台引擎已点火，正在疯狂撰写中... 只要进度条在转就不会断线！"):
            headers = {
                "Authorization": f"Bearer {DIFY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # --- 核心修改2：精准对齐 Dify 的 input 变量名 ---
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
                "user": "Vanessa-Team" # 标记调用来源
            }
            
            try:
                response = requests.post(DIFY_API_URL, headers=headers, json=payload, stream=True)
                response.raise_for_status()
                
                result_box = st.empty()
                full_result = ""
                
                # 捕获 Dify 吐出来的每一个字
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            data_str = decoded_line[5:].strip()
                            try:
                                json_data = json.loads(data_str)
                                if json_data.get('event') == 'text_chunk':
                                    chunk = json_data.get('data', {}).get('text', '')
                                    full_result += chunk
                                    # 实时渲染打字机效果
                                    result_box.markdown(full_result + " ▌")
                                elif json_data.get('event') == 'workflow_finished':
                                    result_box.markdown(full_result) # 去掉光标
                                    st.success("✅ 剧本生成完毕！请将上方内容复制到飞书文档。")
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                st.error(f"连接失败，请检查 Dify API 或必填项是否填写完整: {e}")