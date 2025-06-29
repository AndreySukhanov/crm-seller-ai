from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class CRM(ABC):
    @abstractmethod
    def _request(self, method: str, payload: Dict[str, Any] = {}) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_custom_field(self, lead_id: str, field_code: str, value: Any) -> Optional[bool]:
        pass

    @abstractmethod
    def create_lead_meeting(
            self,
            lead_id: str,
            meeting_time: datetime,
            title: str,
            duration_hours: int = 1,
            description: Optional[str] = None
    ) -> Optional[str]:
        pass

    @abstractmethod
    def get_lead_responsible_free_slots(
            self,
            lead_id: str,
            from_date: datetime,
            to_date: datetime
    ) -> List[str]:
        pass

    @abstractmethod
    def send_message_to_chat(
            self,
            crm_entity: str,
            chat_id: str,
            manager_id: str,
            message: str,
            crm_entity_type: str = "lead"
    ) -> Optional[int]:
        pass

    @abstractmethod
    def create_lead_from_contact(self, contact_id: str) -> Optional[bool]:
        pass

    @abstractmethod
    def get_latest_lead_id_by_contact(self, contact_id: str):
        pass

    @abstractmethod
    def get_contact(self, contact_id: str) -> Optional[bool]:
        pass

    @abstractmethod
    def start_dioalog(self, chat_id: str) -> Optional[bool]:
        pass

    @abstractmethod
    def switch_dialogue_to_operator(self, chat_id: str) -> Optional[bool]:
        pass

    @abstractmethod
    def get_sales_funnel(self) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_funnel_lead(self) -> Optional[List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def create_new_item_funnel_lead(
            self,
            status: str,
            title_field: str,
            weight: int
    ):
        pass

    @abstractmethod
    def move_lead_in_funnel(
            self,
            new_status: str,
            id_lead: int
    ):
        pass

    @abstractmethod
    def add_lead_comment(self, lead_id: str, message: str) -> Optional[str]:
        pass

    @abstractmethod
    def get_lead_by_id(self, lead_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def update_lead(self, lead_id: str, fields: Dict[str, Any]) -> Optional[bool]:
        pass

    @abstractmethod
    def create_crm_custom_field_at_lead(
            self,
            field_code: str,
            form_label: str,
            column_label: str,
            user_type_id: str,
            default_value: str = None,
            xml_id: str = None
    ):
        pass

    @abstractmethod
    def get_status_id_by_lead_id(self, lead_id: str) -> str:
        pass

    @abstractmethod
    def get_funnel_status_by_name(self, name: str):
        pass

    @abstractmethod
    def get_classification_by_lead_id(self, lead_id) -> str:
        pass
