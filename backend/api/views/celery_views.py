# backend/api/views/celery_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from celery.result import AsyncResult
from order_service.celery import app


class TaskStatusView(APIView):
    """
    Представление для получения статуса асинхронной задачи Celery.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        """
        Получение статуса задачи по ее ID.
        """
        task = AsyncResult(task_id, app=app)

        if task.state == 'PENDING':
            response = {
                'status': 'pending',
                'message': 'Задача находится в очереди на выполнение'
            }
        elif task.state == 'STARTED':
            response = {
                'status': 'started',
                'message': 'Задача выполняется'
            }
        elif task.state == 'SUCCESS':
            response = {
                'status': 'success',
                'message': 'Задача успешно выполнена',
                'result': task.result
            }
        elif task.state == 'FAILURE':
            response = {
                'status': 'failure',
                'message': 'Задача завершилась с ошибкой',
                'error': str(task.result)
            }
        else:
            response = {
                'status': task.state,
                'message': 'Неизвестный статус задачи'
            }

        return Response(response)
