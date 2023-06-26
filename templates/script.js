$(document).ready(function() {
    $('#uploadButton').click(function() {
        var file = $('#csvFile')[0].files[0];
        if(file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                var contents = e.target.result;
                $.ajax({
                    url: "/upload",
                    type: "POST",
                    data: {data: contents},
                    success: function(response) {
                        // Handle the response from the server
                        $("#output").html(response);
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        console.log(textStatus, errorThrown);
                    }
                });
            };
            reader.readAsText(file);
        } else {
            alert("Lütfen bir CSV dosyası seçin.");
        }
    });
});
