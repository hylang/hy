" Vim syntax file
" Language:     hy
" Authors:      Morten Linderud <mcfoxax@gmail.com>
" URL:          http://github.com/Foxboron
"
" Modified version of the clojure syntax file: https://github.com/guns/vim-clojure-static/blob/master/syntax/clojure.vim
if exists("b:current_syntax")
    finish
endif

" hy version 0.9.8
syntax keyword hyConstant null
syntax keyword hyBoolean false true
syntax keyword hySpecial . except def do finally fn if let quote try
syntax keyword hyException except finally throw try
syntax keyword hyCond cond when
syntax keyword hyRepeat while
syntax keyword hyDefine defmacro defclass defn
syntax keyword hyMacro -> ->> .. and assert for import or
syntax keyword hyFunc * + - / < <= = == > >= assoc atom bool bytes char char? class class? eval even? false? first flatten float format int iterate list macroexpand map max methods mod name namespace next not != nth partial pop print range read reduce remove replace secondsorted split str type zip
syntax keyword hyVariable string

" Keywords are symbols:
"   static Pattern symbolPat = Pattern.compile("[:]?([\\D&&[^/]].*/)?([\\D&&[^/]][^/]*)");
" But they:
"   * Must not end in a : or /
"   * Must not have two adjacent colons except at the beginning
"   * Must not contain any reader metacharacters except for ' and #
syntax match hyKeyword "\v<:{1,2}%([^ \n\r\t()\[\]{}";@^`~\\%/]+/)*[^ \n\r\t()\[\]{}";@^`~\\%/]+:@<!>"

syntax match hyStringEscape "\v\\%([\\btnfr"]|u\x{4}|[0-3]\o{2}|\o{1,2})" contained

syntax region hyString start=/"/ skip=/\\\\\|\\"/ end=/"/ contains=hyStringEscape

syntax match hyCharacter "\\."
syntax match hyCharacter "\\o\%([0-3]\o\{2\}\|\o\{1,2\}\)"
syntax match hyCharacter "\\u\x\{4\}"
syntax match hyCharacter "\\space"
syntax match hyCharacter "\\tab"
syntax match hyCharacter "\\newline"
syntax match hyCharacter "\\return"
syntax match hyCharacter "\\backspace"
syntax match hyCharacter "\\formfeed"

syntax match hySymbol "\v%([a-zA-Z!$&*_+=|<.>?-]|[^\x00-\x7F])+%(:?%([a-zA-Z0-9!#$%&*_+=|'<.>/?-]|[^\x00-\x7F]))*[#:]@<!"

let s:radix_chars = "0123456789abcdefghijklmnopqrstuvwxyz"
for s:radix in range(2, 36)
    execute 'syntax match hyNumber "\v\c<[-+]?' . s:radix . 'r[' . strpart(s:radix_chars, 0, s:radix) . ']+>"'
endfor
unlet! s:radix_chars s:radix

syntax match hyNumber "\v<[-+]?%(0\o*|0x\x+|[1-9]\d*)N?>"
syntax match hyNumber "\v<[-+]?%(0|[1-9]\d*|%(0|[1-9]\d*)\.\d*)%(M|[eE][-+]?\d+)?>"
syntax match hyNumber "\v<[-+]?%(0|[1-9]\d*)/%(0|[1-9]\d*)>"

syntax match hyVarArg "&"

syntax match hyQuote "'"
syntax match hyQuote "`"
syntax match hyUnquote "\~"
syntax match hyUnquote "\~@"
syntax match hyMeta "\^"
syntax match hyDeref "@"
syntax match hyDispatch "\v#[\^'=<_]?"

" hy permits no more than 20 params.
syntax match hyAnonArg "%\(20\|1\d\|[1-9]\|&\)\?"

