import openai
import streamlit as st
import logging
from PIL import Image, ImageEnhance
import time
import json
import requests
import base64
from openai import OpenAI, OpenAIError

# Configure logging
logging.basicConfig(level=logging.INFO)
NUMBER_OF_MESSAGES_TO_DISPLAY = 20

st.set_page_config(
    page_title="SPTEK 공공데이터 AI 검색",
    page_icon="imgs/avatar_streamly.png",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Get help": "https://github.com/sungil",
        "Report a bug": "https://github.com/sungil",
        "About": """
            ### AI-Based API Recommendation Bot
            Powered using Naver Clovax-HCX-003.
            
            GitHub: https://github.com/sungil
            
            The UI source refers to streamly(https://github.com/AdieLaine/Streamly).
            
            공공 데이터 AI 검색 로봇은 data.go.kr 에서 제공 하는 약 1만 2천건의 방대한 공공 데이터 API를 좀더 쉽고 편리하게
            사용자가 검색할 수 있도록 자연어 검색이 가능한 AI 기술을 적용한 서비스 입니다. AI LLM 모델은 
            Naver Clovax-HCX-003가 적용 되어 있으며 웹 UI는 아래의 Streamlit 코드와 라이선스가 적용되어 있습니다. 
            
        """
    }
)

# Title
st.title("공공 데이터 AI 검색 로봇 입니다.")

