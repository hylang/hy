$(document).ready(function(){
  var backlog = [];
  $('#hy-console').console({
    promptLabel: 'hy=> ',
    commandValidate:function(line){
      if (line == '') return false;
      else return true;
    },
    commandHandle:function(line, report){
      $.ajax({
        type: 'POST',
        url: '/eval',
        data: JSON.stringify({code: line, env: backlog}),
        contentType: 'application/json',
        dataType: 'json',
        success: function(data) {
          report([{msg : data.stdout, className:'jquery-console-message-value'},
                  {msg : data.stderr, className:'jquery-console-message-error'}]);
        }
      });
      backlog.push(line);
    },
    animateScroll:true,
    promptHistory:true,
    autofocus:true,
  }).promptText('(+ 41 1)');
});
