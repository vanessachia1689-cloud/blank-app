import streamlit as st
import requests
import json
import time  # 👈 新增：用于显示心跳时间戳

# ... (前面的代码保持不变) ...

            try:
                # 👈 修复 1：把 7200 改成了我们约定好的 14400 (4小时)
                response = requests.post(DIFY_API_URL, headers=headers, json=payload, stream=True, timeout=(300, 14400))
                response.raise_for_status()
                
                # 提示流式输出正在进行
                st.markdown("### 📜 剧本流式输出实时预览 (生成完毕后将自动折叠)")
                st.divider()
                
                result_box = st.empty()
                heartbeat_box = st.empty() # 👈 修复 2：新增一个专门用来跳动心跳的“起搏器”占位符
                full_result = ""
                
                # 捕获字块
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            data_str = decoded_line[5:].strip()
                            try:
                                json_data = json.loads(data_str)
                                
                                # 👈 修复 3：拦截 ping 事件，强行刷新前端 UI，防止 WebSocket 休眠断连
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

# ... (后面的代码保持不变) ...