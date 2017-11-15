
========================
django_celery_async_view
========================

.. image:: https://travis-ci.org/EeroPaukkonen/django_celery_async_view.svg?branch=master
    :target: https://travis-ci.org/EeroPaukkonen/django_celery_async_view

.. image:: https://codecov.io/gh/EeroPaukkonen/django_celery_async_view/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/EeroPaukkonen/django_celery_async_view

Asynchronously load view or download file in django.
This is done by rendering view or creating file in celery task and polling it in javascript.

-------------
Documentation
-------------

The full documentation is at https://django_celery_async_view.readthedocs.io.

----------
Quickstart
----------

Install django_celery_async_view::

    pip install django_celery_async_view

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django_celery_async_view',
        ...
    )

Features
========

This package includes two separate features: AsyncView and AsyncDownload.

AsyncView
---------
example_app.views.py

.. code-block:: python

    class ExampleView(AsyncDownloadView):
        task = example_view_task

example_app.tasks.py

.. code-block:: python

    @shared_task
    def example_view_task(user_id):
        return AsyncViewReturnHTML().run(
            user_id=user_id,
            html_string=create_html_example(...)
        )

example_download_page.html

.. code-block:: html

    <!-- jQuery before django_celery_async_view -->
    <script type="text/javascript" src="{% static "path/to/jquery.js" %}"></script>
    <script type="text/javascript" src="{% static "django_celery_async_view/django_celery_async_view.js" %}"></script>
    <script>
        var task_id = '{{task_id}}';
        var poll_interval = 10000;
        AsyncViews.initAsyncView(poll_interval, task_id);
    </script>

AsyncDownload
-------------

example_app.views.py

.. code-block:: python

    class ExampleDownloadView(AsyncDownloadView):
        task = my_download_task

example_async_page.html

.. code-block:: html

    <script src="{% static "django_celery_async_view/django_celery_async_view.js" %}"></script>

      <script>
          $(document).ready(function(){
              var poll_interval = 5 * 1000;  // 5s
              var task_id = '{{task_id}}';
              AsyncViews.initAsyncView(poll_interval, task_id);
          });
      </script>

example_app.tasks.py

.. code-block:: python

  @shared_task
  def example_download_task(*args, **kwargs):
    return MyDownloadCreateFile().run(*args, **kwargs)

  class ExampleDownloadCreateFile(AbstractAsyncDownloadCreateFile):
    def create_file(self, some_arg):
      # do stuff to create:
      # file_content, filename, mimetype
      return file_content, filename, mimetype

example_download_page.html

.. code-block:: html

    <!-- jQuery before django_celery_async_view -->
    <script type="text/javascript" src="{% static "path/to/jquery.js" %}"></script>
    <script type="text/javascript" src="{% static "django_celery_async_view/django_celery_async_view.js" %}"></script>
    <button>DOWNLOAD</button>
    <button class="async-download-button"
            data-href="/example-download/" data-poll-interval="5000">
        Async Download
    </button>


Configurations
==============

settings.py

.. code-block:: python

    ASYNC_VIEW_TEMP_FILE_DURATION_MS = 10 * 60 * 1000  # 10min

-----------------------
Running Example Project
-----------------------

Requires redis.
Does not require postgres (tests require postgres)

::

    # setup
    # install redis
    cd example
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate

    # run:
    # run redis (if not running)
    celery worker -A example
    python manage.py runserver


-------------
Running Tests
-------------

Tests are run against example project?
Tests require postgres and

    A) env var POSTGRES_PASSWORD set
    B) or no postgres server authentication

::

    virtualenv venv
    source venv/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

-----------
Development
-----------

What needs to be fixed for Python3 support
==========================================

1) copy celerytest project and set celerytest.__init__ imports to absolute

::

    celerytest.__init__.py:1: in <module>
    from config import CELERY_TEST_CONFIG, CELERY_TEST_CONFIG_MEMORY
    ImportError: No module named 'config'

2) AsyncResult(task_id).wait(timeout=5, interval=0.5) and possibly result.get() will break.

::

    example\example\tests\test_async_views.py:50: in phase3
    example_view_task.AsyncResult(task_id).wait(timeout=5, interval=0.5)

        if meta:
                self._maybe_set_cache(meta)
                status = meta['status']
                if status in PROPAGATE_STATES and propagate:
    >               raise meta['result']
    E               TypeError: exceptions must derive from BaseException

    celery\result.py:175: TypeError


Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
