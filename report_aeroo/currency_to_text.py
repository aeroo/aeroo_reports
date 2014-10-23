#!/usr/bin/python
# -*- coding: utf8 -*-

###########################################################
# Developed by Kaspars Vilkens - Alistek Ltd (c) 2011
#     pep-8, unicode and doctests by Paul Stevens, paul@nfg.nl, 2010
#
# Supported currencies: LVL, EUR, USD, UAH
# Supported sum: 0 ... 999999999999.99
# Supported languages: lv_LV, en_US, ru_RU, uk_UA
###########################################################
import string

supported_currency = ['LVL','EUR','USD', 'UAH']
supported_language = ['lv_LV','en_US','ru_RU', 'uk_UA']

def currency_to_text(sum, currency, language):
    """
    
    first some simple tests

    >>> currency_to_text(123, 'EUR', 'en_US')
    'one hundred twenty three euros zero cents'

    >>> currency_to_text(1.11, 'EUR', 'en_US')
    'one euro eleven cents'

    >>> currency_to_text(1.10, 'USD', 'en_US')
    'one US dollar ten cents'

    >>> currency_to_text(1.01, 'USD', 'en_US')
    'one US dollar one cent'

    >>> currency_to_text(1.01, 'LVL', 'lv_LV') == 'viens lats viens santīms'
    True

    >>> currency_to_text(123.12, 'LVL', 'ru_RU') == 'стo двaдцать три лата двенадцать сантимов'
    True

    >>> currency_to_text(123.12, 'USD', 'ru_RU') == 'стo двaдцать три доллара США двенадцать центов'
    True


    """
    if sum < 0 or sum > 999999999999.99 : 
        raise Exception('Sum out of bounds: must be from 0 to 999999999999.99')
    if currency not in supported_currency: 
        raise Exception("""Unsupported or no currency: must be one of (%s)""" % \
            string.join(supported_currency,','))
    if language not in supported_language: 
        raise Exception("""Unsupported or no language: must be one of (%s)""" % \
            string.join(supported_language,','))
