import streamlit as st
import requests

# 1. Page Configuration & Branding
st.set_page_config(page_title="Rafiki IT", page_icon="🤖", layout="centered")

# Custom CSS for MOHI Green branding
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; }
    .stButton>button { background-color: #2e7d32; color: white; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 Rafiki IT: MOHI Support")
st.caption("Empathetic I.T. assistance aligned with MOHI's mission and values.")

# 2. Sidebar with Directives & Suggested Questions
with st.sidebar:
     
    # st.image("https://mohiit.org/static/images/inventorylogo.png", width=150)
    st.image("assets/mohi-it-logo.png", width=150)
    st.header("How to use Rafiki")
    st.info("Rafiki is here to help with Portal Login, Leave Applications, and I.T. Policies.")
    
    st.subheader("Suggested Prompts")
    if st.button("📍 Where is the IT Office?"):
        st.session_state.pending_prompt = "Where is the IT office located and what are the extensions?"
    if st.button("🔐 Locked out of Portal"):
        st.session_state.pending_prompt = "My portal account is locked, what should I do?"
    if st.button("📝 Apply for Leave"):
        st.session_state.pending_prompt = "Show me the steps to apply for employee leave."

# 3. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Handle Input (Manual or Suggested)
prompt = st.chat_input("Ask Rafiki about I.T. support or MOHI policies...")
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Rafiki is consulting the MOHI knowledge base..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/api/chat",
                    json={"message": prompt, "history": st.session_state.messages},
                    timeout=30
                )
                
                if response.status_code == 200:
                    answer = response.json().get("response")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.warning("⚠️ Rafiki is currently offline. Please ensure the Django server is running in the background.")
            except Exception:
                st.error("🔌 Connection Error: I can't reach the 'Brain' right now. Please notify the I.T. Department if this persists.")
