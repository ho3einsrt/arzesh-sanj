import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .finance import calculate, FinanceError

@csrf_exempt
def calculation(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'فقط درخواست POST پذیرفته می‌شود.'}, status=405)
    try:
        data = json.loads(request.body, parse_float=Decimal)
        if not isinstance(data, dict):
            raise FinanceError('ورودی باید یک شیء باشد.')
        result = calculate(data)
        return JsonResponse({key: str(value) for key, value in result.items()})
    except (ValueError, UnicodeDecodeError) as exc:
        return JsonResponse({'error': str(exc) if isinstance(exc, FinanceError) else 'ورودی JSON معتبر نیست.'}, status=400)
