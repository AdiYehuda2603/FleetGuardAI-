# -*- coding: utf-8 -*-
"""
Chat Manager - ניהול שיחות והיסטוריה
"""

import uuid
from datetime import datetime
import json


class ChatManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_new_conversation(self, title=None, template_id=None):
        """יוצר שיחה חדשה"""
        conversation_id = f"CONV-{uuid.uuid4().hex[:12].upper()}"

        if not title:
            title = f"שיחה חדשה - {datetime.now().strftime('%d/%m/%Y %H:%M')}"

        self.db.save_conversation(conversation_id, title, template_id)
        return conversation_id

    def load_conversation(self, conversation_id):
        """טוען שיחה קיימת"""
        history_df = self.db.get_conversation_history(conversation_id)

        messages = []
        for _, row in history_df.iterrows():
            messages.append({
                "role": row['role'],
                "content": row['content']
            })

        return messages

    def save_user_message(self, conversation_id, content):
        """שומר הודעת משתמש"""
        self.db.save_message(conversation_id, "user", content)

    def save_assistant_message(self, conversation_id, content):
        """שומר הודעת עוזר"""
        self.db.save_message(conversation_id, "assistant", content)

    def get_template_prompt(self, template_id):
        """מחזיר את הפרומפט של תבנית"""
        template = self.db.get_template(template_id)

        if template is None:
            return None

        try:
            config = json.loads(template['configuration'])
            return config.get('prompt', '')
        except:
            return None

    def apply_template(self, template_id):
        """מיישם תבנית ויוצר שיחה חדשה"""
        template = self.db.get_template(template_id)

        if template is None:
            return None, None

        # יצירת שיחה חדשה עם התבנית
        conversation_id = self.create_new_conversation(
            title=f"{template['template_name']} - {datetime.now().strftime('%d/%m/%Y')}",
            template_id=template_id
        )

        # עדכון last_used
        self.db.update_template_last_used(template_id)

        # החזרת הפרומפט
        prompt = self.get_template_prompt(template_id)

        return conversation_id, prompt
