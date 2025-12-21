# -*- coding: utf-8 -*-
"""
Enhanced Chat UI - Professional, clean, and minimalistic chat interface
"""

import streamlit as st
import json
from datetime import datetime


def render_chat_with_history(db, auth):
    """
    Renders an enhanced, professional chat interface with conversation history and templates

    Features:
    - Clean, minimalistic design
    - Structured message presentation
    - Improved conversation management
    - Better visual hierarchy
    - Responsive layout
    """
    from src.chat_manager import ChatManager
    from src.ai_engine import FleetAIEngine

    # Initialize chat manager
    chat_mgr = ChatManager(db)

    # === SIDEBAR: Conversations & Templates ===
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💬 ניהול שיחות")

        # New conversation button
        if st.button("➕ שיחה חדשה", use_container_width=True, type="primary"):
            new_conv_id = chat_mgr.create_new_conversation()
            st.session_state.conversation_id = new_conv_id
            st.session_state.messages = []
            st.session_state.conversation_title = f"שיחה - {datetime.now().strftime('%d/%m')}"
            st.rerun()

        st.markdown("---")

        # Quick templates
        st.markdown("### 📊 תבניות")

        templates_df = db.get_all_templates()

        if not templates_df.empty:
            with st.container():
                for _, template in templates_df.iterrows():
                    if st.button(
                        f"📋 {template['template_name']}",
                        key=f"tpl_{template['template_id']}",
                        use_container_width=True,
                        help=template.get('description', '')
                    ):
                        # Apply template
                        conv_id, prompt = chat_mgr.apply_template(template['template_id'])

                        if prompt:
                            st.session_state.conversation_id = conv_id
                            st.session_state.messages = []
                            st.session_state.conversation_title = template['template_name']
                            st.session_state.pending_template_prompt = prompt
                            st.rerun()

        st.markdown("---")

        # Conversation history
        st.markdown("### 📜 שיחות קודמות")

        conversations_df = db.get_all_conversations(limit=10)

        if not conversations_df.empty:
            with st.container():
                for _, conv in conversations_df.iterrows():
                    # Format date
                    try:
                        last_updated = datetime.fromisoformat(conv['last_updated'])
                        time_str = last_updated.strftime('%d/%m')
                    except:
                        time_str = ""

                    # Truncate title
                    title_short = conv['title'][:20] + "..." if len(conv['title']) > 20 else conv['title']

                    col1, col2 = st.columns([5, 1])

                    with col1:
                        if st.button(
                            f"💬 {title_short}",
                            key=f"conv_{conv['conversation_id']}",
                            help=f"{conv['title']} | {time_str}",
                            use_container_width=True
                        ):
                            st.session_state.conversation_id = conv['conversation_id']
                            st.session_state.messages = chat_mgr.load_conversation(conv['conversation_id'])
                            st.session_state.conversation_title = conv['title']
                            st.rerun()

                    with col2:
                        if st.button("🗑", key=f"del_{conv['conversation_id']}", help="מחק"):
                            db.delete_conversation(conv['conversation_id'])
                            if st.session_state.get('conversation_id') == conv['conversation_id']:
                                new_conv_id = chat_mgr.create_new_conversation()
                                st.session_state.conversation_id = new_conv_id
                                st.session_state.messages = []
                                st.session_state.conversation_title = "שיחה חדשה"
                            st.rerun()
        else:
            st.caption("אין שיחות שמורות")

    # === MAIN CHAT AREA ===

    # Header
    st.markdown("### 🤖 אנליסט AI")
    if 'conversation_title' in st.session_state:
        st.caption(f"📝 {st.session_state.conversation_title}")

    st.markdown("---")

    # Quick guide (collapsible)
    with st.expander("💡 דוגמאות לשאלות", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **תפעול ותחזוקה:**
            - כמה עלה תחזוקה החודש?
            - איזה מוסך הכי זול?
            - מה הקילומטראז' של רכב X?
            """)
        with col2:
            st.markdown("""
            **אסטרטגיה וניהול:**
            - איזה דגם הכי אמין?
            - אילו רכבים כדאי להחליף?
            - מה הרכבים המצטיינים?
            """)

    st.markdown("---")

    # Initialize conversation if needed
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = chat_mgr.create_new_conversation()
        st.session_state.messages = []
        st.session_state.conversation_title = "שיחה חדשה"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Handle pending template prompt
    if "pending_template_prompt" in st.session_state:
        pending_prompt = st.session_state.pending_template_prompt
        del st.session_state.pending_template_prompt

        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(pending_prompt)

        st.session_state.messages.append({"role": "user", "content": pending_prompt})
        chat_mgr.save_user_message(st.session_state.conversation_id, pending_prompt)

        # Get AI response
        api_key = auth.get_api_key()
        if api_key:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("מנתח..."):
                    ai_engine = FleetAIEngine()
                    response = ai_engine.ask_analyst(pending_prompt)
                    st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})
            chat_mgr.save_assistant_message(st.session_state.conversation_id, response)

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for idx, message in enumerate(st.session_state.messages):
            avatar = "👤" if message["role"] == "user" else "🤖"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    # Chat input
    st.markdown("---")
    prompt = st.chat_input("הקלד שאלה...")

    if prompt:
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})
        chat_mgr.save_user_message(st.session_state.conversation_id, prompt)

        # Check API key
        api_key = auth.get_api_key()
        if not api_key:
            with st.chat_message("assistant", avatar="🤖"):
                st.error("⚠️ חסר מפתח API. אנא הוסף מפתח ב-.env")
        else:
            # Get AI response
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("מנתח..."):
                    ai_engine = FleetAIEngine()
                    response = ai_engine.ask_analyst(prompt)
                    st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})
            chat_mgr.save_assistant_message(st.session_state.conversation_id, response)


# דוגמה לשימוש ב-main.py:
# =============================
# with tab2:
#     from src.chat_ui_upgrade import render_chat_with_history
#     render_chat_with_history(db, auth)
