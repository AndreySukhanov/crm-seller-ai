import json
import inspect
from typing import get_type_hints, Optional, Union, get_origin, get_args

from chat.models import Func, Property
# from chat.services.settings import FUNCTIONS
from crm.services.crm_abs import CRM
import logging

from users.models import Company

logger = logging.getLogger(__name__)


def call_gpt_func(choice, crm: CRM):
    function_name = choice.function_call.name
    arguments = json.loads(choice.function_call.arguments)

    # Унифицированный лог: логируем имя функции и все её аргументы
    logger.info(f"GPT вызвал функцию: {function_name} с аргументами: {json.dumps(arguments, ensure_ascii=False)}")

    func = getattr(crm, function_name)
    return func(**arguments)


def get_company_funcs(company: Company):
    # result = FUNCTIONS.copy()
    result = []

    type_mapping = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "list": "array",
        "dict": "object",
        "any": ["string", "number", "boolean", "object", "array", "null"]
    }

    company_funcs = company.funcs.select_related('func').prefetch_related('func__props')

    for company_func in company_funcs:
        func = company_func.func
        properties = func.props.all()

        props = {}
        for prop in properties:
            json_type = type_mapping.get(prop.type, "string")  # default to "string" if unknown
            props[prop.name] = {
                "type": json_type,
                "description": prop.description or ""
            }

        required_props = [prop.name for prop in properties if prop.required]

        result.append({
            "name": func.name,
            "description": func.description or "",
            "parameters": {
                "type": "object",
                "properties": props,
                "required": required_props
            }
        })

    logger.info(f"funcs map: {result}")
    return result



# ================================ Автосоздание функций в бд =============================
def is_optional(annotation):
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        return type(None) in args
    return False


def type_to_str(annotation):
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        non_none = [arg for arg in args if arg is not type(None)]
        return type_to_str(non_none[0])
    elif annotation in (int, str, float, bool):
        return annotation.__name__
    elif annotation is None:
        return "None"
    return str(annotation)


def populate_funcs_from_crm():
    for name, method in inspect.getmembers(CRM, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue

        func_obj, created = Func.objects.get_or_create(
            name=name,
            defaults={
                "description": method.__doc__.strip() if method.__doc__ else ""
            }
        )

        # Очистим старые параметры если уже есть
        if not created:
            func_obj.props.all().delete()

        sig = inspect.signature(method)
        type_hints = get_type_hints(method)

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            annotation = type_hints.get(param_name, str)
            required = not is_optional(annotation) and param.default is param.empty
            if param_name:
                Property.objects.create(
                    func=func_obj,
                    name=param_name,
                    type=type_to_str(annotation),
                    description="",  # можно позже автоматически или вручную заполнить
                    required=required
                )

    logger.info("✅ Синхронизация с CRM завершена.")
