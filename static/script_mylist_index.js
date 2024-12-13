console.log("Homepage js file loaded ver")

$(document).ready(function() {
    $.ajax({
        url: $SCRIPT_ROOT + '/active_list_data',
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



function change_quantity(id) {
    value = $('#' + id).val()
    if (value === '') {
        console.log('empty textbox')
        return;
    }
    $.ajax({
        url: $SCRIPT_ROOT + '/active_list_quantity',
        dataType: 'json',
        type: 'POST',
        data: {
            id: id,
            value: value
        },
        success: function (response) {
            $('#primary_data').replaceWith(response)
        },
        error: function () {
            console.log('error')
        }
    })
}



$(document).on("submit", "form", function(e) {
    var form = $(this);
    var formId = form.attr("id");
    e.preventDefault();
    // alert("js file")

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



function submit_ios_fix(e) {
    // Patch work for datalist submission issue on iphone. Issue occurs
    // when trying to type in an item that already exists.
                
    if (e.code === "Enter" || e.code === "NumpadEnter") {
        e.preventDefault();
        document.getElementById("item_submit_button").click();
    }
}