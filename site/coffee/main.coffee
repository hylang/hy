# Copyright (c) 2012 Paul Tagliamonte <paultag@debian.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

theme = "elegant"

HyCodeMirror = CodeMirror.fromTextArea($('#hython-target')[0], {
    mode:  "clojure",
    theme: theme,
    autofocus: true,
})

PyCodeMirror = CodeMirror($('#python-repl')[0], {
    mode:  "python",
    theme: theme,
    readOnly: true,
})

PyCodeMirror.setSize("100%", "100%")
HyCodeMirror.setSize("100%", "100%")

reload = ->
  input = HyCodeMirror.getValue()
  $.ajax({
      url: "/hy2py",
      type: "POST",
      data: {'code': input},
      success: (result) ->
        PyCodeMirror.setValue(result)
        now = new Date().getTime();
        $("#build-msgs").text(now + " Updated.")
      statusCode: {
        500: (response) ->
          now = new Date().getTime();
          $("#build-msgs").text(now + " " + response.responseText)
      }
  });


$(document).ready(->
  count = 0

  HyCodeMirror.on("change", (instance, cob) ->
    count += 1
    curcount = count
    window.setTimeout(->
      if curcount == count
        reload()
    , 500)
  )
  reload()
)
