console.log("My items ajax")


$(document).ready(function() {
    $.ajax({
        url: $SCRIPT_ROOT + '/my_items_data',
        dataType: 'json',
        type: 'GET',
        success: function (response) {
            $('#primary_data').replaceWith(response);

        },
        error: function (response) {
            alert('Server side error with input');
            location.reload();
        }
    })
})

$(document).on("submit", "form", function(e) {
    
    var form = $(this);
    var formId = form.attr("id");
    e.preventDefault();

    $.ajax({
        url: $SCRIPT_ROOT + '/' + formId,
        dataType: 'json',
        type: 'POST',
        data: form.serialize(),
        success: function(response) {
            $('#primary_data').replaceWith(response);
        },
        error: function(response) {
            location.reload();
        }
    })
})
