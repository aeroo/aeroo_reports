# Copyright (c) 2008 marscel.wordpress.com
#
# Copyright (c) 2011 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>

# Code39.py v1
# Requires Python and Python Imaging Library (PIL), 
# has been tested with Python v2.6 and PIL v1.1.6

# Usage example:
# code39.py 100 2 "Hello World" barcode.png
#
# This creates a PNG image "barcode.png" containing a barcode of the height of 100px
# a min line width of 2px with "Hello World" encoded as "*HELLO WORLD*" in Code 39

from PIL import Image, ImageDraw, ImageFont
from openerp.tools import config, ustr
import os, sys

marginx = 10
marginy = 10
fontsize = 15

charmap = {
'*':[0,3,0,1,2,1,2,1,0],
'-':[0,3,0,1,0,1,2,1,2],
'$':[0,3,0,3,0,3,0,1,0],
'%':[0,1,0,3,0,3,0,3,0],
' ':[0,3,2,1,0,1,2,1,0],
'.':[2,3,0,1,0,1,2,1,0],
'/':[0,3,0,3,0,1,0,3,0],
'+':[0,3,0,1,0,3,0,3,0],
'0':[0,1,0,3,2,1,2,1,0],
'1':[2,1,0,3,0,1,0,1,2],
'2':[0,1,2,3,0,1,0,1,2],
'3':[2,1,2,3,0,1,0,1,0],
'4':[0,1,0,3,2,1,0,1,2],
'5':[2,1,0,3,2,1,0,1,0],
'6':[0,1,2,3,2,1,0,1,0],
'7':[0,1,0,3,0,1,2,1,2],
'8':[2,1,0,3,0,1,2,1,0],
'9':[0,1,2,3,0,1,2,1,0],
'A':[2,1,0,1,0,3,0,1,2],
'B':[0,1,2,1,0,3,0,1,2],
'C':[2,1,2,1,0,3,0,1,0],
'D':[0,1,0,1,2,3,0,1,2],
'E':[2,1,0,1,2,3,0,1,0],
'F':[0,1,2,1,2,3,0,1,0],
'G':[0,1,0,1,0,3,2,1,2],
'H':[2,1,0,1,0,3,2,1,0],
'I':[0,1,2,1,0,3,2,1,0],
'J':[0,1,0,1,2,3,2,1,0],
'K':[2,1,0,1,0,1,0,3,2],
'L':[0,1,2,1,0,1,0,3,2],
'M':[2,1,2,1,0,1,0,3,0],
'N':[0,1,0,1,2,1,0,3,2],
'O':[2,1,0,1,2,1,0,3,0],
'P':[0,1,2,1,2,1,0,3,0],
'Q':[0,1,0,1,0,1,2,3,2],
'R':[2,1,0,1,0,1,2,3,0],
'S':[0,1,2,1,0,1,2,3,0],
'T':[0,1,0,1,2,1,2,3,0],
'U':[2,3,0,1,0,1,0,1,2],
'V':[0,3,2,1,0,1,0,1,2],
'W':[2,3,2,1,0,1,0,1,0],
'X':[0,3,0,1,2,1,0,1,2],
'Y':[2,3,0,1,2,1,0,1,0],
'Z':[0,3,2,1,2,1,0,1,0]
}

def create_c39(height, smallest, text):
    pixel_length = 0
    i = 0
    newtext = ""
    machinetext = "*" + text + "*"
    seglist = []
    while i < len(machinetext):
        char = machinetext[i].capitalize()
        i = i + 1
        try:
            cmap = charmap[char]
            if len(cmap) != 9:
                continue
            
            j = 0
            while j < 9:
                seg = int(cmap[j])
                
                if seg == 0 or seg == 1:
                    pixel_length = pixel_length + smallest
                    seglist.append(seg)
                elif seg == 2 or seg == 3:
                    pixel_length = pixel_length + smallest * 3
                    seglist.append(seg)
                
                j = j + 1
            
            newtext += char
        except:
            continue
    
    pixel_length = pixel_length + 2*marginx + len(newtext) * smallest
    pixel_height = height + 2*marginy + fontsize
    
    barcode_img = Image.new('RGB', [pixel_length, pixel_height], "white")
    
    if len(seglist) == 0:
        return barcode_img
    
    i = 0
    draw = ImageDraw.Draw(barcode_img)
    current_x = marginx
    
    while i < len(seglist):
        seg = seglist[i]
        color = (255, 255, 255)
        wdth = smallest
        
        if seg == 0 or seg == 2:
            color = 0
            if seg == 0:
                wdth = smallest
            else:
                wdth = smallest * 3
        elif seg == 1 or seg == 3:
            color = (255, 255, 255)
            if seg == 1:
                wdth = smallest
            else:
                wdth = smallest * 3
        
        j = 1
        
        while j <= wdth:
            draw.line((current_x, marginy, current_x, marginy+height), fill=color)
            current_x = current_x + 1            
            j = j + 1
        
        if ((i+1) % 9) == 0:        
            j = 1
            while j <= smallest:
                draw.line((current_x, marginy, current_x, marginy+height), fill=(255,255,255))
                current_x = current_x + 1
                j = j + 1            
        i = i + 1

    ad = os.path.abspath(os.path.join(ustr(config['root_path']), u'addons'))
    mod_path_list = map(lambda m: os.path.abspath(ustr(m.strip())), config['addons_path'].split(','))
    mod_path_list.append(ad)

    for mod_path in mod_path_list:
        font_file = mod_path+os.path.sep+ \
                    "report_aeroo"+os.path.sep+"barcode"+os.path.sep+"FreeMonoBold.ttf"
        if os.path.lexists(font_file):
            font = ImageFont.truetype(font_file, fontsize)
    
    draw.text((pixel_length/2 - len(newtext)*(fontsize/2)/2-len(newtext), height+fontsize), newtext, font=font, fill=0)
    
    del draw
    
    return barcode_img

