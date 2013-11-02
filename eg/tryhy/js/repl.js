$(document).ready(function(){
  var backlog = [];
  var console = $('#hy-console').console({
    promptLabel: '=> ',
    commandValidate:function(line){
      if (line == '') return false;
      else return true;
    },
    commandHandle:function(line, report){
      $('.jquery-console-cursor').addClass('running');
      $.ajax({
        type: 'POST',
        url: '/eval',
        data: JSON.stringify({code: line, env: backlog}),
        contentType: 'application/json',
        dataType: 'json',
        success: function(data) {
          $('.jquery-console-cursor').removeClass('running');
          report([{msg : data.stdout, className:'jquery-console-message-value'},
                  {msg : data.stderr, className:'jquery-console-message-error'}]);
        }
      });
      backlog.push(line);
    },
    animateScroll:true,
    promptHistory:true,
    autofocus:true,
    welcomeMessage: 'hy ({hy_version})'.supplant({hy_version: hy_version})
  });
  console.promptText('(+ 41 1)');
});


if (!String.prototype.supplant) {
    String.prototype.supplant = function (o) {
        return this.replace(
            /\{([^{}]*)\}/g,
            function (a, b) {
                var r = o[b];
                return typeof r === 'string' || typeof r === 'number' ? r : a;
            }
        );
    };
}
