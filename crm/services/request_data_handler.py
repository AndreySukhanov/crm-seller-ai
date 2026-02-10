import logging

from crm.models import Lead
from crm.services.bitrix import Bitrix
from users.models import Company, User

logger = logging.getLogger(__name__)


def get_crm(company):
    if company and company.crm_name == "bitrix":
        return Bitrix(company.webhook)
    return None


class RequestDataHandler:
    def __init__(self, data):
        self.data = data
        self.event = self.data.get("event")

        self.company = get_company(data)
        if not self.company:
            raise ValueError("Company not found for auth[domain]")

        self.crm: Bitrix = Bitrix(self.company.webhook)

        raw_entity_data = self.data.get("data[PARAMS][CHAT_ENTITY_DATA_2]", "")
        parts = raw_entity_data.split("|") if raw_entity_data else []
        if len(parts) < 6:
            raise ValueError("Invalid data[PARAMS][CHAT_ENTITY_DATA_2] format")

        self.lead_id = parts[1]
        self.contact_id = parts[5]
        logger.info("contact id: %s", self.contact_id)

        self.crm_entity_type = "lead"
        self.chat_id = self.data.get("data[PARAMS][TO_CHAT_ID]")
        self.crm_entity = self.lead_id

        if self.lead_id == "0":
            last_created_lead = self.crm.get_latest_lead_id_by_contact(self.contact_id)
            if last_created_lead:
                self.lead_id = last_created_lead
            else:
                self.lead_id = self.crm.create_lead_from_contact(self.contact_id)
            self.crm_entity_type = "contact"
            self.crm_entity = self.contact_id

        logger.info("resolved lead id: %s", self.lead_id)

        chat_entity_id = data.get("data[PARAMS][CHAT_ENTITY_ID]", "")
        self.channel = chat_entity_id.split("|")[0] if chat_entity_id else None
        self.message = self.data.get("data[PARAMS][MESSAGE]")
        self.is_manager = data.get("data[PARAMS][IS_MANAGER]") == "Y"
        self.is_first_request = None

        self.user = self.get_or_create_user()
        self.lead = self.get_or_create_lead()

    def get_or_create_lead(self):
        lead, created = Lead.objects.get_or_create(
            user=self.user,
            lead_id=self.lead_id,
            defaults={
                "dialog_id": self.chat_id,
                "crm": self.company.crm_name,
            },
        )

        if created:
            self.is_first_request = True
        elif self.chat_id and lead.dialog_id != self.chat_id:
            lead.dialog_id = self.chat_id
            lead.save(update_fields=["dialog_id"])

        return lead

    def get_or_create_user(self):
        username = f"{self.company.crm_name}_{self.chat_id}_{self.company.id}"
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "company": self.company,
                "first_name": self.data.get("data[USER][FIRST_NAME]"),
                "last_name": self.data.get("data[USER][LAST_NAME]"),
            },
        )
        return user


def get_company(data):
    auth_domain = data.get("auth[domain]")
    if not auth_domain:
        return None
    return Company.objects.filter(auth_domain=auth_domain).first()