syntax match   hyRegexpEscape  "\v\\%(\\|[tnrfae]|c\u|0[0-3]?\o{1,2}|x%(\x{2}|\{\x{1,6}\})|u\x{4})" contained display
syntax region  hyRegexpQuoted  start=/\v\<@!\\Q/ms=e+1 skip=/\v\\\\|\\"/ end=/\\E/me=s-1 end=/"/me=s-1 contained
syntax region  hyRegexpQuote   start=/\v\<@!\\Q/       skip=/\v\\\\|\\"/ end=/\\E/       end=/"/me=s-1 contains=hyRegexpQuoted keepend contained
syntax cluster hyRegexpEscapes contains=hyRegexpEscape,hyRegexpQuote

" Character property classes
" Generated from https://github.com/guns/vim-hy-static/blob/vim-release-004/clj/src/vim_hy_static/generate.clj
" Java version 1.7.0_17
syntax match hyRegexpPosixCharClass "\v\\[pP]\{%(ASCII|Alnum|Alpha|Blank|Cntrl|Digit|Graph|Lower|Print|Punct|Space|Upper|XDigit)\}" contained display
syntax match hyRegexpJavaCharClass "\v\\[pP]\{java%(Alphabetic|Defined|Digit|ISOControl|IdentifierIgnorable|Ideographic|JavaIdentifierPart|JavaIdentifierStart|Letter|LetterOrDigit|LowerCase|Mirrored|SpaceChar|TitleCase|UnicodeIdentifierPart|UnicodeIdentifierStart|UpperCase|Whitespace)\}" contained display
syntax match hyRegexpUnicodeCharClass "\v\\[pP]\{\cIs%(alnum|alphabetic|assigned|blank|control|digit|graph|hex_digit|hexdigit|ideographic|letter|lowercase|noncharacter_code_point|noncharactercodepoint|print|punctuation|titlecase|uppercase|white_space|whitespace|word)\}" contained display
syntax match hyRegexpUnicodeCharClass "\v\\[pP]%(C|L|M|N|P|S|Z)" contained display
syntax match hyRegexpUnicodeCharClass "\v\\[pP]\{%(Is|gc\=|general_category\=)?%(C[cfnos]|L[CDlmotu]|M[cen]|N[dlo]|P[cdefios]|S[ckmo]|Z[lps])\}" contained display
syntax match hyRegexpUnicodeCharClass "\v\\[pP]\{\c%(Is|sc\=|script\=)%(arab|arabic|armenian|armi|armn|avestan|avst|bali|balinese|bamu|bamum|batak|batk|beng|bengali|bopo|bopomofo|brah|brahmi|brai|braille|bugi|buginese|buhd|buhid|canadian_aboriginal|cans|cari|carian|cham|cher|cherokee|common|copt|coptic|cprt|cuneiform|cypriot|cyrillic|cyrl|deseret|deva|devanagari|dsrt|egyp|egyptian_hieroglyphs|ethi|ethiopic|geor|georgian|glag|glagolitic|goth|gothic|greek|grek|gujarati|gujr|gurmukhi|guru|han|hang|hangul|hani|hano|hanunoo|hebr|hebrew|hira|hiragana|imperial_aramaic|inherited|inscriptional_pahlavi|inscriptional_parthian|ital|java|javanese|kaithi|kali|kana|kannada|katakana|kayah_li|khar|kharoshthi|khmer|khmr|knda|kthi|lana|lao|laoo|latin|latn|lepc|lepcha|limb|limbu|linb|linear_b|lisu|lyci|lycian|lydi|lydian|malayalam|mand|mandaic|meetei_mayek|mlym|mong|mongolian|mtei|myanmar|mymr|new_tai_lue|nko|nkoo|ogam|ogham|ol_chiki|olck|old_italic|old_persian|old_south_arabian|old_turkic|oriya|orkh|orya|osma|osmanya|phag|phags_pa|phli|phnx|phoenician|prti|rejang|rjng|runic|runr|samaritan|samr|sarb|saur|saurashtra|shavian|shaw|sinh|sinhala|sund|sundanese|sylo|syloti_nagri|syrc|syriac|tagalog|tagb|tagbanwa|tai_le|tai_tham|tai_viet|tale|talu|tamil|taml|tavt|telu|telugu|tfng|tglg|thaa|thaana|thai|tibetan|tibt|tifinagh|ugar|ugaritic|unknown|vai|vaii|xpeo|xsux|yi|yiii|zinh|zyyy|zzzz)\}" contained display
syntax match hyRegexpUnicodeCharClass "\v\\[pP]\{\c%(In|blk\=|block\=)%(aegean numbers|aegean_numbers|aegeannumbers|alchemical symbols|alchemical_symbols|alchemicalsymbols|alphabetic presentation forms|alphabetic_presentation_forms|alphabeticpresentationforms|ancient greek musical notation|ancient greek numbers|ancient symbols|ancient_greek_musical_notation|ancient_greek_numbers|ancient_symbols|ancientgreekmusicalnotation|ancientgreeknumbers|ancientsymbols|arabic|arabic presentation forms-a|arabic presentation forms-b|arabic supplement|arabic_presentation_forms_a|arabic_presentation_forms_b|arabic_supplement|arabicpresentationforms-a|arabicpresentationforms-b|arabicsupplement|armenian|arrows|avestan|balinese|bamum|bamum supplement|bamum_supplement|bamumsupplement|basic latin|basic_latin|basiclatin|batak|bengali|block elements|block_elements|blockelements|bopomofo|bopomofo extended|bopomofo_extended|bopomofoextended|box drawing|box_drawing|boxdrawing|brahmi|braille patterns|braille_patterns|braillepatterns|buginese|buhid|byzantine musical symbols|byzantine_musical_symbols|byzantinemusicalsymbols|carian|cham|cherokee|cjk compatibility|cjk compatibility forms|cjk compatibility ideographs|cjk compatibility ideographs supplement|cjk radicals supplement|cjk strokes|cjk symbols and punctuation|cjk unified ideographs|cjk unified ideographs extension a|cjk unified ideographs extension b|cjk unified ideographs extension c|cjk unified ideographs extension d|cjk_compatibility|cjk_compatibility_forms|cjk_compatibility_ideographs|cjk_compatibility_ideographs_supplement|cjk_radicals_supplement|cjk_strokes|cjk_symbols_and_punctuation|cjk_unified_ideographs|cjk_unified_ideographs_extension_a|cjk_unified_ideographs_extension_b|cjk_unified_ideographs_extension_c|cjk_unified_ideographs_extension_d|cjkcompatibility|cjkcompatibilityforms|cjkcompatibilityideographs|cjkcompatibilityideographssupplement|cjkradicalssupplement|cjkstrokes|cjksymbolsandpunctuation|cjkunifiedideographs|cjkunifiedideographsextensiona|cjkunifiedideographsextensionb|cjkunifiedideographsextensionc|cjkunifiedideographsextensiond|combining diacritical marks|combining diacritical marks for symbols|combining diacritical marks supplement|combining half marks|combining marks for symbols|combining_diacritical_marks|combining_diacritical_marks_supplement|combining_half_marks|combining_marks_for_symbols|combiningdiacriticalmarks|combiningdiacriticalmarksforsymbols|combiningdiacriticalmarkssupplement|combininghalfmarks|combiningmarksforsymbols|common indic number forms|common_indic_number_forms|commonindicnumberforms|control pictures|control_pictures|controlpictures|coptic|counting rod numerals|counting_rod_numerals|countingrodnumerals|cuneiform|cuneiform numbers and punctuation|cuneiform_numbers_and_punctuation|cuneiformnumbersandpunctuation|currency symbols|currency_symbols|currencysymbols|cypriot syllabary|cypriot_syllabary|cypriotsyllabary|cyrillic|cyrillic extended-a|cyrillic extended-b|cyrillic supplement|cyrillic supplementary|cyrillic_extended_a|cyrillic_extended_b|cyrillic_supplementary|cyrillicextended-a|cyrillicextended-b|cyrillicsupplement|cyrillicsupplementary|deseret|devanagari|devanagari extended|devanagari_extended|devanagariextended|dingbats|domino tiles|domino_tiles|dominotiles|egyptian hieroglyphs|egyptian_hieroglyphs|egyptianhieroglyphs|emoticons|enclosed alphanumeric supplement|enclosed alphanumerics|enclosed cjk letters and months|enclosed ideographic supplement|enclosed_alphanumeric_supplement|enclosed_alphanumerics|enclosed_cjk_letters_and_months|enclosed_ideographic_supplement|enclosedalphanumerics|enclosedalphanumericsupplement|enclosedcjklettersandmonths|enclosedideographicsupplement|ethiopic|ethiopic extended|ethiopic extended-a|ethiopic supplement|ethiopic_extended|ethiopic_extended_a|ethiopic_supplement|ethiopicextended|ethiopicextended-a|ethiopicsupplement|general punctuation|general_punctuation|generalpunctuation|geometric shapes|geometric_shapes|geometricshapes|georgian|georgian supplement|georgian_supplement|georgiansupplement|glagolitic|gothic|greek|greek and coptic|greek extended|greek_extended|greekandcoptic|greekextended|gujarati|gurmukhi|halfwidth and fullwidth forms|halfwidth_and_fullwidth_forms|halfwidthandfullwidthforms|hangul compatibility jamo|hangul jamo|hangul jamo extended-a|hangul jamo extended-b|hangul syllables|hangul_compatibility_jamo|hangul_jamo|hangul_jamo_extended_a|hangul_jamo_extended_b|hangul_syllables|hangulcompatibilityjamo|hanguljamo|hanguljamoextended-a|hanguljamoextended-b|hangulsyllables|hanunoo|hebrew|high private use surrogates|high surrogates|high_private_use_surrogates|high_surrogates|highprivateusesurrogates|highsurrogates|hiragana|ideographic description characters|ideographic_description_characters|ideographicdescriptioncharacters|imperial aramaic|imperial_aramaic|imperialaramaic|inscriptional pahlavi|inscriptional parthian|inscriptional_pahlavi|inscriptional_parthian|inscriptionalpahlavi|inscriptionalparthian|ipa extensions|ipa_extensions|ipaextensions|javanese|kaithi|kana supplement|kana_supplement|kanasupplement|kanbun|kangxi radicals|kangxi_radicals|kangxiradicals|kannada|katakana|katakana phonetic extensions|katakana_phonetic_extensions|katakanaphoneticextensions|kayah li|kayah_li|kayahli|kharoshthi|khmer|khmer symbols|khmer_symbols|khmersymbols|lao|latin extended additional|latin extended-a|latin extended-b|latin extended-c|latin extended-d|latin-1 supplement|latin-1supplement|latin_1_supplement|latin_extended_a|latin_extended_additional|latin_extended_b|latin_extended_c|latin_extended_d|latinextended-a|latinextended-b|latinextended-c|latinextended-d|latinextendedadditional|lepcha|letterlike symbols|letterlike_symbols|letterlikesymbols|limbu|linear b ideograms|linear b syllabary|linear_b_ideograms|linear_b_syllabary|linearbideograms|linearbsyllabary|lisu|low surrogates|low_surrogates|lowsurrogates|lycian|lydian|mahjong tiles|mahjong_tiles|mahjongtiles|malayalam|mandaic|mathematical alphanumeric symbols|mathematical operators|mathematical_alphanumeric_symbols|mathematical_operators|mathematicalalphanumericsymbols|mathematicaloperators|meetei mayek|meetei_mayek|meeteimayek|miscellaneous mathematical symbols-a|miscellaneous mathematical symbols-b|miscellaneous symbols|miscellaneous symbols and arrows|miscellaneous symbols and pictographs|miscellaneous technical|miscellaneous_mathematical_symbols_a|miscellaneous_mathematical_symbols_b|miscellaneous_symbols|miscellaneous_symbols_and_arrows|miscellaneous_symbols_and_pictographs|miscellaneous_technical|miscellaneousmathematicalsymbols-a|miscellaneousmathematicalsymbols-b|miscellaneoussymbols|miscellaneoussymbolsandarrows|miscellaneoussymbolsandpictographs|miscellaneoustechnical|modifier tone letters|modifier_tone_letters|modifiertoneletters|mongolian|musical symbols|musical_symbols|musicalsymbols|myanmar|myanmar extended-a|myanmar_extended_a|myanmarextended-a|new tai lue|new_tai_lue|newtailue|nko|number forms|number_forms|numberforms|ogham|ol chiki|ol_chiki|olchiki|old italic|old persian|old south arabian|old turkic|old_italic|old_persian|old_south_arabian|old_turkic|olditalic|oldpersian|oldsoutharabian|oldturkic|optical character recognition|optical_character_recognition|opticalcharacterrecognition|oriya|osmanya|phags-pa|phags_pa|phaistos disc|phaistos_disc|phaistosdisc|phoenician|phonetic extensions|phonetic extensions supplement|phonetic_extensions|phonetic_extensions_supplement|phoneticextensions|phoneticextensionssupplement|playing cards|playing_cards|playingcards|private use area|private_use_area|privateusearea|rejang|rumi numeral symbols|rumi_numeral_symbols|ruminumeralsymbols|runic|samaritan|saurashtra|shavian|sinhala|small form variants|small_form_variants|smallformvariants|spacing modifier letters|spacing_modifier_letters|spacingmodifierletters|specials|sundanese|superscripts and subscripts|superscripts_and_subscripts|superscriptsandsubscripts|supplemental arrows-a|supplemental arrows-b|supplemental mathematical operators|supplemental punctuation|supplemental_arrows_a|supplemental_arrows_b|supplemental_mathematical_operators|supplemental_punctuation|supplementalarrows-a|supplementalarrows-b|supplementalmathematicaloperators|supplementalpunctuation|supplementary private use area-a|supplementary private use area-b|supplementary_private_use_area_a|supplementary_private_use_area_b|supplementaryprivateusearea-a|supplementaryprivateusearea-b|surrogates_area|syloti nagri|syloti_nagri|sylotinagri|syriac|tagalog|tagbanwa|tags|tai le|tai tham|tai viet|tai xuan jing symbols|tai_le|tai_tham|tai_viet|tai_xuan_jing_symbols|taile|taitham|taiviet|taixuanjingsymbols|tamil|telugu|thaana|thai|tibetan|tifinagh|transport and map symbols|transport_and_map_symbols|transportandmapsymbols|ugaritic|unified canadian aboriginal syllabics|unified canadian aboriginal syllabics extended|unified_canadian_aboriginal_syllabics|unified_canadian_aboriginal_syllabics_extended|unifiedcanadianaboriginalsyllabics|unifiedcanadianaboriginalsyllabicsextended|vai|variation selectors|variation selectors supplement|variation_selectors|variation_selectors_supplement|variationselectors|variationselectorssupplement|vedic extensions|vedic_extensions|vedicextensions|vertical forms|vertical_forms|verticalforms|yi radicals|yi syllables|yi_radicals|yi_syllables|yijing hexagram symbols|yijing_hexagram_symbols|yijinghexagramsymbols|yiradicals|yisyllables)\}" contained display

