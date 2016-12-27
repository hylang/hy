/*
Language: Hy
Description: Hy syntax (based on clojure.js)
Author: Sergey Sobko <s.sobko@profitware.ru>
Category: lisp
*/

function(hljs) {
  var keywords = {
    'builtin-name':
      // keywords

   };

  var SYMBOLSTART = 'a-zA-Z_\\-!.?+*=<>&#\'';
  var SYMBOL_RE = '[' + SYMBOLSTART + '][' + SYMBOLSTART + '0-9/;:]*';
  var SIMPLE_NUMBER_RE = '[-+]?\\d+(\\.\\d+)?';

  var SHEBANG = {
    className: 'meta',
    begin: '^#!', end: '$'
  };

  var SYMBOL = {
    begin: SYMBOL_RE,
    relevance: 0
  };
  var NUMBER = {
    className: 'number', begin: SIMPLE_NUMBER_RE,
    relevance: 0
  };
  var STRING = hljs.inherit(hljs.QUOTE_STRING_MODE, {illegal: null});
  var COMMENT = hljs.COMMENT(
    ';',
    '$',
    {
      relevance: 0
    }
  );
  var LITERAL = {
    className: 'literal',
    begin: /\b([Tt]rue|[Ff]alse|nil|None)\b/
  };
  var COLLECTION = {
    begin: '[\\[\\{]', end: '[\\]\\}]'
  };
  var HINT = {
    className: 'comment',
    begin: '\\^' + SYMBOL_RE
  };
  var HINT_COL = hljs.COMMENT('\\^\\{', '\\}');
  var KEY = {
    className: 'symbol',
    begin: '[:]{1,2}' + SYMBOL_RE
  };
  var LIST = {
    begin: '\\(', end: '\\)'
  };
  var BODY = {
    endsWithParent: true,
    relevance: 0
  };
  var NAME = {
    keywords: keywords,
    lexemes: SYMBOL_RE,
    className: 'name', begin: SYMBOL_RE,
    starts: BODY
  };
  var DEFAULT_CONTAINS = [LIST, STRING, HINT, HINT_COL, COMMENT, KEY, COLLECTION, NUMBER, LITERAL, SYMBOL];

  LIST.contains = [hljs.COMMENT('comment', ''), NAME, BODY];
  BODY.contains = DEFAULT_CONTAINS;
  COLLECTION.contains = DEFAULT_CONTAINS;

  return {
    aliases: ['hylang'],
    illegal: /\S/,
    contains: [SHEBANG, LIST, STRING, HINT, HINT_COL, COMMENT, KEY, COLLECTION, NUMBER, LITERAL]
  }
}
