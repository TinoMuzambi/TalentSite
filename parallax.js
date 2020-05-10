$(window).scroll(function(){
   var scrollVal = $(this).scrollTop();

   $(".intro-img-container").css("transform",'translate(0px,-' + scrollVal / 2 + '%)');
});