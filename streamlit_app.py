import streamlit as st
import requests
import json

# 你的专属 Dify API 密钥 (已自动填入)
DIFY_API_KEY = "app-VkFKu6BHzDKWekp9NOugxk2C"
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"

# 页面外观设置
st.set_page_config(page_title="北美短剧剧本生成器", page_icon="🎬", layout="centered")
st.title("🎬 北美短剧剧本流水线")
st.markdown("⚠️ **机密系统：仅供内部项目组使用，请勿外传。**")

# 实习生的输入区
user_title = st.text_input("【1】请输入剧名 (Title):", placeholder="例如：My Zombie Bodyguard")
user_input = st.text_area("【2】请粘贴输入材料 (大纲/创意/原故事):", height=200)

if st.button("🚀 开始生成剧本 (流式不断线版)"):
    if not user_input:
        st.warning("导演，您还没输入材料呢！")
    else:
        # 建立防断线的流式连接
        with st.spinner("后台引擎已点火，正在疯狂撰写中... 只要进度条在转就不会断线！"):
            headers = {
                "Authorization": f"Bearer {DIFY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # 【重要核对】：这里的 title 和 raw_text 必须和你 Dify 里的输入变量名一模一样！
            payload = {
                "inputs": {
                    "title": user_title,
                    "raw_text": user_input
                },
                "response_mode": "streaming",
                "user": "intern-01"
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
                st.error(f"连接失败，请检查 Dify API 是否正常: {e}")