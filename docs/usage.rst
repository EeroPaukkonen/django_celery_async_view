=====
Usage
=====

To use django_celery_async_view in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django_celery_async_view.apps.DjangoCeleryAsyncViewConfig',
        ...
    )

Add django_celery_async_view's URL patterns:

.. code-block:: python

    from django_celery_async_view import urls as django_celery_async_view_urls


    urlpatterns = [
        ...
        url(r'^', include(django_celery_async_view_urls)),
        ...
    ]
