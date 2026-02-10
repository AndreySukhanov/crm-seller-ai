from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

import logging

from chat.services import chat_with_gpt
from .services.outgoing import outgoing
from .services.request_data_handler import RequestDataHandler
from .services.topnlab.topnlab_integration import TopnlabAPI

logger = logging.getLogger(__name__)


class WebhookView(APIView):
    def post(self, request, *args, **kwargs):
        logger.info("Webhook payload received: %s", request.data)
        event = request.data.get("event")

        if event in ("ONCRMLEADADD", "ONCRMLEADUPDATE"):
            outgoing(request.data)

        if event == "ONIMBOTMESSAGEADD":
            try:
                rdh = RequestDataHandler(request.data)
            except ValueError as exc:
                logger.warning("Invalid webhook payload: %s", exc)
                return Response(
                    {"status": "error", "detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if rdh.is_manager:
                return Response(
                    {
                        "status": "success",
                        "is_manager": rdh.is_manager,
                    },
                    status=status.HTTP_200_OK,
                )

            answer_gpt = chat_with_gpt(rdh=rdh)
            if answer_gpt:
                rdh.crm.send_message_to_chat(
                    crm_entity=rdh.crm_entity,
                    chat_id=rdh.chat_id,
                    manager_id=1,
                    message=answer_gpt,
                    crm_entity_type=rdh.crm_entity_type,
                )

                if rdh.company.use_topnlab:
                    api_topnlab = TopnlabAPI(appkey=rdh.company.api_key_topnlab)
                    api_topnlab.create_realty(
                        owner_fio=rdh.user.last_name,
                        owner_phone=rdh.user.phone,
                        action=1,
                        object_type="flat",
                    )

            return Response(
                {
                    "status": "success",
                    "received_data": answer_gpt,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "status": "success",
                "received_data": request.data,
            },
            status=status.HTTP_200_OK,
        )
