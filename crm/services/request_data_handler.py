from crm.models import Lead
from crm.services.bitrix import Bitrix
from users.models import Company, User

import logging

logger = logging.getLogger(__name__)

def get_crm(company):
    if company.crm_name == "bitrix":
        return Bitrix(company.webhook)
class RequestDataHandler:
    def __init__(self, data):
        self.data = data
        self.lead_id = self.data.get("data[PARAMS][CHAT_ENTITY_DATA_2]").split("|")[1]
        self.contact_id = self.data.get("data[PARAMS][CHAT_ENTITY_DATA_2]").split("|")[5]

        logger.info(f"contact id: {self.contact_id}")
        self.crm_entity_type = "lead"
        self.company = get_company(data)
        self.crm: Bitrix = Bitrix(self.company.webhook)
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

        logger.info(f"self.lead_id id: {self.lead_id}")


        self.event = self.data.get("event")
        self.channel = data.get("data[PARAMS][CHAT_ENTITY_ID]").split("|")[0]
        self.message = self.data.get("data[PARAMS][MESSAGE]")
        self.is_manager = data.get("data[PARAMS][IS_MANAGER]") == "Y"
        self.is_first_request = None  # устанавливается в методе get_or_create_lead
        self.user = self.get_or_create_user()
        self.lead = self.get_or_create_lead()


    def get_or_create_lead(self):
        lead, created = Lead.objects.get_or_create(
            user=self.user,
            lead_id=self.lead_id,
            dialog_id=self.chat_id,
        )
        if created:
            self.is_first_request = True

        return lead

    def get_or_create_user(self):
        if not (user:=User.objects.filter(username=f"{self.company.crm_name}_{self.chat_id}_{self.company.id}").first()):
            user, _ = User.objects.get_or_create(
                username=f"{self.company.crm_name}_{self.chat_id}_{self.company.id}",
                company=self.company,
                first_name=self.data.get("data[USER][FIRST_NAME]"),
                last_name=self.data.get("data[USER][LAST_NAME]"),
            )

        return user

def get_company(data):
    auth_domain = data.get("auth[domain]")
    if not auth_domain:
        return None

    company = Company.objects.filter(auth_domain=auth_domain).first()
    return company
