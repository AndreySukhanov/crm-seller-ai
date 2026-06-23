import json
import openai
from datetime import datetime
from django.utils import timezone

from chat.models import Chat
from chat.services.build_history import build_messages
from chat.services.documents import load_index, retrieve
from chat.services.funcs import get_company_funcs, call_gpt_func
from chat.services.settings import CHAT_MODEL
from conf import settings
from crm.services import bitrix
from crm.services.crm_abs import CRM
from crm.services.request_data_handler import RequestDataHandler
from crm.models import Lead
from users.models import Company
import logging

logger = logging.getLogger(__name__)
openai.api_key = settings.OPENAI_API_KEY
if settings.OPENAI_BASE_URL:
    openai.base_url = settings.OPENAI_BASE_URL


class GPT:
    def __init__(self, rdh: RequestDataHandler, chat: Chat):
        self.rdh: RequestDataHandler = rdh
        self.chat = chat
        self.index, self.all_docs = load_index(rdh.company)

    def ask_gpt(self):
        return ask_gpt(
            self.index, self.all_docs, self.rdh.message,
            self.chat, self.rdh.lead_id, self.rdh.company,
            self.rdh.crm
        )



def ask_gpt(index, docs, query: str, chat: Chat, lead_id: int, company: Company, crm) -> str:
    # Обновляем время последней активности лида
    # try:
    #     lead_obj = Lead.objects.get(lead_id=lead_id)
    #     lead_obj.last_activity = timezone.now()
    #     lead_obj.save(update_fields=['last_activity'])
    #     logger.info(f"Updated last_activity for lead {lead_id}")
    # except Lead.DoesNotExist:
    #     logger.warning(f"Lead with id {lead_id} not found, cannot update last_activity")

    # retrieved = retrieve(index, docs, query)
    # if not retrieved:
    #     categories = sorted({doc.get("category", "Без категории") for doc in docs})
    #     fallback = (
    #             "Благодарим за обращение. К сожалению, по вашему запросу ничего не найдено.\n\n"
    #             "Вот категории товаров, которые у нас есть:\n\n"
    #             + "\n".join(f"• {cat}" for cat in categories)
    #     )
    #     chat.add("user", query)
    #     chat.add("assistant", fallback)
    #     return fallback
    # messages = build_messages(query, retrieved, chat, lead_id, company)
    messages = build_messages(query, [], chat, lead_id, company)
    try:
        resp = openai.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            functions=get_company_funcs(company),
            function_call="auto",
            response_format={"type": "json_object"}
        )
        choice = resp.choices[0].message
        if resp.choices[0].message.content:
            json_msg = json.loads(resp.choices[0].message.content)
            fields = company.lead_fields.all()
            for f in fields:
                if f.field_code in json_msg:
                    crm.update_custom_field(lead_id=lead_id, field_code=f.field_code, value=json_msg[f.field_code])
                    logger.info(f"Обновлено поле {f.field_code} {json_msg[f.field_code]}")

            if json_msg.get("stage"):
                if chat.stage != json_msg["stage"]:
                    chat.stage = json_msg["stage"]
                    if company.off_gpt_on_stage and crm.get_funnel_status_by_name(company.off_gpt_on_stage) == json_msg["stage"]:
                        chat.gpt_enabled = False
                    chat.save()
                    crm.move_lead_in_funnel(id_lead=lead_id, new_status=json_msg["stage"])
                    logger.info(f"Лид передвинут в воронку {json_msg['stage']}")
            logger.info(f"json answer {json_msg}")

        logger.info(f"tool_calls {choice.tool_calls}")
        # Если GPT хочет вызвать функцию
        if choice.function_call:
            function_name = choice.function_call.name
            arguments = json.loads(choice.function_call.arguments)

            logger.info(f"GPT вызвал функцию: {function_name} с аргументами: {arguments}")

            # Логика обработки функции bitrix_get_free_slots
            if function_name == "bitrix_get_free_slots":
                slots = bitrix.get_lead_responsible_free_slots(
                    # settings.BITRIX_WEBHOOK,
                    company.webhook,
                    arguments["lead_id"],
                    datetime.fromisoformat(arguments["from_date"]),
                    datetime.fromisoformat(arguments["to_date"])
                )
                result = {"slots": slots}

            # Логика обработки функции bitrix_create_meeting
            elif function_name == "bitrix_create_meeting":
                meeting_id = bitrix.create_lead_meeting(
                    # settings.BITRIX_WEBHOOK,
                    company.webhook,
                    arguments["lead_id"],
                    datetime.fromisoformat(arguments["meeting_time"]),
                    arguments["title"],
                    arguments.get("duration_hours", 1),
                    arguments.get("description")
                )
                result = {"meeting_id": meeting_id}

            # Другие функции (если есть)
            else:
                result = call_gpt_func(choice, crm)

            # Вбрасываем ответ от функции обратно в GPT
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": choice.function_call,
                "name": function_name
            })
            messages.append({
                "role": "function",
                "name": function_name,
                "content": json.dumps(result)
            })

            follow_up = openai.chat.completions.create(
                model=CHAT_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "json_object"},
            )
            json_msg = json.loads(follow_up.choices[0].message.content)
            if json_msg.get("stage"):
                if chat.stage != json_msg["stage"]:
                    chat.stage = json_msg["stage"]
                    if company.off_gpt_on_stage and crm.get_funnel_status_by_name(company.off_gpt_on_stage) == json_msg["stage"]:
                        chat.gpt_enabled = False
                    chat.save()
                    crm.move_lead_in_funnel(id_lead=lead_id, new_status=json_msg["stage"])
                    logger.info(f"Лид передвинут в воронку {json_msg['stage']}")

            answer = json_msg.get("message").replace('\\n', '\n')
            chat.add("user", query)
            chat.add("assistant", answer)
            logger.info(f"Ответ GPT после вызова функции: {json_msg}")
            return answer

        # Обычный ответ без вызова функции
        answer = json_msg.get("message").replace('\\n', '\n')
        chat.add("user", query)
        chat.add("assistant", answer)
        logger.info(f"Ответ GPT без функции: {answer}")
        return answer

    except openai.OpenAIError as e:
        logger.exception("OpenAI API error: %s", e)
        return "Произошла ошибка при обращении к ИИ-серверу. Попробуйте позже."
