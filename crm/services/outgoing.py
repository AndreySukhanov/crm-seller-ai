import requests

from crm.services.request_data_handler import get_company, get_crm
import logging
logger = logging.getLogger(__name__)


def outgoing(data):
    lead_id = data.get("data[FIELDS][ID]")
    company = get_company(data)

    if outgoing_conf := company.outgoing.all().first():
        crm = get_crm(company)
        stage = crm.get_status_id_by_lead_id(lead_id)
        need_stage = crm.get_funnel_status_by_name(outgoing_conf.stage_name)
        logger.info(f"{outgoing_conf.stage_name}")
        logger.info(f"outgoing lead {lead_id} stage: {stage}")
        logger.info(f"outgoing lead need_stage: {need_stage}")
        if stage == "IN_PROCESS":
            lead = crm.get_lead_by_id(lead_id)
            contact = crm.get_contact(lead.get("CONTACT_ID"))
            logger.info(f"outgoing contact {contact}")
            recipient = contact.get("PHONE")[0]["VALUE"]
            payload = {
                "recipient": recipient,
                "body": outgoing_conf.start_message,
            }
            headers = {
                "Authorization": outgoing_conf.wappi_token,
                "Content-Type": "application/json"
            }
            resp = requests.post(
                f"https://wappi.pro/api/sync/message/send?profile_id={outgoing_conf.wappi_profile}",
                json=payload,
                headers=headers
            )
            resp.raise_for_status()
            logger.info(f"outgoing message successfully sent to {recipient}")
