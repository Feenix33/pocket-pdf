# Pocket Roff
# get library unidecode to get rid of accents
# TODO
# rethink the whole processor to a statemachine?

from reportlab.platypus import Paragraph, Frame, FrameBreak, PageBreak, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
import PIL

from cfgpocket import Cfg
import re
import os

class Pocketroff:
    """Create the reportlab content buffer to feed into the renderer"""
    def __init__(self, spacers=None):
        #self.fontName = 'Courier'
        #self.fontName = 'Times'
        self.fontName = 'Helvetica'
        self.fontSize = 7
        self.alignment = 0
        self.defineFonts()
        self.styleActive = self.styleNormal
        self.titleContent = []
        self.bodyContent = []
        self.content = self.bodyContent
        self.spacers = True # space between paragraphs
        self.breakers = True # new frame between file reads
        self.numbered = False
        self.pushState()

    def pushState(self):
        """save the state"""
        self._fontName = self.fontName
        self._fontSize = self.fontSize
        self._styleActive = self.styleActive
        self._spacers = self.spacers
        self._breakers = self.breakers
        self._alignment = self.alignment
        self._numbered = self.numbered

    def popState(self):
        """restore the state"""
        self.fontName = self._fontName
        self.fontSize = self._fontSize
        self.styleActive = self._styleActive
        self.spacers = self._spacers
        self.breakers = self._breakers
        self.alignment = self._alignment
        self.numbered = self._numbered
        self.defineFonts()
    
    def defaultFont(self):
        self.fontName = 'Helvetica'
        self.fontSize = 7
        self.alignment = 0
        self.defineFonts()

    def defineFonts(self):
        """Another function because of dependencies, only called internally"""
        leadSpace = max(self.fontSize+1, self.fontSize*1.1) # space one line to the next
        self.styleNormal = ParagraphStyle(name='Normal', fontSize= self.fontSize, spaceAfter= 0, spaceBefore= 0, leading=leadSpace,alignment=self.alignment,fontName=self.fontName)
        self.styleHeading = ParagraphStyle(name='Heading', fontSize= self.fontSize, spaceAfter= self.fontSize, spaceBefore= 0, leading=leadSpace,alignment=1,fontName=self.fontName+"-Bold")

    def newPage(self):
        self.content.append(PageBreak())

    def text(self, text):
        """first gen, kill this"""
        styleNormal = ParagraphStyle(name='Normal', fontSize= 7, spaceAfter= 0, spaceBefore= 0, leading=8,)
        content = []
        for line in text:
            content.append(Paragraph(line, styleNormal))
            content.append(Spacer(0, styleNormal.leading))
        return content

    def processFile(self, filename):
        with open(filename, "r") as file:
            text = file.readlines()
        #run through the cleaner
        text = self.textCleaner(text)

        self.processInput(text, self.numbered)
        #new page for next recipe
        if self.breakers: self.newPage()

    def processRecipeFile(self, tokens):
        """Assumes line one is title, then ingredients, then steps"""
        filename = tokens[0]

        print ("Processing recipe ",filename)
        text = ''
        with open(filename, "r", errors='ignore') as file:
            text = file.readlines()

        #set recipe defaults
        self.pushState()
        self.spacers = False

        #run through the compressor
        if 'compress' in tokens:
            text = self.textCompressor(text)

        #first line is heading
        self.processData(text[0], style=self.styleHeading,forceSpacer=True,isNumber=False, resetNumber=True)

        #ingredients until blank line
        jj = 1
        for line in text[1:]:
            if len(line) == 0 or line == '\n':
                break
            else:
                jj+=1

        #steps
        self.processInput(text[1:jj+1])
        k = jj+1
        isNumber = False
        if 'number' in tokens:
            isNumber = True
        self.processInput(text[k:], isNumber=isNumber)

        #restore
        self.popState()

        #new page for next recipe
        self.newPage()

    def textCleaner(self, text):
        problems = {'½': '1/2',
                    '¼': '1/4',
                    '\n': '',
                    'é': 'e',
                    '•': '',  #degree
                    }
        for prob,ans in problems.items():
            text = [re.sub(prob,ans,line) for line in text]
        return text

    def textCompressor(self, text):
        wordList = {'teaspoon': 'tsp',
                    'Teaspoon': 'tsp',
                    'tablespoon': 'Tbl',
                    'Tablespoon': 'Tbl',
                    'ounces': 'oz',
                    'cup': 'c',
                    'cook for': 'cook',
                    'Cook for': 'Cook',
                    'large': 'lg',
                    'medium': 'med',
                    'small': 'sml',
                    'with a tight fitting lid': '',
                    'minute': 'min',
                    'second': 'sec',
                    'bake for': 'bake',
                    'Add the': 'Add',
                    'add the': 'add',
                    'from the': 'from',
                    'the oven': 'oven',
                    }
        for word,abbrev in wordList.items():
            text = [re.sub(word,abbrev,line) for line in text]
        return text

    def resetNumber(self):
        self.content.append(Paragraph('<seqreset id="cme"/>', self.styleNormal))

    def processImage(self, filename):
        image = PIL.Image.open(filename[0])
        iw, ih = image.size
        imR = iw/ih
        myR = 2.2/3.8
        if imR < myR:
            ph = 3.8
            pw = (ph*iw)/ih
        else:
            pw = 2.2
            ph = (pw*ih)/iw
        #self.newPage()
        #self.content.append(Image(filename[0], width=2.2*inch, height=3.8*inch))
        self.content.append(Image(filename[0], width=pw*inch, height=ph*inch))

    def processCommand(self, line):
        #print (line.lower().split())
        tokens = line.split()
        match tokens[0].lower():
            case ".image":
                self.processImage(tokens[1:])
            case ".title":
                self.content = self.titleContent
            case ".body":
                self.content = self.bodyContent
            case ".heading":
                if len(tokens) > 1:
                    #self.processData("<para alignment=center><b>"+line[7:]+"</b></para>", forceSpacer=True)
                    self.processData(line[9:], style=self.styleHeading,forceSpacer=True)
            case ".file":
                for fn in tokens[1:]:
                    self.processFile(fn)
            case ".recipe":
                self.processRecipeFile(tokens[1:])
            case ".np" | ".new": # new page
                self.newPage()
            case ".verbal": #message to screen
                print (" ".join(tokens[1:]))
            case ".defaultfont":
                self.defaultFont()
            case ".fontname":
                self.fontName = tokens[1]
                self.defineFonts()
            case ".fontsize":
                self.fontSize = int(tokens[1])
                self.defineFonts()
            case ".alignment":
                self.alignment = int(tokens[1])
                self.defineFonts()
            case ".spacers":
                self.spacers = True if int(tokens[1]) else False
            case ".numbered":
                if int(tokens[1]) == 0: self.numbered = False
                elif int(tokens[1]) > 0: self.numbered = True
                elif int(tokens[1]) < 0: self.resetNumber()
            case ".breakers":
                self.breakers = True if int(tokens[1]) else False
            case _:
                print ("Unknown command: ", line)

    def processData(self, line, **kwargs):
        style = kwargs['style'] if 'style' in kwargs else self.styleNormal
        #if kwargs: print (kwargs)
        forceSpacer = kwargs['forceSpacer'] if 'forceSpacer' in kwargs else False
        isNumber = kwargs['isNumber'] if 'isNumber' in kwargs else False
        resetNumber = kwargs['resetNumber'] if 'resetNumber' in kwargs else False

        if resetNumber: 
            self.resetNumber()
            #self.content.append(Paragraph('<seqreset id="cme"/>', style))

        prefix = '<seq id="cme"> ' if isNumber and len(line) > 0 else ""
        self.content.append(Paragraph(prefix+line, style))
        if len(line) == 0 or line == '\n': 
            self.content.append(Spacer(0, style.leading))
        if self.spacers or forceSpacer:
            self.content.append(Spacer(0, style.leading))

    def process(self, text):
        self.bodyContent = []
        self.titleContent = []
        self.content = self.bodyContent
        self.processInput(text)
        return self.bodyContent, self.titleContent

    def processComment(self, line):
        return

    def processInput(self, text, isNumber=False, resetNumber=False):
        """Process the passed text into reportlab paragraphs, etc"""
        for line in text:
            if len(line) > 0 and line[0] == '.': # self is a command
                self.processCommand(line)
            elif len(line) > 0 and line[0] == '#': # comment
                self.processComment(line)
            else:
                self.processData(line, isNumber=isNumber, resetNumber=resetNumber)
