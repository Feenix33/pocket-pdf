"""
Four Page Pocket Document
72 points per inch

fonts: Helvetica, Times, Courier
Alignment: 0-TA_LEFT 1-center 2-right 4-justify

This order:
    3R   2R
    4    1

Eight is 
7 6 5 4 upside down
8 1 2 3

commands
.font <font params> adjust the current font
.addstyle name <font params> create a new style but no set
.style name use the specified style
.newpage    force a framebreak (page because pocket docs)
.list [reset|n] start a list, optionally reset numbered list or set start number
.endlist [true|false] end a list, optionally add spacer
.markdown  switch to markdown like processing mode (end with .normal)
.normal    switch to normal processing mode
.spacer   add a spacer of current font size

MARKDOWN-LIKE:
# Title
## Heading1
### Heading2
#### Heading3
-list unordered list (bulleted)
1. list ordered list (numbered)
**bold**  (auto-close at eol)
*italic*  (auto-close at eol)
~~strikethrough~~  (auto-close at eol)
-[] task list uncompleted
-[x] task list completed
-- horizontal rule
.command  process a command not like markdown

No code blocks, block quotes, images

TODO:
* debug how to put multiple font mods on a line
* two+ font mods should stay together or override
* list push/pop
* remove spacer handling and add before/afters space
* add bullet style
* test nested lists
* numbered lists
* command to do list or numbered list
- add markdown processor (should it use mode or parser type)
* right left center alignment in commands
- config file and command line options
- meta data for pdf
- title page formatting
- list without bullet
- alternative list approach using reportlab ListFlowable
- better handling of large paragraphs that don't fit in a frame
- numbered lists w/levels
- make a central switch styles function

TODO BUGS:
* Nested numbered lists does not turn off correctly
* mixed list type pops

"""
import random
from reportlab.lib.pagesizes import A4, landscape, letter, portrait
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
import reportlab.lib.enums 
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (Frame, FrameBreak, Spacer, Paragraph,
    BaseDocTemplate, PageTemplate, PageBreak, 
    ListItem, ListFlowable,
)
import copy

"""
    Try this approach to lists?
    ------
    def aList(self):
        #TODO make this generic?
        style = self.currentStyle
        t = ListFlowable(
        [
            Paragraph("Item no.1", style),
            ListItem(Paragraph("Item no. 2", style),bulletColor="green",value=7),
            ListFlowable(
                    [
                    Paragraph("sublist item 1", style),
                    ListItem(Paragraph('sublist item 2', style),bulletColor='red',value='square')
                    ],
                    bulletType='bullet',
                    start='square',
                    ),
            Paragraph("Item no.4", style),
            ],
            bulletType='i'
        )
        return t
"""