syntax match   hyRegexpPredefinedCharClass "\v%(\\[dDsSwW]|\.)" contained display
syntax cluster hyRegexpCharPropertyClasses contains=hyRegexpPosixCharClass,hyRegexpJavaCharClass,hyRegexpUnicodeCharClass
syntax cluster hyRegexpCharClasses         contains=hyRegexpPredefinedCharClass,hyRegexpCharClass,@hyRegexpCharPropertyClasses
syntax region  hyRegexpCharClass           start="\\\@<!\[" end="\\\@<!\]" contained contains=hyRegexpPredefinedCharClass,@hyRegexpCharPropertyClasses
syntax match   hyRegexpBoundary            "\\[bBAGZz]"   contained display
syntax match   hyRegexpBoundary            "[$^]"         contained display
syntax match   hyRegexpQuantifier          "[?*+][?+]\="  contained display
syntax match   hyRegexpQuantifier          "\v\{\d+%(,|,\d+)?}\??" contained display
syntax match   hyRegexpOr                  "|" contained display
syntax match   hyRegexpBackRef             "\v\\%([1-9]\d*|k\<[a-zA-z]+\>)" contained display

" Mode modifiers, mode-modified spans, lookaround, regular and atomic
" grouping, and named-capturing.
syntax match hyRegexpMod "\v\(@<=\?:"                        contained display
syntax match hyRegexpMod "\v\(@<=\?[xdsmiuU]*-?[xdsmiuU]+:?" contained display
syntax match hyRegexpMod "\v\(@<=\?%(\<?[=!]|\>)"            contained display
syntax match hyRegexpMod "\v\(@<=\?\<[a-zA-Z]+\>"            contained display