#--------------for currencies with 100 fractions
    sum = float(sum)
    sum = round(sum, 2)
    # find out digits before floating point - currency
    sum_cur = int(sum)
    # find out digits after floating point - fractions
    sum_frc = int(round((sum - sum_cur) * 100,0))
    cur_in_words = dtowords(sum_cur, language)
    frc_in_words = dtowords(sum_frc, language)
    #------------------------------------
    if language == 'lv_LV' :
        if sum_cur == 1 or (str(sum_cur)[-1] == '1' and str(sum_cur)[-2] != '1'): # is the currency sum one
            if currency == 'LVL':
                cur_in_words += u' lats'
            elif currency == 'EUR':
                cur_in_words += u' eiro'
            elif currency == 'USD':
                cur_in_words += u' dolārs'
            elif currency == 'UAH':
                cur_in_words += u' grivna'
        else:
            if currency == 'LVL':
                cur_in_words += u' lati'
            elif currency == 'EUR':
                cur_in_words += u' eiro'
            elif currency == 'USD':
                cur_in_words += u' dolāri'
            elif currency == 'UAH':
                cur_in_words += u' grivnas'
	
        if sum_frc == 1 or (str(sum_frc)[-1] == '1' and str(sum_frc)[-2] != '1'): # is the fraction sum one
            if currency == 'LVL':
                frc_in_words += u' santīms'
            elif currency == 'EUR' or currency == 'USD' :
                frc_in_words += u' cents'
	    elif currency == 'UAH':
                frc_in_words += u' kapeika'
        else:
            if currency == 'LVL':
                frc_in_words += u' santīmi'
            elif currency == 'EUR' or currency == 'USD':
                frc_in_words += u' centi'
	    elif currency == 'UAH':
                frc_in_words += u' kapeikas'
    #------------------------------------
    if language == 'en_US' :
        if sum_cur == 1 or (str(sum_cur)[-1] == '1' and str(sum_cur)[-2] != '1'): # is the currency sum one
            if currency == 'LVL':
                cur_in_words += u' Latvian lats'
            elif currency == 'EUR':
                cur_in_words += u' euro'
            elif currency == 'USD':
                cur_in_words += u' US dollar'
        else:
            if currency == 'LVL':
                cur_in_words += u' Latvian lats'
            elif currency == 'EUR':
                cur_in_words += u' euros'
            elif currency == 'USD':
                cur_in_words += u' dollars'
        if sum_frc == 1 or (str(sum_frc)[-1] == '1' and str(sum_frc)[-2] != '1'): # is the fraction sum one
            if currency == 'LVL':
                frc_in_words += u' santim'
            elif currency == 'EUR' or currency == 'USD':
                frc_in_words += u' cent'
        else:
            if currency == 'LVL':
                frc_in_words += u' santims'
            elif currency == 'EUR' or currency == 'USD' :
                frc_in_words += u' cents'
    #------------------------------------
    if language == 'ru_RU' :
        if sum_cur == 1 or (str(sum_cur)[-1] == '1' and str(sum_cur)[-2] != '1'): # is the currency sum one
            if currency == 'LVL':
                cur_in_words += u' лат'
            elif currency == 'EUR':
                cur_in_words += u' евро'
            elif currency == 'USD':
                cur_in_words += u' доллар США'
        elif (sum_cur in [2, 3, 4]) or (str(sum_cur)[-1] in ['2', '3', '4'] and str(sum_cur)[-2] != '1'):
            if currency == 'LVL':
                cur_in_words += u' лата'
            elif currency == 'EUR' :
                cur_in_words += u' евро'
            elif currency == 'USD' :
                cur_in_words += u' доллара США'
        elif (sum_cur >= 5 and sum_cur <= 20) or str(sum_cur)[-1] not in [2, 3, 4]:
            if currency == 'LVL' :
                cur_in_words += u' латов'
            elif currency == 'EUR' :
                cur_in_words += u' евро'
            elif currency == 'USD' :
                cur_in_words += u' долларов США'
	
        if sum_frc == 1 or (str(sum_frc)[-1] == '1' and str(sum_frc)[-2] != '1') : # is the fraction one
            if currency == 'LVL' :
                frc_in_words += u' сантим'
            elif currency == 'EUR' or currency == 'USD' :
                frc_in_words += u' цент'
        elif (sum_frc in [2, 3, 4]) or (str(sum_frc)[-1] in ['2', '3', '4'] and str(sum_frc)[-2] != '1') :
            if currency == 'LVL' :
                frc_in_words += u' сантима'
            elif currency == 'EUR' or currency == 'USD' :
                frc_in_words += u' цента'
        elif (sum_frc >= 5 and sum_frc <= 20) or str(sum_frc)[-1] not in [2, 3, 4] :
            if currency == 'LVL' :
                frc_in_words += u' сантимов'
            elif currency == 'EUR' or currency == 'USD' :
                frc_in_words += u' центов'
    #------------------------------------
    if language == 'uk_UA' :
	if sum_cur == 1 or (str(sum_cur)[-1] == '1' and str(sum_cur)[-2] != '1') : # is the currency sum one
	    if currency == 'LVL' :
		cur_in_words += u' лат'
	    elif currency == 'EUR' :
		cur_in_words += u' евро'
	    elif currency == 'USD' :
		cur_in_words += u' доллар США'
	    elif currency == 'UAH' :
		cur_in_words += u' гривня'
	elif (sum_cur in [2, 3, 4]) or (str(sum_cur)[-1] in ['2', '3', '4'] and str(sum_cur)[-2] != '1') :
	    if currency == 'LVL' :
		cur_in_words += u' лата'
	    elif currency == 'EUR' :
		cur_in_words += u' евро'
	    elif currency == 'USD' :
		cur_in_words += u' доллара США'
	    elif currency == 'UAH' :
		cur_in_words += u' гривні'
	elif (sum_cur >= 5 and sum_cur <= 20) or str(sum_cur)[-1] not in [2, 3, 4] :
	    if currency == 'LVL' :
		cur_in_words += u' латов'
	    elif currency == 'EUR' :
		cur_in_words += u' евро'
	    elif currency == 'USD' :
		cur_in_words += u' долларов США'
	    elif currency == 'UAH' :
		cur_in_words += u' гривень'
			
	if sum_frc == 1 or (str(sum_frc)[-1] == '1' and str(sum_frc)[-2] != '1') : # is the fraction one
	    if currency == 'LVL' :
		frc_in_words += u' сантим'
	    elif currency == 'EUR' or currency == 'USD' :
		frc_in_words += u' цент'
	    elif currency == 'UAH' :
		frc_in_words += u' копійка'
	elif (sum_frc in [2, 3, 4]) or (str(sum_frc)[-1] in ['2', '3', '4'] and str(sum_frc)[-2] != '1') :
	    if currency == 'LVL' :
		frc_in_words += u' сантима'
	    elif currency == 'EUR' or currency == 'USD' :
		frc_in_words += u' цента'
	    elif currency == 'UAH' :
		frc_in_words += u' копійки'
	elif (sum_frc >= 5 and sum_frc <= 20) or str(sum_frc)[-1] not in [2, 3, 4] :
	    if currency == 'LVL' :
		frc_in_words += u' сантимов'
	    elif currency == 'EUR' or currency == 'USD' :
		frc_in_words += u' центов'
	    elif currency == 'UAH' :
		frc_in_words += u' копійок'
	frc_in_words = str(sum_frc) + u' коп.'

    return (cur_in_words + ' ' + frc_in_words).strip().encode('utf-8')