class Booklet: 
    """ The render engine for the 4up pocket book maker
        Proper add the rotation which has to be done manually
    """
    def __init__(self,nameOut="output.pdf", docSize=letter, marginSize=0.3*inch, showFrames=False, drawFolds=True):
        self.docSize = docSize
        self.margin = marginSize # CFG
        self.showFrames = showFrames # CFG
        self.drawFolds = drawFolds # CFG

        self.canvas = Canvas(nameOut, pagesize=self.docSize)
        self.initStyles()
        self.currentStyle = self.styles["Normal"]
        self.frameN = 0
        #self.spacer = False # need to CFG this
        self.mode = 'normal'
        self.parser = 'normal' # normal or markdown
        self.styleStack = []
        self.modeStack = []
        self.bulletNumberStack = []
        self.stack_bulletNumbered = []
        self.bulletLevel = 0
        self.bulletNumbered = False

    def initStyles(self, baseFontSize=10):
        self.styles = {
            "Normal": self.buildParagraphStyle(name='Normal',fontSize=baseFontSize),
            "NormalNS": self.buildParagraphStyle(name='Normal',fontSize=baseFontSize,spaceAfter=0),
            "Title": self.buildParagraphStyle(name='Title', fontSize=baseFontSize+4,alignment=reportlab.lib.enums.TA_CENTER),
            "Heading1": self.buildParagraphStyle(name='Heading1', fontSize=baseFontSize+4),
            "Heading2": self.buildParagraphStyle(name='Heading2', fontSize=baseFontSize+2),
            "Heading3": self.buildParagraphStyle(name='Heading3', fontSize=baseFontSize,),
            "Bullet": self.buildParagraphStyle(name='Bullet', fontSize=baseFontSize,spaceAfter=0,bulletIndent=10,leftIndent=2*10),
        }
    def addStyle(self, name, paragraphStyle):
        self.styles[name] = paragraphStyle
    
    def pushStyle(self):
        self.styleStack.append(copy.copy(self.currentStyle))
        self.modeStack.append(self.mode)
        self.bulletNumberStack.append(self.bulletNumbered)
        self.stack_bulletNumbered.append(self.bulletNumbered)
        #print (f"Pushed style {self.currentStyle.name}, mode {self.mode}")

    def popStyle(self):
        if len(self.styleStack) > 0:
            self.currentStyle = self.styleStack.pop()
            self.mode = self.modeStack.pop()
            self.bulletNumbered = self.bulletNumberStack.pop()
            self.bulletNumbered = self.stack_bulletNumbered.pop()
            #print (f"Popped style to {self.currentStyle.name}, mode {self.mode}")

    def useBulletStyle(self):
        self.currentStyle = self.styles["Bullet"]
        leftIndent = self.bulletLevel * 10
        bulletIndent = (1+ self.bulletLevel) * 10
        self.processCommand(f".font leftIndent={leftIndent} bulletIndent={bulletIndent}")
        self.bulletLevel += 1
        self.mode = 'list'

    def alignmentStrToEnum(self, alignstr):
        match alignstr.lower():
            case 'left':
                return reportlab.lib.enums.TA_LEFT
            case 'center':
                return reportlab.lib.enums.TA_CENTER
            case 'right':
                return reportlab.lib.enums.TA_RIGHT
            case 'justify':
                return reportlab.lib.enums.TA_JUSTIFY
            case _:
                return reportlab.lib.enums.TA_LEFT

    def buildParagraphStyle(self, name='CurrentStyle',
            textColor=colors.black,
            backColor=colors.white,
            alignment=reportlab.lib.enums.TA_LEFT,
            align=None,
            firstLineIndent=0,
            leftIndent=0,
            bulletIndent=0,
            fontName='Helvetica',
            fontSize=10,
            spaceBefore=0,
            spaceAfter=None,
            leading=None):
        if leading == None: leading = int(fontSize * 1.2)
        if spaceAfter == None: spaceAfter = int(fontSize * 1.2)
        tempAlign = alignment if align == None else self.alignmentStrToEnum(align.lower())
        return ParagraphStyle(
            name=name,
            backColor = backColor,
            textColor = textColor,
            alignment = tempAlign,
            firstLineIndent = firstLineIndent,
            leftIndent=leftIndent,
            bulletIndent=bulletIndent,
            fontName=fontName,
            fontSize=fontSize,
            spaceBefore=spaceBefore,
            spaceAfter=spaceAfter,
            leading=leading)
    
    def adjustCurrentStyle(self, modifiers):
        # adust the current style in place; save with push/pop if needed
        for mod in modifiers:
            cmd = mod.split("=")
            match cmd[0]:
                case 'textColor' | 'backColor': 
                    setattr(self.currentStyle, cmd[0], eval('colors.'+cmd[1]))
                case 'alignment' | 'firstLineIndent' | 'fontSize' | 'leading' | 'leftIndent' | 'bulletIndent':
                    setattr(self.currentStyle, cmd[0], int(cmd[1])) 
                case 'align':
                    setattr(self.currentStyle, 'alignment', self.alignmentStrToEnum(cmd[1].lower()))

    def string2Style(self, inputstr):
        instr = inputstr.replace(" ","")
        indict = dict(item.split("=") for item in instr.split(","))
        for k,v in indict.items():
            match k:
                case 'textColor' | 'backColor': 
                    #indict[k] = eval('colors.'+v)
                    indict[k] = eval('colors.'+v)
                case 'alignment' | 'firstLineIndent' | 'fontSize' | 'leading' | 'leftIndent' | 'bulletIndent':
                    indict[k] = int(v)
        return self.buildParagraphStyle(**indict)

    def RotatePage(self):
        self.canvas.translate(self.docSize[0]/2, self.docSize[1]/2)
        self.canvas.rotate(180)
        self.canvas.translate(-self.docSize[0]/2, -self.docSize[1]/2)

    def addSpacer(self):
        self.currentFrame.add(Spacer(1, self.currentStyle.fontSize), self.canvas)

    #xxyy====================================================================================
    def processCommand(self, line):
        tokens = line.split()
        match tokens[0].lower():
            case ".newpage":
                self.addContent(FrameBreak())
            case ".list": # start a list  
                if len(tokens) == 1:
                    self.pushStyle()
                    self.useBulletStyle()
                    self.bulletNumbered = False
                else: # > 1
                    if self.mode != 'list':
                        self.pushStyle()
                        self.useBulletStyle()
                        self.bulletNumbered = True
                    if tokens[1].lower() == "reset":
                        self.addContent(Paragraph("<seqreset>", self.currentStyle)) # TODO can we not add content here?
                    elif tokens[1].isdigit():
                        digit = int(tokens[1])
                        self.addContent(Paragraph(f"<seqreset base={digit}>", self.currentStyle))
            case ".endlist": # end a list
                self.processCommand(".pop")
                self.bulletLevel = max(self.bulletLevel-1,0)
                if len(tokens) > 1:
                    if tokens[1].lower() == "true":
                        self.addSpacer()
            case ".spacer":
                self.addSpacer()
            case ".push":
                self.pushStyle()
            case ".pop":
                self.popStyle()
            case ".font": #adjust the current font
                if len(tokens) > 1:
                    sArg = " ".join(tokens[1:])
                    #self.currentStyle = self.string2Style(sArg)
                    self.adjustCurrentStyle(tokens[1:])
            case ".addstyle": # create a new style and add to the library
                if len(tokens) > 2:
                    sArg = " ".join(tokens[2:])
                    self.addStyle(tokens[1], self.string2Style(sArg))
            case ".style": # pick style by name from the library
                if len(tokens) > 1:
                    self.currentStyle = self.styles[tokens[1]]
            case ".markdown":
                self.parser = 'markdown'
            case ".normal":
                self.parser = 'normal'
            case _:
                print (f"Unhandled command {line}")

    #xxyy====================================================================================
    #def addContent(self, obj, spacer=True):
    def addContent(self, obj):
        #TODO if obj is continuously too large need to punch out
        #TODO if spacer don't put if we moved to a new column
        if self.currentFrame.add(obj, self.canvas) == 0: # won't handle a giant paragraph
            self.frameN += 1
            if self.frameN >= len(self.frameList):
                self.frameN = 0
                self.canvas.showPage()
                self.frameList = self.defineFrames(self.docSize, self.margin)
                self.frameRotate = self.defineRotate()
                if self.drawFolds: self.drawFoldlines(self.canvas)
            self.currentFrame = self.frameList[self.frameN]
            
            if self.frameRotate[self.frameN]:
                self.RotatePage()
            if self.showFrames: self.currentFrame.drawBoundary(self.canvas)
            self.currentFrame.add(obj, self.canvas) #adding the failed content
        #if spacer:
        #    self.addSpacer()
    #====================================================================================

    def processText(self, line):
        #    if self.currentFrame.add(para, self.canvas) == 0: # won't handle a giant paragraph
        # some preprocessing 
        # TODO rethink this
        if self.mode == 'list':
            if self.bulletNumbered:
                line = "<seq> " + line
            else:
                line = "<bullet>&bull;</bullet>" + line
        #self.addContent(Paragraph(line, self.currentStyle), self.spacer)
        self.addContent(Paragraph(line, self.currentStyle))

    def build(self):
        #self.canvas.setAuthor(Cfg.get("author"))
        #self.canvas.setTitle(Cfg.get("title"))
        #self.canvas.setSubject(Cfg.get("subject"))
        #self.canvas.setKeywords(Cfg.get("keywords"))
        self.canvas.save()

    def markdownAttributes(self, line):
        # parse markdown line for attributes like bold italic strikethough
        # return modified line
        # loop through the line
        priorChar = ''
        closeBold = False
        closeItalic = False
        closeStrike = False
        rtnLine = ''
        i = 0
        while i < len(line):
            char = line[i]
            match char:
                case '*': # bold italic or escaped asterisk
                    if priorChar == '*': # bold
                        if closeBold:
                            rtnLine += "</b>"
                            closeBold = False
                        else:
                            rtnLine += "<b>"
                            closeBold = True
                        priorChar = ''
                    elif priorChar == "\\": # escaped
                        rtnLine += '*'
                        priorChar = ''
                    else: # italic
                        if closeItalic:
                            rtnLine += "</i>"
                            closeItalic = False
                        else:
                            rtnLine += "<i>"
                            closeItalic = True
                        priorChar = ''
                case _:
                    rtnLine += char
            priorChar = char
            i += 1

        # close dangling problems
        if closeBold:
            rtnLine += "</b>"
        if closeItalic:
            rtnLine += "</i>"
        if closeStrike:
            rtnLine += "</strike>"
        return rtnLine

    def markdownProcessLine(self, line):
        """
        # Title
        ## Heading1
        ### Heading2
        #### Heading3
        -list unordered list
        1. list ordered list
        **bold**
        *italic*
        ~~strikethrough~~
        -[] task list uncompleted
        -[x] task list completed
        -- horizontal rule
        .command  process a command not like markdown
        """
        #mmmm
        stripped = line.strip()
        if len(stripped) > 0:
            match stripped[0]:
                case '.':
                    self.processCommand(stripped)
                case '#':
                    match stripped.count('#'):
                        case 1:
                            self.addContent(Paragraph(stripped[1:], self.styles["Title"]))
                        case 2:
                            self.addContent(Paragraph(stripped[2:], self.styles["Heading1"]))
                        case 3:
                            self.addContent(Paragraph(stripped[3:], self.styles["Heading2"]))
                        case _:
                            self.addContent(Paragraph(stripped[4:], self.styles["Heading3"]))
                case _:
                    self.addContent(Paragraph(self.markdownAttributes(stripped), self.styles["Normal"]))
            


    def processFile(self, fname):
        # this is separate to recursively process files
        with open (fname, 'r') as file:
            for line in file:
                if self.parser == 'normal':
                    if line[0] == '.':
                        self.processCommand(line)
                    else:
                        self.processText(line)
                else: # markdown parser
                    self.markdownProcessLine(line)
        #self.addContent(self.aList())