syntax region hyRegexpGroup start="\\\@<!(" matchgroup=hyRegexpGroup end="\\\@<!)" contained contains=hyRegexpMod,hyRegexpQuantifier,hyRegexpBoundary,hyRegexpEscape,@hyRegexpCharClasses
syntax region hyRegexp start=/\#"/ skip=/\\\\\|\\"/ end=/"/ contains=@hyRegexpCharClasses,hyRegexpEscape,hyRegexpQuote,hyRegexpBoundary,hyRegexpQuantifier,hyRegexpOr,hyRegexpBackRef,hyRegexpGroup keepend

syntax keyword hyCommentTodo contained FIXME XXX TODO FIXME: XXX: TODO:

syntax match hyComment ";.*$" contains=hyCommentTodo,@Spell
syntax match hyComment "#!.*$"

syntax region hySexp   matchgroup=hyParen start="("  matchgroup=hyParen end=")"  contains=TOP,@Spell
syntax region hyVector matchgroup=hyParen start="\[" matchgroup=hyParen end="\]" contains=TOP,@Spell
syntax region hyMap    matchgroup=hyParen start="{"  matchgroup=hyParen end="}"  contains=TOP,@Spell

" Highlight superfluous closing parens, brackets and braces.
syntax match hyError "]\|}\|)"