def dtowords(sum_integers, language):
    """
    >>> dtowords(0, 'en_US')
    u'zero'

    >>> dtowords(1, 'en_US')
    u'one'

    >>> dtowords(11, 'en_US')
    u'eleven'

    >>> dtowords(169, 'en_US')
    u'one hundred sixty nine'

    >>> dtowords(12345, 'en_US')
    u'twelve thousand three hundred fourty five'

    >>> dtowords(123456, 'en_US')
    u'one hundred twenty three thousand four hundred fifty six'

    >>> dtowords(0, 'lv_LV')
    u'nulle'

    >>> dtowords(1, 'lv_LV')
    u'viens'

    >>> dtowords(11, 'lv_LV')
    u'vienpadsmit'

    >>> dtowords(169, 'lv_LV').encode('utf-8') == 'simts sešdesmit deviņi'
    True

    >>> dtowords(12345, 'lv_LV').encode('utf-8') == 'divpadsmit tūkstoši trīs simti četrdesmit pieci'
    True

    >>> dtowords(123456, 'lv_LV').encode('utf-8') == 'simts divdesmit trīs tūkstoši četri simti piecdesmit seši'
    True

    >>> dtowords(0, 'ru_RU').encode('utf-8') == 'ноль'
    True

    >>> dtowords(1, 'ru_RU').encode('utf-8') == 'один'
    True

    >>> dtowords(11, 'ru_RU').encode('utf-8') == 'одиннадцать'
    True

    >>> dtowords(169, 'ru_RU').encode('utf-8') == 'стo шестьдесят девять'
    True

    >>> dtowords(12345, 'ru_RU').encode('utf-8') == 'двенадцать тысяч триста сорок пять'
    True

    >>> dtowords(123456, 'ru_RU').encode('utf-8') == 'стo двaдцать три тысячи четыреста пятьдесят шесть'
    True


    """
    diginwords = u''
    if sum_integers == 0:
        return wordify('0', 0, language)
    elif sum_integers > 0:
        lengthx = len(str(sum_integers))
        nrchunks = (lengthx / 3)
    if nrchunks < (float(lengthx) / 3) :
        nrchunks+=1
    inc = 1
    while inc <= nrchunks:
        startpos = (lengthx - inc * 3)
        chunklength = 3
        if startpos < 0:
            chunklength += startpos
            startpos = 0
        chunk = str(sum_integers)[startpos : startpos + chunklength]
        wordified = wordify(chunk, inc-1, language)
        inc += 1
        spacer = ''
        if len(diginwords) > 0 :
            spacer = ' '
        diginwords = wordified + spacer + diginwords
    return diginwords

