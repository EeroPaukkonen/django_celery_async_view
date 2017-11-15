/**
 * =========
 * AsyncView
 * =========
 *
 * How to use
 * ----------
 * asyncViews.initAsyncView("some-url", 10000, "543-t43-56-f3453")
 *
 * =============
 * AsyncDownload
 * =============
 *
 * How to use
 * ----------
 * #1 Bind listener
 *      $('some-download-button-selector').on('click', function(){
 *          asyncViews.startFileCreation(
 *              "some-url", 10000)
 *      })
 * #2 User e.g. clicks download button
 *
 * What happens
 * # Phase 1. ajax GET base_url
 *      returns {"task_id": "<task_id>"}
 * # Phase 2. ajax GET base_url?task_id=<task_id>
 *     returns {"ready": "<is the task ready>"}
 * # Phase 3.
 *     window.href=base_url?task_id=<task_id>&download=true
 *
 *
 * @type {{createAsyncDownloadListener, createUrl, startFileCreation, pollIfFileIsNotReady, pollIsFileReady, downloadFile, initAsyncView}}
 */
var AsyncViews = (function(){

    return {

        max_polls: 20,

        // =========
        // AsyncView
        // =========
        /**
         * @param options
         * @param options.poll_interval
         *      in milliseconds
         *      integer
         *      or
         *      array of integers e.g. [500, 2500, 10000]
         *      The poll interval will be taken from the array in order
         *      last is used when none left
         * @param options.max_polls
         * @param options.task_id
         * @param options.base_url
         * @param options.success
         * @param options.error
         * @param options.complete
         */
        initAsyncView: function(options){
            var that = this;
            var poll_interval = options.poll_interval || [500, 2500, 10000];
            var task_id = options.task_id;
            if(task_id === undefined)throw new Error('task_id not defined');
            var base_url = options.base_url;
            if(base_url === null || base_url === undefined){
                base_url = window.location.pathname;
            }
            var max_polls = options.max_polls || that.max_polls;
            var poll_count = 0;
            function poll() {
                poll_count += 1;
                $.ajax({
                    url: that._createUrl(base_url, task_id),
                    type: "GET",
                    success: function(data) {
                        if (!data.ready){
                            if(poll_count >= max_polls){
                                // Poll limit reached
                                that._createAjaxErrorFunction(options)();
                            }else{
                                // NEXT POLL
                                that._setTimeout(
                                    function() {poll();},
                                    poll_interval, poll_count
                                );
                            }
                        } else {
                            that._createAjaxSuccessFunction(options)();
                            document.open();
                            document.write(data['html']);
                            document.close();
                            $(document).trigger('async-view-rewrite');
                        }
                    },
                    error: that._createAjaxErrorFunction(options),
                    dataType: 'json',
                    timeout: 2000
                });
            }
            // Start polling
            that._setTimeout(
                function() {poll();},
                poll_interval, poll_count
            );
        },

        // =============
        // AsyncDownload
        // =============

        async_download_button_class: 'async-download-button',

        /**
         * AsyncDownload starting point
         * # Phase 1.
         *
         * @param options
         * @param options.base_url
         * @param options.poll_interval
         *      in milliseconds
         *      integer
         *      or
         *      array of integers e.g. [500, 2500, 10000]
         *      The poll interval will be taken from the array in order
         *      last is used when none left
         * @param options.success: <function called when file download starts>
         *        even though success is called the download itself might still fail
         * @param options.error: <function called if ajax fails before download called>
         * @param options.complete <function called if error or success is called>
         *        even though complete is called the download itself might still fail
         */
        startFileCreation: function(options){
            var that = this;
            var base_url = options.base_url;
            if(base_url === undefined)throw new Error('base_url not defined');
            var poll_interval = options.poll_interval || [500, 2500, 10000];
            var max_polls = options.max_polls || that.max_polls;
            $.ajax({
                url: base_url,
                type: "GET",
                success: function(data) {
                    var task_id = data.task_id;
                    var ready = data.ready;
                    that._pollIfFileIsNotReady(
                        base_url, task_id, ready, poll_interval, max_polls,
                        0, options);
                },
                error: that._createAjaxErrorFunction(options),
                dataType: 'json',
                timeout: 2000
            });
        },

        /**Poll IF file is not ready
         * # Phase 2.A
         */
        _pollIfFileIsNotReady: function(
                base_url, task_id, ready, poll_interval, max_polls,
                poll_count, options){
            var that = this;
            if (!ready){
                // # Phase 2.B
                that._setTimeout(
                    function() {
                        that._pollIsFileReady(
                            base_url, task_id, ready, poll_interval, max_polls,
                            poll_count, options
                        );
                    },
                    poll_interval,
                    poll_count
                );
            } else {
                // # Phase 3.
                that._downloadFile(base_url, task_id, options);
            }
        },

        /** Poll is file ready.
         *  Phase 2.B
         * @param base_url
         * @param task_id
         * @param ready
         * @param poll_interval
         * @param max_polls
         * @param poll_count
         * @param options
         */
        _pollIsFileReady: function(base_url, task_id, ready, poll_interval, max_polls,
                                   poll_count, options){
            var that = this;
            poll_count += 1;
            $.ajax({
                url: that._createUrl(base_url, task_id),
                type: 'GET',
                success: function(data) {
                    ready = data.ready;
                    if(!ready && poll_count >= max_polls){
                        // Poll limit reached
                        that._createAjaxErrorFunction(options)();
                        return;
                    }
                    // # Phase 2.A
                    that._pollIfFileIsNotReady(
                        base_url, task_id, ready, poll_interval, max_polls,
                        poll_count, options);
                },
                error: that._createAjaxErrorFunction(options),
                dataType: 'json',
                timeout: 2000
            });
        },

        /** Download the file.
         * # Phase 3.
         */
        _downloadFile: function(base_url, task_id, options){
            var that = this;
            that._createAjaxSuccessFunction(options)();
            window.location.href = that._createUrl(base_url, task_id) + '&download=true';
        },

        // =======
        // Helpers
        // =======

        /**Adds task_id=<task_id> to the base_url
         * @param base_url
         * @param task_id
         * @returns {string}
         * @private
         */
        _createUrl: function(base_url, task_id){
            if(base_url.indexOf('?') < 0){
                base_url += '?';
            }
            if(base_url[-1] !== '?' && base_url[-1] !== '&'){
                base_url += '&';
            }
            return base_url + 'task_id=' + task_id;
        },

        /**Create callback that calls error and complete
         * if they exist.
         * @param options
         * @returns {Function}
         */
        _createAjaxErrorFunction: function(options){
            return function(){
                if(options && options.error){
                options.error();
                }
                if(options && options.complete){
                    options.complete();
                }
            };
        },

        /**Create callback that calls success and complete
         * if they exist.
         * @param options
         * @returns {Function}
         */
        _createAjaxSuccessFunction: function(options){
            return function(){
                if(options && options.success){
                options.success();
                }
                if(options && options.complete){
                    options.complete();
                }
            };
        },

        _setTimeout: function(callback, poll_interval, poll_count){
            if(typeof(poll_interval) === "object"){
                // poll_interval is array of poll_intervals
                if(poll_count >= poll_interval.length){
                    poll_interval = poll_interval[poll_interval.length -1];
                }else{
                    poll_interval = poll_interval[poll_count];
                }
            }
            setTimeout(callback, poll_interval);
        }

    };
})();

$(document).on('ready async-view-rewrite', function(){
    $('body').on('click', '.' + AsyncViews.async_download_button_class, function(){
        var $download_button = $(this);
       //$download_button.attr('disabled', 'disabled');
        var startFileCreationArguments = {}
        startFileCreationArguments.base_url = $download_button.attr('data-href');
        startFileCreationArguments.poll_interval = parseInt(
            $download_button.attr('data-poll-interval'));
        AsyncViews.startFileCreation(startFileCreationArguments);
    });

});


