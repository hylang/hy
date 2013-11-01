$(document).ready(function(){
  $('#hy-console').console({
    promptLabel: 'hy=> ',
    commandValidate:function(line){
      if (line == "") return false;
      else return true;
    },
    commandHandle:function(line, report){
      $.getJSON("/eval", {code: line}, function(data) {
        report([{msg : data.stdout, className:"jquery-console-message-value"},
                {msg : data.stderr, className:"jquery-console-message-error"}]);
      });
    },
    animateScroll:true,
    promptHistory:true,
    autofocus:true,
  }).promptText('(+ 41 1)');
});
