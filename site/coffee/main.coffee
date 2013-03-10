reload = ->
  input = $("#repl-input").val()
  $('#repl-output').load('/hy2pycol', {'code': input})

$(document).ready(->
  count = 0
  $("#repl-input").keyup((e) ->
    curcount = 0
    count += 1
    curcount = count
    window.setTimeout(->
      if curcount == count
        console.log("trigger")
        reload()
    , 500)
  )
  reload()
);
