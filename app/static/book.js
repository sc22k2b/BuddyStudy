$(document).ready(function(){

    // Set the token so that we are not rejected by server
	var csrf_token = $('meta[name=csrf-token]').attr('content');
    // Configure ajaxSetup so that the CSRF token is added to the header of every request
   $.ajaxSetup({
       beforeSend: function(xhr, settings) {
           if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
               xhr.setRequestHeader("X-CSRFToken", csrf_token);
           }
       }
   });

   $("a.book").on("click", function() {

        var clicked_obj = $(this)

        var ids = $(this).attr('id')

        $.ajax({

            url: '/book',
            type: 'POST',
            data: JSON.stringify({ ids : ids}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(response){

                console.log(response);

                if(response.full == false){
                    if(clicked_obj.children()[0].innerHTML == "Booked"){
                        clicked_obj.children()[0].innerHTML = "Book";
                    }
                    else{
                        clicked_obj.children()[0].innerHTML = "Booked";
                    }
                }
                else{
                    clicked_obj.children()[0].innerHTML = "Book";
                    alert("Session is already full")
                }

                clicked_obj.children()[1].innerHTML = " " + response.attendance;
            },
            error: function(error){
                console.log(error);

            }
        });
   
   });
});
