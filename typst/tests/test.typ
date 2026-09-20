#import "../cbcp.typ": *

#let _padded = " \t\n\r\u{0B}\u{0C}EN_CH\u{0C}\u{0B}\r\n\t "

// normalize-locale-id
#assert.eq(normalize-locale-id(" DE_Ch "), "de-ch")
#assert.eq(normalize-locale-id("EN-CH"), "en-ch")
#assert.eq(normalize-locale-id("zh_Hant_TW"), "zh-hant-tw")
#assert.eq(normalize-locale-id(" XX_YY "), "xx-yy")
#assert.eq(normalize-locale-id("EN"), "en")
#assert.eq(normalize-locale-id(" \t\n"), "")
#assert.eq(normalize-locale-id("en__US"), "en--us")
#assert.eq(normalize-locale-id(_padded), "en-ch")

// display
#assert.eq(to-bcp47("de-ch"), "de-CH")
#assert.eq(to-bcp47("EN_CH"), "en-CH")
#assert.eq(to-bcp47("zh-hant-tw"), "zh-Hant-TW")
#assert.eq(to-bcp47("es-419"), "es-419")
#assert.eq(to-bcp47("de-CH"), "de-CH")
#assert.eq(base-language("DE-CH"), "de")
#assert.eq(base-language("en"), "en")

// well-formed + equality
#assert(is-well-formed("de-ch"))
#assert(is-well-formed("en"))
#assert(not is-well-formed(""))
#assert(not is-well-formed("en--us"))
#assert(locale-eq("DE_CH", "de-ch"))
#assert(not locale-eq("de-ch", "de-de"))

// vendor
#assert.eq(deepl-source("de-CH"), "DE")
#assert.eq(deepl-source("en"), "EN")
#assert.eq(deepl-target("en"), "EN-GB")
#assert.eq(deepl-target("en-US"), "EN-US")
#assert.eq(deepl-target("en-gb"), "EN-GB")
#assert.eq(deepl-target("pt"), "PT-PT")
#assert.eq(deepl-target("pt-BR"), "PT-BR")
#assert.eq(deepl-target("zh"), "ZH-HANS")
#assert.eq(deepl-target("fr-CH"), "FR")
#assert.eq(deepl-target("de-ch"), "DE")
#assert.eq(google-language("de-CH"), "de")
#assert.eq(google-language("EN"), "en")