class FourPage(Booklet):
    def __init__(self,nameOut="output.pdf", docSize=letter, marginSize=0.3*inch, showFrames=False, drawFolds=True):
        super().__init__(nameOut, docSize, marginSize, showFrames, drawFolds)
        self.frameList = self.defineFrames(self.docSize, self.margin)
        self.frameRotate = self.defineRotate()
        self.currentFrame = self.frameList[self.frameN]
        if self.showFrames: self.currentFrame.drawBoundary(self.canvas)
        if self.drawFolds: self.drawFoldlines(self.canvas)
        self.initStyles(baseFontSize=10)
        self.currentStyle = self.styles["Normal"]

    def defineFrames(self, docSize, margin):
        docWidth, docHeight = docSize
        frameWidth = (docWidth - 4*margin) / 2
        frameHeight = (docHeight - 4*margin) / 2
        return [
            Frame(x1=(frameWidth+3*margin),y1=margin, width=frameWidth, height=frameHeight), #lr
            Frame(x1=margin,y1=margin,width=frameWidth, height=frameHeight), #ul
            Frame(x1=(frameWidth+3*margin),y1=margin,width=frameWidth, height=frameHeight), #ur
            Frame(x1=margin,y1=margin,width=frameWidth, height=frameHeight), #ll
        ]

    def defineRotate(self):
        return [False, True, False, True]

    def drawFoldlines(self, canvas):
        canvas.saveState()
        canvas.setDash(1,5) # on off
        canvas.line(0, self.docSize[1]/2, self.docSize[0], self.docSize[1]/2)
        canvas.line(self.docSize[0]/2, 0, self.docSize[0]/2, self.docSize[1])
        canvas.restoreState()

