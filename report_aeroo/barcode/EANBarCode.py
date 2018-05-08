# Copyright (c) 2009-2011 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>

from openerp.tools import config, ustr
fontsize = 12

"""
This class generate EAN bar code, it required PIL (python imaging library)
installed.

If the code has not checksum (12 digits), it added automatically.

Create bar code sample :
   from EANBarCode import EanBarCode
   bar = EanBarCode()
   bar.getImage("9782212110708",50,"gif")

"""

class EanBarCode:
   """ Compute the EAN bar code """
   def __init__(self):
      A = {0 : "0001101", 1 : "0011001", 2 : "0010011", 3 : "0111101", 4 : "0100011", 
           5 : "0110001", 6 : "0101111", 7 : "0111011", 8 : "0110111", 9 : "0001011"}
      B = {0 : "0100111", 1 : "0110011", 2 : "0011011", 3 : "0100001", 4 : "0011101",
           5 : "0111001", 6 : "0000101", 7 : "0010001", 8 : "0001001", 9 : "0010111"}
      C = {0 : "1110010", 1 : "1100110", 2 : "1101100", 3 : "1000010", 4 : "1011100",
           5 : "1001110", 6 : "1010000", 7 : "1000100", 8 : "1001000", 9 : "1110100"}
      self.groupC = C

      self.family = {0 : (A,A,A,A,A,A), 1 : (A,A,B,A,B,B), 2 : (A,A,B,B,A,B), 3 : (A,A,B,B,B,A), 4 : (A,B,A,A,B,B),
                     5 : (A,B,B,A,A,B), 6 : (A,B,B,B,A,A), 7 : (A,B,A,B,A,B), 8 : (A,B,A,B,B,A), 9 : (A,B,B,A,B,A)}


   def makeCode(self, code):
      """ Create the binary code
      return a string which contains "0" for white bar, "1" for black bar, "L" for long bar """
      
      # Convert code string in integer list
      self.EAN13 = []
      for digit in code:
         self.EAN13.append(int(digit))
         
      # If the code has already a checksum
      if len(self.EAN13) == 13:
         # Verify checksum
         self.verifyChecksum(self.EAN13)
      # If the code has not yet checksum
      elif len(self.EAN13) == 12:
         # Add checksum value
         self.EAN13.append(self.computeChecksum(self.EAN13))
      
      # Get the left codage class
      left = self.family[self.EAN13[0]]
      
      # Add start separator
      strCode = 'L0L'
      
      # Compute the left part of bar code
      for i in range(0,6):
         strCode += left[i][self.EAN13[i+1]]
      
      # Add middle separator 
      strCode += '0L0L0'
      
      # Compute the right codage class
      for i in range (7,13):
         strCode += self.groupC[self.EAN13[i]]
      
      # Add stop separator
      strCode += 'L0L'
      
      return strCode


   def computeChecksum(self, arg):
      """ Compute the checksum of bar code """
      # UPCA/EAN13
      weight=[1,3]*6
      magic=10
      sum = 0
      
      for i in range(12):         # checksum based on first 12 digits.
         sum = sum + int(arg[i]) * weight[i]
      z = ( magic - (sum % magic) ) % magic
      if z < 0 or z >= magic:
         return None
      return z


   def verifyChecksum(self, bits): 
      """ Verify the checksum """
      computedChecksum = self.computeChecksum(bits[:12])
      codeBarChecksum = bits[12]
      
      if codeBarChecksum != computedChecksum:
         raise Exception ("Bad checksum is %s and should be %s"%(codeBarChecksum, computedChecksum))


   def getImage(self, value, height = 50, xw=1, rotate=None, extension = "PNG"):
      """ Get an image with PIL library 
      value code barre value
      height height in pixel of the bar code
      extension image file extension"""
      from PIL import Image, ImageFont, ImageDraw
      import os
      from string import lower, upper
      
      # Get the bar code list
      bits = self.makeCode(value)
      
      # Get thee bar code with the checksum added
      code = ""
      for digit in self.EAN13:
         code += "%d"%digit
      
      # Create a new image
      position = 8
      im = Image.new("L",(len(bits)+position,height+2))
      
      # Load font
      ad = os.path.abspath(os.path.join(ustr(config['root_path']), u'addons'))
      mod_path_list = map(lambda m: os.path.abspath(ustr(m.strip())), config['addons_path'].split(','))
      mod_path_list.append(ad)

      for mod_path in mod_path_list:
          font_file = mod_path+os.path.sep+ \
                      "report_aeroo"+os.path.sep+"barcode"+os.path.sep+"FreeMonoBold.ttf"#"courB08.pil"
          if os.path.lexists(font_file):
              font = ImageFont.truetype(font_file, fontsize)
              #font = ImageFont.load(font_file)
      
      # Create drawer
      draw = ImageDraw.Draw(im)
      
      # Erase image
      draw.rectangle(((0,0),(im.size[0],im.size[1])),fill=256)
      
      # Draw first part of number
      draw.text((0, height-9), code[0], font=font, fill=0)
      
      # Draw first part of number
      draw.text((position+3, height-9), code[1:7], font=font, fill=0)
         
      # Draw second part of number
      draw.text((len(bits)/2+2+position, height-9), code[7:], font=font, fill=0)
      
      # Draw the bar codes
      for bit in range(len(bits)):
         # Draw normal bar
         if bits[bit] == '1':
            draw.rectangle(((bit+position,0),(bit+position,height-10)),fill=0)
         # Draw long bar
         elif bits[bit] == 'L':
            draw.rectangle(((bit+position,0),(bit+position,height-3)),fill=0)
            
      # Save the result image
      return im

