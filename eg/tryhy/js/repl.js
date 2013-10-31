$(document).ready(function(){
  $('#hy-console').console({
    promptLabel: 'hy=> ',
    commandValidate:function(line){
      if (line == "") return false;
      else return true;
    },
    commandHandle:function(line, report){
      $.get("/eval", {code: line}, function(data) {
        report([{msg : data, className:"jquery-console-message-value"}]);
      });
    },
    animateScroll:true,
    promptHistory:true,
    autofocus:true,
  }).promptText('(+ 41 1)');
});
