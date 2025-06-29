from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Company
from users.stats import get_company_stats
import logging

logger = logging.getLogger(__name__)


# Create your views here.
@csrf_exempt
def stats_view(request):
    return render(request, 'stats/index.html')


class StatsView(APIView):
    def get(self, request):
        code = request.GET.get("code")
        if not code:
            return Response({"error": "Code parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            company = Company.objects.get(stat_code=code)
        except Company.DoesNotExist:
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)

        data = get_company_stats(company)
        logger.info("stats data", data)
        return Response(data)