def wordify(chunk, chunknr, language):
    words = u''

    if language == 'lv_LV':
        skaitli = [u'nulle', u'viens', u'divi', u'trīs', u'četri', u'pieci',
                   u'seši', u'septiņi', u'astoņi', u'deviņi']
        skaitlix = [u'nulle', u'vien', u'div', u'trīs', u'četr', u'piec', u'seš',
                    u'septiņ', u'astoņ', u'deviņ']
        skaitli_teens = [u'desmit', u'vienpadsmit', u'divpadsmit', u'trīspadsmit',
                         u'četrpadsmit', u'piecpadsmit', u'sešpadsmit',
                         u'septiņpadsmit', u'astoņpadsmit', u'deviņpadsmit']
        daudzums = [u'simts', u' tūkstotis', u' miljons', u' miljards']
        daudzumsx = [u' simti', u' tūkstoši', u' miljoni', u' miljardi']

    elif language == 'en_US':
        skaitli = [u'zero', u'one', u'two', u'three', u'four', u'five', u'six',
                   u'seven', u'eight', u'nine']
        skaitlix = [u'zero', u'one', u'twen', u'thir', u'four', u'fif', u'six',
                    u'seven', u'eigh', u'nine']
        skaitli_teens = [u'ten', u'eleven', u'twelve', u'thirteen', u'fourteen',
                         u'fifteen', u'sixteen', u'seventeen', u'eighteen', u'nineteen']
        daudzums = [u' hundred', u' thousand', u' million', u' billion']
        daudzumsx = daudzums

    elif language == 'ru_RU':
        skaitli = [u'ноль', u'один', u'два', u'три', u'четыре', u'пять', u'шесть',
                   u'семь', u'восемь', u'девять']
        skaitlix = [u'', u'один', u'двa', u'три', u'четыре', u'пять', u'шесть',
                    u'семь', u'восемь', u'девять']
        skaitli_teens = [u'десять', u'одиннадцать', u'двенадцать', u'тринадцать',
                         u'четырнадцать', u'пятнадцать', u'шестнадцать', u'семнадцать',
                         u'восемнадцать', u'девятнадцать']
        daudzums = [u'стo', u' тысяча', u' миллион', u' миллиард']
        daudzumsx = [u'сoт', u' тысяч', u' миллионов', u' миллиардов']

    elif language == 'uk_UA' :
	skaitli = [u'ноль', u'один', u'два', u'три', u'чотири', u'п\'ять', u'шість',
		    u'сім', u'вісім', u'дев\'ять']
	skaitlix = [u'', u'один', u'двa', u'три', u'чотири', u'п\'ять', u'шість',
		    u'сім', u'вісім', u'дев\'ять']
	skaitli_teens = [u'десять', u'одинадцять', u'дванадцять', u'тринадцять',
			u'чотирнадцять', u'п\'ятнадцять', u'шістнадцять', u'сімнадцять',
			u'вісімнадцять', u'дев\'ятнадцять']
	daudzums = [u'стo', u' тисяча', u' мiллiон', u' мiллiард']
	daudzumsx = [u'сoт', u' тисяч', u' мiллiонiв', u' мiллiардов']
    digit1 = u''
    digit2 = u''
    digit3 = u''
    chunklength = len(chunk)
    # placing digits in right places
    if chunklength == 1:
        digit3 = chunk[0 : 1]
    if chunklength == 2:
        digit2 = chunk[0 : 1]
        digit3 = chunk[1 : 2]
    if chunklength == 3:
        digit1 = chunk[0 : 1]
        digit2 = chunk[1 : 2]
        digit3 = chunk[-1]
    # processing zero
    if chunklength == 1 and digit3  == '0' :
        return skaitli[0]
    # processing hundreds
    if chunklength == 3 :
        if digit1 == '1' :
            if language == 'lv_LV' or language == 'ru_RU' or language == 'uk_UA':
                words += daudzums[0]
            elif language == 'en_US' :
                words += skaitli[int(digit1)] + daudzumsx[0]
        else :
            if language == 'lv_LV' :
                if int(digit1) > 1 : words += skaitli[int(digit1)] + daudzumsx[0]
            elif language == 'en_US' :
                if int(digit1) > 1 : words += skaitli[int(digit1)] + daudzumsx[0]
            elif language == 'ru_RU' :
                if int(digit1) == 2 :
                    words += u'двести'
                elif int(digit1) == 3 :
                    words += u'триста'
                elif int(digit1) == 4 :
                    words += u'четыреста'
                elif int(digit1) >= 5 :
                    words += skaitli[int(digit1)] + daudzumsx[0]
	    elif language == 'uk_UA' :
		if int(digit1) == 2 :
		    words += u'двісті'
		elif int(digit1) == 3 :
		    words += u'триста'
		elif int(digit1) == 4 :
		    words += u'чотириста'
		elif int(digit1) >= 5 :
		    words += skaitli[int(digit1)] + daudzumsx[0]
    # processing tens
    if chunklength > 1:
        spacer = ''
        if len(words) > 0 : spacer = ' '
        if digit2 == '1':
	    if language == 'lv_LV' or language == 'en_US' or language == 'ru_RU' or language == 'uk_UA':
                words += spacer + skaitli_teens[int(digit3)]
        else:
            if language == 'lv_LV':
                if int(digit2) > 1 and int(digit2) > 0:
                    words += spacer + skaitlix[int(digit2)] + u'desmit'
            elif language == 'en_US':
                if int(digit2) > 1 and int(digit2) > 0:
                    words += spacer + skaitlix[int(digit2)] + u'ty'
	    elif language == 'ru_RU':
                if int(digit2) > 1 and int(digit2) < 4:
                    words += spacer + skaitlix[int(digit2)] + u'дцать'
                elif digit2 == '4':
                    words += spacer + u'сорок'
                elif int(digit2) >= 5 and int(digit2) != 9:
                    words += spacer + skaitlix[int(digit2)] + u'десят'
                elif digit2 == '9':
                    words += spacer + u'девяносто'
	    elif language == 'uk_UA' :
		if int(digit2) > 1 and int(digit2) < 4:
		    words += spacer + skaitlix[int(digit2)] + u'дцять'
		elif digit2 == '4':
		    words += spacer + u'сорок'
		elif int(digit2) >= 5 and int(digit2) != 9:
		    words += spacer + skaitlix[int(digit2)] + u'десят'
		elif digit2 == '9':
		    words += spacer + u'дев\'яносто'
    # processing ones
    if chunklength > 0 and digit2 != '1' :
        spacer = ''
        if len(words) > 0: spacer = u' '
        if language == 'lv_LV' or language == 'en_US':
	    if int(digit3) > 0:
                words += spacer + skaitli[int(digit3)]
	elif language == 'ru_RU':
            if chunknr == 1:
                if int(digit3) == 1:
                    words += spacer + u'одна'
                elif int(digit3) == 2: 
                    words += spacer + u'две'
                elif int(digit3) >= 3 and int(digit3) != 0: 
                    words += spacer + skaitli[int(digit3)]
            else:
                if int(digit3) > 0: words += spacer + skaitli[int(digit3)]
	elif language == 'uk_UA' :
	    if chunknr == 1 :
		if int(digit3) == 1 : words += spacer + u'одна'
		elif int(digit3) == 2 : words += spacer + u'дві'
		elif int(digit3) >= 3 and int(digit3) != 0: words += spacer + skaitli[int(digit3)]
	    else:
		if int(digit3) > 0 : words += spacer + skaitli[int(digit3)]
    # end processing
    if len(words) > 0 :
        
        if digit3 == '1' and chunknr > 0:
	    return words + daudzums[chunknr]
        elif digit3 != '1' and chunknr > 0:
	    if language == 'lv_LV' or language == 'en_US' :
		return words + daudzumsx[chunknr]
	    elif language == 'ru_RU' :
		if (int(digit3) == 2 or int(digit3) == 3 or int(digit3) == 4) and digit2 != '1' :
	    	    if chunknr == 1 :
			return words + u' тысячи'
	    	    elif chunknr == 2 :
			return words + u' миллионa'
	    	    elif chunknr == 3 :
			return words + u' миллиардa'
		else:
	    	    return words + daudzumsx[chunknr]
	    elif language == 'uk_UA' :
		if (int(digit3) == 2 or int(digit3) == 3 or int(digit3) == 4) and digit2 != '1' :
		    if chunknr == 1 :
			return words + u' тисячі'
		    elif chunknr == 2 :
			return words + u' мілліонa'
		    elif chunknr == 3 :
			return words + u' мілліардa'
		else:
		    return words + daudzumsx[chunknr]
	else:
	    return words
    else:
	return ''


if __name__ == '__main__':
    import doctest
    doctest.testmod()