syntax sync fromstart

highlight default link hyConstant     Constant
highlight default link hyBoolean      Boolean
highlight default link hyCharacter    Character
highlight default link hyKeyword      Keyword
highlight default link hyNumber       Number
highlight default link hyString       String
highlight default link hyStringEscape Character

highlight default link hyRegexp                    Constant
highlight default link hyRegexpEscape              Character
highlight default link hyRegexpCharClass           SpecialChar
highlight default link hyRegexpPosixCharClass      hyRegexpCharClass
highlight default link hyRegexpJavaCharClass       hyRegexpCharClass
highlight default link hyRegexpUnicodeCharClass    hyRegexpCharClass
highlight default link hyRegexpPredefinedCharClass hyRegexpCharClass
highlight default link hyRegexpBoundary            SpecialChar
highlight default link hyRegexpQuantifier          SpecialChar
highlight default link hyRegexpMod                 SpecialChar
highlight default link hyRegexpOr                  SpecialChar
highlight default link hyRegexpBackRef             SpecialChar
highlight default link hyRegexpGroup               hyRegexp
highlight default link hyRegexpQuoted              hyString
highlight default link hyRegexpQuote               hyRegexpBoundary

highlight default link hyVariable  Identifier
highlight default link hyCond      Conditional
highlight default link hyDefine    Define
highlight default link hyException Exception
highlight default link hyFunc      Function
highlight default link hyMacro     Macro
highlight default link hyRepeat    Repeat

highlight default link hySpecial   Special
highlight default link hyVarArg    Special
highlight default link hyQuote     SpecialChar
highlight default link hyUnquote   SpecialChar
highlight default link hyMeta      SpecialChar
highlight default link hyDeref     SpecialChar
highlight default link hyAnonArg   SpecialChar
highlight default link hyDispatch  SpecialChar

highlight default link hyComment     Comment
highlight default link hyCommentTodo Todo

highlight default link hyError     Error

highlight default link hyParen     Delimiter

let b:current_syntax = "hy"

" vim:sts=4:sw=4:ts=4:et:smc=20000