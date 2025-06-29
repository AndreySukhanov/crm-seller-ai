from datetime import datetime
from typing import List

from chat.models import Chat
from crm.services.bitrix.lead_methods import get_custom_field_value_by_lead_id, get_status_id_by_lead_id
from users.models import Company
import logging

logger = logging.getLogger(__name__)




def extend_system_prompt(company: Company, lead_id: str) -> str:
    funnel_steps = company.funnel_steps.filter(use=True)

    # Собираем шаги воронки
    stage_map = {
        f"{funnel_step.name}": f"{funnel_step.status_id}" for funnel_step in funnel_steps
    }
    stage_map_instructions = "\n".join([f"- {k}: {v}" for k, v in stage_map.items()])

    # Собираем информацию о функциях компании
    func_instructions = ""
    funcs = company.funcs.all()
    if funcs.exists():
        func_instructions += "# ПРАВИЛА ВЫЗОВА GPT-ФУНКЦИЙ\n"
        for func in funcs:
            func_instructions += (
                f"\n## {func.func.name} {func.func_context}\n"
                f"{func.prompt.strip()}\n"
            )

    status_id = get_status_id_by_lead_id(webhook=company.webhook, lead_id=lead_id)

    fields = company.lead_fields.all()
    fields_values = ""
    for field in fields:
        lead_field_value = get_custom_field_value_by_lead_id(
            webhook=company.webhook, lead_id=lead_id, field_code=field.field_code)
        fields_values += f"Текущее значение поля {field.field_code}: {lead_field_value}\n"

    return (
            company.promt.strip()
            + f"\n\n# ИНФОРМАЦИЯ О КЛИЕНТЕ\n"
              f"Текущий `lead_id`: {lead_id}\n"
              f"{fields_values}"
              f"Текущий статус лида: {status_id}\n"
              f"Текущая дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
              f"# ЭТАПЫ ВОРОНКИ ПРОДАЖ {company.name} ({company.crm_name}):\n"
              f"{stage_map_instructions}\n\n"
              f"{func_instructions}"
    )


def build_messages(user_query: str, retrieved: List[dict], chat: Chat, lead_id: int, company: Company) -> List[dict]:
    # Формируем блок контекста
    context = ""
    for i, doc in enumerate(retrieved, 1):
        header = doc.get("section") or doc.get("category") or "Фрагмент"
        body = doc.get("text") or doc.get("description") or doc.get("title", "")
        compat = ", ".join(doc.get("compatibility", []))
        benefits = ", ".join(doc.get("benefits", [])) if doc.get("benefits") else ""

        context += f"[{header}]\n{body.strip()}\n"
        if compat:
            context += f"Совместимость: {compat}\n"
        if benefits:
            context += f"Выгоды: {benefits}\n"
        context += "\n"

    # Сбор полного system prompt-а
    full_prompt = extend_system_prompt(company, lead_id) + "\n\nКонтекст:\n" + context.strip()
    logger.info(full_prompt)

    # Построение структуры сообщений
    messages = [{"role": "system", "content": full_prompt}]
    messages.extend(chat.get())
    messages.append({"role": "user", "content": user_query.strip()})
    return messages
