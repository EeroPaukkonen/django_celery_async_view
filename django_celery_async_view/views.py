# -*- coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render
try:
    from django.views import View
except ImportError:
    from django.views.generic import View


from django_celery_async_view.task_helpers import open_result


class _BaseView(View):
    allow_no_user = True

    def has_permission(self, opened_result):
        if opened_result['user_id'] is None:
            # File has no owner
            if not self.allow_no_user:
                raise Exception('user_id is None while allow_no_user=True')
            else:
                return True
        return opened_result['user_id'] == self.request.user.id

    def get_user_id(self, request):
        user_id = request.user.id
        if user_id is None and not self.allow_no_user:
            raise Exception('user_id is None')
        return user_id


class AbstractAsyncView(_BaseView):
    """
    Define:
        task =  # set some celery task
    """
    initial_interval = 20000
    poll_interval = 5000

    # Set this if using render_loading_page
    loading_page_template = None

    context = None

    # This needs to be set
    task = None

    eager = False

    def get(self, request):
        """
        Returns one of the following
        # Phase 1. Loading page
        # Phase 2. Not ready (JsonResponse)
        # Phase 3. Ready+Html (JsonResponse)
        :param request:
        :return:
        """
        if self.eager:
            return self.eager_response(request)
        if self.task is None:
            raise ValueError('Define task. task should be celery task.')

        task_id = request.GET.get('task_id')

        if task_id is None:
            # Phase 1. Loading page
            task_id = self.task.delay(
                user_id=self.get_user_id(request)
            )
            return self.render_loading_page(request, task_id)

        result = self.task.AsyncResult(task_id)
        # Ask: There's also no way to reliably check if a task exists in the queue
        # -> invalid task_id is not detected
        if not result.ready():
            # Phase 2. Not ready (JsonResponse)
            return JsonResponse({
                'ready': False
            })
        else:
            # Phase 3. Ready+Html (JsonResponse)
            result = result.get()
            return self.create_html_response(result)

    def eager_response(self, request):
        """
        Used for testing or disabling the three step proses.
        :param request:
        :return:
        """
        # Phase 1.
        result = self.task(user_id=self.get_user_id(request))
        # Phase 3.
        return self.create_html_response(result, json_response=False)

    def render_loading_page(self, request, task_id):
        """
        # Phase 1.
        :param request:
        :param task_id:
        :return:
        """
        if self.loading_page_template is None:
            raise NotImplementedError()
        context = {
            'view_title': 'Loading...',
            'task_id': task_id,
            'initial_interval': self.initial_interval,
            'poll_interval': self.poll_interval
        }
        if self.context is not None:
            context.update(self.context)

        return render(request, self.loading_page_template, context)

    def create_html_response(self, result, json_response=True):
        """
        # Phase 3. Ready+Html (JsonResponse)
        :param result:
        :return:
        """
        opened_result = open_result(result)
        if opened_result is None:
            return HttpResponseBadRequest()
        if not self.has_permission(opened_result):
            raise PermissionDenied
        html_str = opened_result['content']
        if not html_str:
            return HttpResponseBadRequest()
        if json_response:
            return JsonResponse({
                'ready': True,
                'html': html_str
            })
        return HttpResponse(html_str)


class AsyncDownloadView(_BaseView):
    """
    Extend AbstractAsyncDownloadTask
        implement create_file()
    Extend AsyncDownloadView
        Define
            task = <extended AbstractAsyncDownloadTask>
        Implement
            setup()
                Set following (optional)
                    create_file_args
                    create_file_kwargs
    """
    create_file_args = None
    create_file_kwargs = None
    task = None

    eager = False

    def setup(self, request):
        """
        This should be implemented
        Set following
            create_file_function
            create_file_args
            create_file_kwargs
        Called in no_task_id() # Phase 1.
        :param request:
        :return:
            HttpResponse if something failed
            else None
        """
        raise NotImplementedError('Implement this when extending.')

    def get(self, request):
        if self.eager:
            return self.eager_response(request)

        if self.task is None:
            raise ValueError(
                'Define task. '
                'Task should be celery task extending AbstractAsyncDownloadTask.')

        task_id = request.GET.get('task_id')
        download = request.GET.get('download', '').strip().lower()
        download = download == 'true' or download == '1'

        if task_id is None:
            # Phase 1.
            return self.no_task_id(request)

        result = self.task.AsyncResult(task_id)
        if not download:
            # Phase 2.
            return self.is_file_ready(result)
        else:
            # Phase 3.
            result = result.get()
            return self.get_file_response(result)

    def eager_response(self, request):
        """
        Used for testing or disabling the three step proses.
        :param request:
        :return:
        """
        # Phase 1.
        setup_return = self.setup(request)
        if isinstance(setup_return, HttpResponse):
            return setup_return

        result = self.task(
            user_id=self.get_user_id(request),
            *(self.create_file_args or []),
            **(self.create_file_kwargs or {})
        )
        # Phase 3.
        return self.get_file_response(result)

    def no_task_id(self, request):
        """
        Phase 1.
        Start creating file
        Returns:
        """
        setup_return = self.setup(request)
        if isinstance(setup_return, HttpResponse):
            return setup_return

        task_result = self.task.delay(
            user_id=self.get_user_id(request),
            *(self.create_file_args or []),
            **(self.create_file_kwargs or {})
        )
        task_id = task_result.task_id
        return JsonResponse({
            'task_id': task_id,
            'ready': task_result.ready()
        })

    def is_file_ready(self, result):
        """
        Phase 2.
        Is file ready
        Returns:
        """
        return JsonResponse({
            'ready': result.ready()
        })

    def get_file_response(self, result):
        """
        Phase 3.
        Get file
        Returns:

        """
        opened_result = open_result(result)
        if opened_result is None:
            return HttpResponseBadRequest()
        if not self.has_permission(opened_result):
            raise PermissionDenied

        return self.file_instance_to_file_response(opened_result)

    def file_instance_to_file_response(self, opened_result):
        response = HttpResponse(content_type=opened_result['mimetype'])
        response['Content-Disposition'] = u'attachment; filename={}'.format(
            opened_result['filename'])
        response.write(opened_result['content'])
        return response
