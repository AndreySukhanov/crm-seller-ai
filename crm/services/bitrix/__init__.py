from .chat_methods import *
from .funnel_methods import *
from .lead_methods import *
from .meet_methods import *
from .base_methods import *
from ..crm_abs import CRM


class Bitrix(CRM):
    def __init__(self, webhook: str):
        self.webhook = webhook

    def _request(self, method: str, payload: Dict[str, Any] = {}) -> Dict[str, Any]:
        return bitrix_request(self.webhook, method, payload)

    def lead_has_custom_field(self, lead_id: str, field_code: str) -> bool:
        lead = get_lead_by_id(self.webhook, lead_id)
        return bool(lead and field_code in lead)

    def update_custom_field(self, lead_id: str, field_code: str, value: Any) -> Optional[bool]:
        return update_custom_field(self.webhook, lead_id, field_code, value)

    def create_lead_meeting(
            self,
            lead_id: str,
            meeting_time: datetime,
            title: str,
            duration_hours: int = 1,
            description: Optional[str] = None, ) -> Optional[str]:
        return create_lead_meeting(self.webhook, lead_id, meeting_time, title, duration_hours, description)

    def get_lead_responsible_free_slots(
            self,
            lead_id: str,
            from_date: datetime,
            to_date: datetime,
    ) -> List[str]:
        return get_lead_responsible_free_slots(self.webhook, lead_id, from_date, to_date)

    def send_message_to_chat(
            self,
            crm_entity: str,
            chat_id: str,
            manager_id: str,
            message: str,
            crm_entity_type: str = "lead",
    ) -> int | None:
        return send_message_to_chat(
            crm_entity=crm_entity,
            chat_id=chat_id,
            manager_id=manager_id,
            message=message,
            crm_entity_type=crm_entity_type,
            webhook=self.webhook,
        )

    def start_dioalog(self, chat_id: str) -> Optional[bool]:
        return start_dioalog(webhook=self.webhook, chat_id=chat_id)

    def switch_dialogue_to_operator(self, chat_id: str) -> Optional[bool]:
        return switch_dialogue_to_operator(webhook=self.webhook, chat_id=chat_id)

    def get_sales_funnel(self) -> Optional[Dict[str, Any]]:
        return get_sales_funnel(self.webhook)

    def get_funnel_lead(self) -> Optional[List[Dict[str, Any]]]:
        return get_funnel_lead(self.webhook)

    def get_funnel_status_by_name(self, name):
        return get_funnel_status_by_name(self.webhook, name)

    def create_new_item_funnel_lead(self, status: str, title_field: str, weight: int):
        return create_new_item_funnel_lead(
            webhook=self.webhook,
            status=status,
            title_field=title_field,
            weight=weight,
        )

    def create_lead_from_contact(self, contact_id: str) -> dict:
        return create_lead_from_contact(self.webhook, contact_id)

    def add_new_lead_to_session(self, chat_id: str, new_lead_id):
        return add_new_lead_to_session(self.webhook, chat_id, new_lead_id)

    def get_latest_lead_id_by_contact(self, contact_id: str):
        return get_latest_lead_id_by_contact(self.webhook, contact_id)

    def get_contact(self, contact_id: str) -> dict:
        return get_contact(self.webhook, contact_id)

    def move_lead_in_funnel(self, new_status: str, id_lead: int):
        return move_lead_in_funnel(
            webhook=self.webhook,
            new_status=new_status,
            id_lead=id_lead,
        )

    def add_lead_comment(self, lead_id: str, message: str) -> Optional[str]:
        return add_lead_comment(self.webhook, lead_id, message)

    def get_lead_by_id(self, lead_id: str) -> Optional[dict]:
        return get_lead_by_id(self.webhook, lead_id)

    def update_lead(self, lead_id: str, fields: Dict[str, Any]) -> Optional[bool]:
        return update_lead(self.webhook, lead_id, fields)

    def get_lead_userfields(self) -> List[dict]:
        return get_lead_userfields(self.webhook)

    def create_crm_custom_field_at_lead(
            self,
            field_code: str,
            form_label: str,
            column_label: str,
            user_type_id: str,
            default_value: str = None,
            xml_id: str = None,
    ):
        return create_crm_custom_field_at_lead(
            self.webhook,
            field_code=field_code,
            form_label=form_label,
            column_label=column_label,
            user_type_id=user_type_id,
            default_value=default_value,
            xml_id=xml_id,
        )

    def get_status_id_by_lead_id(self, lead_id: str) -> str:
        return get_status_id_by_lead_id(webhook=self.webhook, lead_id=lead_id)
    
    def get_classification_by_lead_id(self, lead_id: str) -> str:
        return get_classification_by_lead_id(webhook=self.webhook, lead_id=lead_id)