def img_to_base64(image_path):
    """Convert image to base64."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        logging.error(f"Error converting image to base64: {str(e)}")
        return None

@st.cache_data(show_spinner=False)
def load_and_enhance_image(image_path, enhance=False):
    img = Image.open(image_path)
    if enhance:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.8)
    return img

@st.cache_data(show_spinner=False)
def load_streamlit_updates():
    """Load the latest Streamlit updates from a local JSON file."""
    try:
        with open("data/streamlit_updates.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading JSON: {str(e)}")
        return {}

def display_streamlit_updates():
    """Display the latest updates of the Streamlit."""
    with st.expander("API AI Bot Announcement", expanded=False):
        st.markdown("2024.09 베타 서비스 시작")

def initialize_conversation():
    conversation_history = []
    return conversation_history

@st.cache_data(show_spinner=False)
def get_latest_update_from_json(keyword, latest_updates):
    for section in ["Highlights", "Notable Changes", "Other Changes"]:
        for sub_key, sub_value in latest_updates.get(section, {}).items():
            for key, value in sub_value.items():
                if keyword.lower() in key.lower() or keyword.lower() in value.lower():
                    return f"Section: {section}\nSub-Category: {sub_key}\n{key}: {value}"
    return "No updates found for the specified keyword."

def construct_formatted_message(latest_updates):
    formatted_message = []
    highlights = latest_updates.get("Highlights", {})
    version_info = highlights.get("Version 1.36", {})
    if version_info:
        description = version_info.get("Description", "No description available.")
        formatted_message.append(f"- **Version 1.36**: {description}")

    for category, updates in latest_updates.items():
        formatted_message.append(f"**{category}**:")
        for sub_key, sub_values in updates.items():
            if sub_key != "Version 1.36":  # Skip the version info as it's already included
                description = sub_values.get("Description", "No description available.")
                documentation = sub_values.get("Documentation", "No documentation available.")
                formatted_message.append(f"- **{sub_key}**: {description}")
                formatted_message.append(f"  - **Documentation**: {documentation}")
    return "\n".join(formatted_message)

@st.cache_data(show_spinner=False)
def on_chat_submit(chat_input, latest_updates):
    user_input = chat_input.strip().lower()

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = initialize_conversation()

    st.session_state.conversation_history.append({"role": "user", "content": user_input})

    try:
        assistant_reply = send_post_request(user_input)

        st.session_state.conversation_history.append({"role": "assistant", "content": assistant_reply})
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.history.append({"role": "assistant", "content": assistant_reply})

    except OpenAIError as e:
        logging.error(f"Error occurred: {e}")
        st.error(f"OpenAI Error: {str(e)}")

def initialize_session_state():
    """Initialize session state variables."""
    if "history" not in st.session_state:
        st.session_state.history = []
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

def send_post_request(content):
    url = "http://127.0.0.1:8000/ai/api_recommender"
    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        'content': content
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json().get("reply")
        else:
            logging.error(f"Error: {response.status_code}, {response.text}")
            return f"연결 상태가 좋지 않습니다({response.status_code})."
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return "연결 상태가 좋지 않습니다."

def main():
    """
    Display Streamlit updates and handle the chat interface.
    """
    initialize_session_state()

    if not st.session_state.history:
        initial_bot_message = "안녕하세요! 어떤 데이터를 찾고 계신가요? 제가 관련 API를 찾아 볼께요!"
        st.session_state.history.append({"role": "assistant", "content": initial_bot_message})
        st.session_state.conversation_history = initialize_conversation()

    # Insert custom CSS for glowing effect
    st.markdown(
        """
        <style>
        .cover-glow {
            width: 100%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #330000,
                0 0 10px #660000,
                0 0 15px #990000,
                0 0 20px #CC0000,
                0 0 25px #FF0000,
                0 0 30px #FF3333,
                0 0 35px #FF6666;
            position: relative;
            z-index: -1;
            border-radius: 45px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Load and display sidebar image
    img_path = "imgs/avatar_streamly.png"
    img_base64 = img_to_base64(img_path)
    if img_base64:
        st.sidebar.markdown(
            f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("---")

    # Sidebar for Mode Selection
    mode = st.sidebar.radio("Select Mode:", options=["Chat with AI Bot", "Latest Updates"], index=0)

    st.sidebar.markdown("---")

    # Display basic interactions
    show_basic_info = st.sidebar.checkbox("Show About Service", value=True)
    if show_basic_info:
        st.sidebar.markdown("""
        - 공공 데이터 AI 검색 로봇은 data.go.kr 에서 
        제공하는 약 1만 2천건의 방대한 공공 데이터 API를 
        좀더 쉽고 편리하게 사용자가 검색할 수 있도록 자연어 
        검색이 가능한 AI 기술을 적용한 서비스 입니다. 
        """)

    # Display advanced interactions
    show_advanced_info = st.sidebar.checkbox("Show License and Refrences", value=False)
    if show_advanced_info:
        st.sidebar.markdown("""
        - **LLM**: Naver Hyper Clovax HCX-003.
        - **UI/UX**:  Streamlit v1.37.1 
        """)

    st.sidebar.markdown("---")

    # Load and display image with glowing effect
    # img_path = "imgs/stsidebarimg.png"
    # img_base64 = img_to_base64(img_path)
    # if img_base64:
    #     st.sidebar.markdown(
    #         f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
    #         unsafe_allow_html=True,
    #     )

    st.sidebar.markdown("""
    에스피테크놀러지(주)<br>
    서울시 서초구 효령로 17 청진빌딩<br>
    대표 02-2101-2500 (FAX) 02-2101-2499<br>
    E-mail : info@sptek.co.kr
    """, unsafe_allow_html=True)


    if mode == "Chat with AI Bot":
        chat_input = st.chat_input("어떤 데이터를 찾고 계신가요?")
        if chat_input:
            latest_updates = load_streamlit_updates()
            on_chat_submit(chat_input, latest_updates)

        # Display chat history
        for message in st.session_state.history[-NUMBER_OF_MESSAGES_TO_DISPLAY:]:
            role = message["role"]
            avatar_image = "imgs/avatar_streamly.png" if role == "assistant" else "imgs/stuser.png" if role == "user" else None
            with st.chat_message(role, avatar=avatar_image):
                st.write(message["content"])

    else:
        display_streamlit_updates()

if __name__ == "__main__":
    main()