class EightPage(Booklet):
    def __init__(self,nameOut="output.pdf", docSize=letter, marginSize=0.1*inch, showFrames=False, drawFolds=True):
        super().__init__(nameOut, landscape(docSize), marginSize, showFrames, drawFolds)
        self.frameList = self.defineFrames(self.docSize, self.margin)
        self.frameRotate = self.defineRotate()
        self.currentFrame = self.frameList[self.frameN]
        if self.showFrames: self.currentFrame.drawBoundary(self.canvas)
        if self.drawFolds: self.drawFoldlines(self.canvas)
        self.initStyles(baseFontSize=8)
        #self.styles["Normal"] = self.buildParagraphStyle(name='Normal',fontSize=8)
        self.currentStyle = self.styles["Normal"]
    
    def defineFrames(self, docSize, margin):
        # 6 5 4 3 upside down
        # 7 0 1 2
        docWidth, docHeight = docSize
        fWidth = docWidth / 4
        fHeight = docHeight / 2

        f0 = self.defineFrame(0*fWidth, 0*fHeight, fWidth, fHeight, margin)
        f1 = self.defineFrame(1*fWidth, 0*fHeight, fWidth, fHeight, margin)
        f2 = self.defineFrame(2*fWidth, 0*fHeight, fWidth, fHeight, margin)
        f3 = self.defineFrame(3*fWidth, 0*fHeight, fWidth, fHeight, margin)
        # top half (upside down)
        f4 = self.defineFrame(0*fWidth, 0*fHeight, fWidth, fHeight, margin)
        f5 = self.defineFrame(1*fWidth, 0*fHeight, fWidth, fHeight, margin)
        f6 = self.defineFrame(2*fWidth, 0*fHeight, fWidth, fHeight, margin)
        f7 = self.defineFrame(3*fWidth, 0*fHeight, fWidth, fHeight, margin)

        return [f1, f2, f3, f4, f5, f6, f7, f0]

    def defineFrame(self, x,y, w,h, m):
        return Frame(x+m, y+m, w-m-m, h-m-m)

    def defineRotate(self):
        return [False, False, False, True, False, False, False, True]

    def drawFoldlines(self, canvas):
        canvas.saveState()
        canvas.setDash(1,5) # on off
        canvas.line(0, self.docSize[1]/2, self.docSize[0], self.docSize[1]/2)
        self.canvas.setStrokeColor('red')
        for x in [2.75, 5.5, 8.25]: #TODO adjust to doc size
            self.canvas.line(x*inch, 0*inch, x*inch, 8.5*inch)
        canvas.restoreState()

# =====================================================================================

if __name__ == "__main__":
    import argparse

    # get the input and output files
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="Input filename")
    parser.add_argument("outfile", help="Output pdf filename")
    args = parser.parse_args()
    outFilename = args.outfile
    if outFilename[-4:] != ".pdf": outFilename += ".pdf"
    """

    inFilename = "input.txt"
    inFilename = "input.md"
    """
    doc = FourPage(nameOut="out4.pdf", 
                       docSize=letter,
                       showFrames=False, 
                       marginSize=0.20*inch,
                       drawFolds=True)
                          
    doc.processFile(inFilename)
    doc.build()
    """

    doc = EightPage(nameOut="out8.pdf", 
                       docSize=letter,
                       showFrames=True, 
                       marginSize=0.10*inch,
                       drawFolds=True)
                          
    doc.processFile(inFilename)
    doc.build()
