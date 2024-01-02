// match-input.js

$(document).ready(function() {
    // Access the URL from the data attribute
    var processDataUrl = $('script[src*="match-input.js"]').attr('data-match-input-url');

    $('.match-event-button').on('click', function() {
        var event = $(this).data('event');
        var matchId = $(this).data('match');
        var playerregId = $(this).data('player');
        var teamregId = $(this).data('team');
        var eventtypeName = $(this).data('eventtype');
        var csrf_token = $(this).data('csrf_token')

        $.ajax({
            url: processDataUrl,
            type: 'POST',
            data: {
                'csrfmiddlewaretoken': csrf_token,
                'event': event,
                'match': matchId,
                'player': playerregId,
                'team': teamregId,
                'eventtype': eventtypeName
            },
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    console.log('Match input data processed successfully');
                    location.reload();
                } else {
                    console.error('Error processing match input data:', response.error);
                    location.reload();
                }
            },
            error: function(xhr, status, error) {
                console.error('AJAX error:', error);
                location.reload();
            }
        });
    });
});
