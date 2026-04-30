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

COMMANDS
.font <font params> adjust the current font
.newpage    force a framebreak (page because pocket docs)
.spacer     add a spacer of current font size
.file       Read in a file and process it, ignore config in the file 

CONFIG
.layout #   Layout is 1,2,4,8 page
.frames     Show frames
.fold       Show folds 
.margin #   Size of margins
.separator  Separator/spacer after every paragraph
.cleaner    Remove fractions and degree symbol    
.scrubber   Shortens some recipe words

FONT PARAMETERS
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

TODO
- Check on redefining frames given this prototype:
    Frame(x1, y1, width,height, leftPadding=6, bottomPadding=6, rightPadding=6, topPadding=6, id=None, showBoundary=0)
- 2 page layout needs to swap frames page by page

"""

import argparse
import os
from reportlab.lib.pagesizes import A4, landscape, letter, portrait
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
import reportlab.lib.enums 
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Frame, Spacer, Paragraph, PageBreak

class Booklet: 
    """ The render engine for the pocket book maker
        Proper add the rotation which has to be done manually
    """
    def __init__(self,nameOut="output.pdf", docSize=letter, marginSize=0.2*inch, showFrames=True, drawFolds=True, separator=False):
        self.docSize = docSize
        self.margin = marginSize # how big is the margin for each frame
        self.showFrames = showFrames # show the frame borders
        self.drawFolds = drawFolds # draw the fold lines or not
        self.frameN = 0 # control variable
        self.canvas = None
        self.layout = None
        self.nameOut = nameOut
        self.fontSize = None
        self.separator = separator # put a spacer after every paragraph
        self.author = None # Metadata
        self.titlepage = False # whether to put a title page in front of the booklet
        self.title = None # Metadata
        self.subject = None # Metadata
        self.keywords = None # Metadata
        self.cleaner = False # run the text through the cleaner
        self.scrubber = False # run the text through the scrubber
    
    def create(self):
        #print("Creating canvas and defining frames...")
        if self.layout == None: self.layout = 8
        if self.layout == 8 or self.layout == 2: self.docSize = landscape(self.docSize) # other functions dependent upon layout
        if self.fontSize == None:
            if self.layout == 1: self.fontSize = 12
            elif self.layout == 2: self.fontSize = 11
            elif self.layout == 4: self.fontSize = 10
            elif self.layout == 8: self.fontSize = 8
        self.frames, self.frameRotate = self.defineFrames()
        self.currentStyle = self.buildParagraphStyle(fontSize=self.fontSize, spaceAfter= 0)
        #print("style defined. Creating canvas...")
        self.canvas = Canvas(self.nameOut, pagesize=self.docSize)
        #print("canvas created.")
        self.frameN = 0
        self.currentFrame = self.frames[self.frameN]
        if self.showFrames: self.currentFrame.drawBoundary(self.canvas)
        if self.drawFolds: self.drawFoldlines() #self.canvas)

    def defineFrames(self):
        # Define frames for the 4-page layout
        width, height = self.docSize
        if self.layout == 1:
            frames = [Frame(self.margin, self.margin, width - 2*self.margin, height - 2*self.margin, id='frame1')]
            rotate = [False]
        elif self.layout == 2:
            #frames = [ #margins are probably off slightly
            #    Frame(self.margin, self.margin, (width-2*self.margin) / 2, height - 2*self.margin, id='frame1'),  # Page 1
            #    Frame(self.margin + (width-2*self.margin) / 2, self.margin, (width-2*self.margin) / 2, height - 2*self.margin, id='frame2')   # Page 2
            #]
            frames = [
                Frame(self.margin + (width/2), self.margin, (width-4*self.margin) / 2, height - 2*self.margin, id='frame2'),   # Page 2
                Frame(self.margin, self.margin, (width-4*self.margin) / 2, height - 2*self.margin, id='frame1')  # Page 1
            ]
            rotate = [False, False]
        elif self.layout == 4:  
            #  3  2
            #  4  1
            fw = width/2 - self.margin*2
            fh = height/2 - self.margin*2
            """
            frames = [
                Frame (fw + self.margin, fh + self.margin, fw, fh, id = 'frame1'),   # Page 1
                Frame (fw + self.margin, self.margin, fw, fh, id = 'frame2'),  # Page 2
                Frame (self.margin, self.margin, fw, fh, id = 'frame3'),  # Page 3
                Frame (self.margin, fh + self.margin, fw, fh, id = 'frame4')  # Page 4
            ]
            #rotate =  [False, True, False, True]
            """
            frames = [
                Frame (3*self.margin+fw, self.margin, fw, fh, id = 'frame1'),  # Page 1
                Frame (self.margin, self.margin, fw, fh, id = 'frame2'),  # Page 2
                Frame (3*self.margin+fw, self.margin, fw, fh, id = 'frame3'),  # Page 3
                Frame (self.margin, self.margin, fw, fh, id = 'frame4')  # Page 4
            ]
            rotate =  [False, True, False, True]
        elif self.layout == 8:
            #print("Defining frames for 8-page layout...")
            def defineFrame(x,y, w,h, m):
                return Frame(x+m, y+m, w-m-m, h-m-m)
            # 6 5 4 3 upside down
            # 7 0 1 2
            fWidth = width / 4
            fHeight = height / 2

            f0 = defineFrame(0*fWidth, 0*fHeight, fWidth, fHeight, self.margin)
            f1 = defineFrame(1*fWidth, 0*fHeight, fWidth, fHeight, self.margin)
            f2 = defineFrame(2*fWidth, 0*fHeight, fWidth, fHeight, self.margin)
            f3 = defineFrame(3*fWidth, 0*fHeight, fWidth, fHeight, self.margin)
            # top half (upside down)
            f4 = defineFrame(0*fWidth, 0*fHeight, fWidth, fHeight, self.margin)
            f5 = defineFrame(1*fWidth, 0*fHeight, fWidth, fHeight, self.margin)
            f6 = defineFrame(2*fWidth, 0*fHeight, fWidth, fHeight, self.margin)
            f7 = defineFrame(3*fWidth, 0*fHeight, fWidth, fHeight, self.margin)

            frames = [f1, f2, f3, f4, f5, f6, f7, f0]
            rotate = [False, False, False, True, False, False, False, True]
        else:
            raise ValueError("Invalid layout value. Supported values are 1, 2, 4, or 8.")

        return frames, rotate

    def buildParagraphStyle(self, name='CurrentStyle',
            textColor=colors.black,
            backColor=colors.white,
            alignment=reportlab.lib.enums.TA_LEFT,
            align=None,
            firstLineIndent=0,
            leftIndent=0,
            bulletIndent=0,
            fontName='Times', #'Helvetica',
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

    def drawFoldlines(self):
        self.canvas.saveState()
        self.canvas.setDash(1,5) # on off

        if self.layout == 2:
            self.canvas.setStrokeColor('red')
            self.canvas.line(self.docSize[0]/2, 0, self.docSize[0]/2, self.docSize[1])
        elif self.layout == 4:
            self.canvas.line(0, self.docSize[1]/2, self.docSize[0], self.docSize[1]/2)
            self.canvas.line(self.docSize[0]/2, 0, self.docSize[0]/2, self.docSize[1])
        elif self.layout == 8:
            self.canvas.line(0, self.docSize[1]/2, self.docSize[0], self.docSize[1]/2)
            self.canvas.setStrokeColor('red')
            for x in [2.75, 5.5, 8.25]: #TODO adjust to doc size
                self.canvas.line(x*inch, 0*inch, x*inch, 8.5*inch)

        self.canvas.restoreState()

    def RotatePage(self):
        self.canvas.translate(self.docSize[0]/2, self.docSize[1]/2)
        self.canvas.rotate(180)
        self.canvas.translate(-self.docSize[0]/2, -self.docSize[1]/2)

    def processFile(self, inputFilename):
        # Process the input file content and generate the output PDF.
        #print(f"Processing input file '{inputFilename}'...")
        try:
            with open(inputFilename, 'r', encoding='latin-1') as f:
                #print (f"Input file '{inputFilename}' opened successfully. Reading content...")
                for line in f:
                    line = line.strip()
                    if self.canvas is None:
                         # Process configuration commands in the header before creating the canvas
                         self.processHeaderLine(line)
                    else:
                        # process content lines and commands
                         self.processContentLine(line)
            #print(f"Input file '{inputFilename}' processed successfully.")
        except FileNotFoundError:
            print(f"Error: Input file '{inputFilename}' not found.")
        except Exception as e:
            print(f"Error: {e}")
    
    def processHeaderLine(self, line):
        #print (f"Processing header line: '{line}'")
        # Process configuration commands in the header before creating the canvas
        if line.startswith('.layout'):
            try:
                self.layout = int(line.split()[1])
            except (IndexError, ValueError):
                print("Invalid layout value. Using default (4).")
        elif line.startswith('.frames') or line.startswith ('.showframes'):
            arg = line.split()[1] if len(line.split()) > 1 else ''
            self.showFrames = arg.lower() not in ['0', 'false']
        elif line.startswith('.fold') or line.startswith('.showfolds'):
            arg = line.split()[1] if len(line.split()) > 1 else ''
            self.drawFolds = arg.lower() not in ['0', 'false']
        elif line.startswith('.separator'):
            arg = line.split()[1] if len(line.split()) > 1 else ''
            self.separator = arg.lower() not in ['0', 'false']
        elif line.startswith('.margin'):
            try:
                self.margin = float(line.split()[1]) * inch
            except (IndexError, ValueError):
                print("Invalid margin value. Using default (0.3 inch).")
        elif line.startswith('.author'):
            self.author = line.split(' ', 1)[1] if len(line.split()) > 1 else None
        elif line.startswith('.titlepage'):
            arg = line.split()[1] if len(line.split()) > 1 else ''
            self.titlepage = arg.lower() not in ['0', 'false']
        elif line.startswith('.title'):
            self.title = line.split(' ', 1)[1] if len(line.split()) > 1 else None
        elif line.startswith('.subject'):
            self.subject = line.split(' ', 1)[1] if len(line.split()) > 1 else None
        elif line.startswith('.keywords'):
            self.keywords = line.split(' ', 1)[1] if len(line.split()) > 1 else None
        elif line.startswith('.cleaner'):
            arg = line.split()[1] if len(line.split()) > 1 else ''
            self.cleaner = arg.lower() not in ['0', 'false']
        elif line.startswith('.scrubber'):
            arg = line.split()[1] if len(line.split()) > 1 else ''
            self.scrubber = arg.lower() not in ['0', 'false']
        else:
            #print("Finished processing header. Creating canvas and frames...")
            # Stop processing header on first non-config line
            self.create()  # Create canvas and frames after processing header
            if self.titlepage:
                self.buildTitlePage()
            self.processContentLine(line)  # Process the first content line
    
    def buildTitlePage(self):
        # Build a simple title page using the metadata
        if self.title == None and self.author == None:
            return # nothing to put on the title page
        title_style = self.buildParagraphStyle(fontSize=self.fontSize*2, alignment=reportlab.lib.enums.TA_CENTER)
        author_style = self.buildParagraphStyle(fontSize=self.fontSize*1.5, alignment=reportlab.lib.enums.TA_CENTER)
        #self.currentFrame.height = 0.75 * self.currentFrame.height # give it more room for the title page
        #self.currentFrame._y1 += 0.25 * self.currentFrame.height # move it down a bit
        #print(f"Current frame is {self.frameN} with dimensions {self.currentFrame._width}x{self.currentFrame._height} at position ({self.currentFrame._x1}, {self.currentFrame._y1})")
        self.canvas.saveState()
        self.canvas.translate(0, -self.currentFrame._height/4) # move to the vertical center of the frame
        if self.title:
            title_para = Paragraph(self.title, title_style)
            self.addObject(title_para)
            self.addObject(Spacer(1, self.currentStyle.fontSize*4))
        if self.author:
            author_para = Paragraph(f"by {self.author}", author_style)
            self.addObject(author_para)
        self.addObject(PageBreak())
        self.canvas.restoreState()

    def processContentLine(self, line):
        # Process content lines and commands after the header has been processed
        if line.startswith('.'):
             self.handleCommand(line)
        else:
             self.handleContent(line)

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
    
    def adjustCurrentStyle(self, modifiers):
        # adust the current style in place
        #print (f"Adjusting current style with modifiers: {modifiers}")
        for mod in modifiers:
            cmd = mod.split("=")
            match cmd[0]:
                case 'textColor' | 'backColor': 
                    setattr(self.currentStyle, cmd[0], eval('colors.'+cmd[1]))
                case 'color':
                    setattr(self.currentStyle, 'textColor', eval('colors.'+cmd[1]))
                case 'alignment' | 'firstLineIndent' | 'fontSize' | 'leading' | 'leftIndent' | 'bulletIndent':
                    setattr(self.currentStyle, cmd[0], int(cmd[1])) 
                case 'size':
                    setattr(self.currentStyle, 'fontSize', int(cmd[1]))
                case 'fontName': 
                    setattr(self.currentStyle, cmd[0], cmd[1])
                case 'name':
                    setattr(self.currentStyle, 'fontName', cmd[1])
                case 'align':
                    setattr(self.currentStyle, 'alignment', self.alignmentStrToEnum(cmd[1].lower()))

    def handleCommand(self, line):
        #print (f"Handling command: '{line}'")
        if line.startswith(".font"): #adjust the current font
            tokens = line.split()
            if len(tokens) > 1:
                self.adjustCurrentStyle(tokens[1:])
        elif line.startswith (".spacer"):
            self.addObject(Spacer(1, self.currentStyle.fontSize))
        elif line.startswith (".newpage") or line.startswith (".np"):
            self.addObject(PageBreak())
        elif line.startswith(".file"):
            tokens = line.split()
            self.processFile(tokens[1])
        else:
            print(f"Unknown command: '{line}'")

    def scrub(self, line):
        """
        Replace all occurrences of strings in the line based on a data structure
        of string pairs. The first string in each pair is replaced with the second.
        Args: line (str): The text line to process
        Returns: str: The scrubbed text with all replacements made
        """
        # Data structure: list of tuples with (original_string, replacement_string)
        # Strings can contain spaces
        replacements = [
            ("teaspoon", "tsp"), ("tablespoon", "Tbl"), ("Tablespoon", "Tbl"), ("tbsp", "Tbl"),
            ("Tbsp", "Tbl"), ("Tbl of ", "Tbl "), ("tsp of ", "tsp "), ("cup", "c"),
            ("c of ", "c "), ("white sugar", "sugar"), ("ounces", "oz"), ("ounce", "oz"),
            ("small", "sm"), ("medium", "med"), ("large", "lg"), ("minute", "min"),
            ("minutes", "min"), ("pound", "lb"), ("cups", "c"), ("Bake for ", "Bake "),
            ("bake for ", "bake "), ("degrees", "deg"), ("Preheat oven to ", "Oven "),
            ("deg F", "F"), ("deg C", "C"), ("Cool for ", "Cool "), 
            # Add more pairs as needed
        ]
        result = line
        for original, replacement in replacements:
            result = result.replace(original, replacement)
    
        return result

    def handleContent(self, line):
        if self.cleaner:
            line = line.replace('½', '1/2').replace('¼', '1/4').replace('¾', '3/4').replace('°', ' deg')
        if self.scrubber:
            line = self.scrub(line)
        obj = Paragraph(line, self.currentStyle)
        self.addObject(obj, self.separator)

    def addObject(self, obj, spacer=False):
        #TODO if obj is continuously too large need to punch out
        #TODO if spacer don't put if we moved to a new column
        if self.currentFrame.add(obj, self.canvas) == 0: # won't handle a giant paragraph
            self.frameN += 1
            if self.frameN >= len(self.frames):
                self.frameN = 0
                self.canvas.showPage()
                #TODO do we need this line?
                self.frames, self.frameRotate = self.defineFrames()
                if self.drawFolds: self.drawFoldlines() #self.canvas)
            self.currentFrame = self.frames[self.frameN]
            
            if self.frameRotate[self.frameN]:
                self.RotatePage()
            if self.showFrames: 
                #print (f"Drawing frame boundary for frame {self.frameN}...")
                self.currentFrame.drawBoundary(self.canvas)
            self.currentFrame.add(obj, self.canvas) #adding the failed content
        elif spacer:
            self.addObject(Spacer(1, self.currentStyle.fontSize))

    def build(self):
        if self.author != None: self.canvas.setAuthor(self.author)
        if self.title != None: self.canvas.setTitle(self.title)
        if self.subject != None: self.canvas.setSubject(self.subject)
        if self.keywords != None: self.canvas.setKeywords(self.keywords)
        self.canvas.save()


##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### 
def parse_arguments():
    """
    Parse command line arguments for input and output files.
    """
    parser = argparse.ArgumentParser(description='Demo program that processes input and output files.')
    parser.add_argument('-i', '--input', default='input.txt', help='Input file name (default: input.txt)')
    parser.add_argument('-o', '--output', help='Output file name (must have .pdf extension)')

    args = parser.parse_args()

    # Determine output file name
    if args.output is None:
        # If output not provided, use input file name with .pdf extension
        base_name = os.path.splitext(args.input)[0]
        outputFilename = base_name + '.pdf'
    else:
        # Ensure output file has .pdf extension
        if not args.output.endswith('.pdf'):
            outputFilename = args.output + '.pdf'
        else:
            outputFilename = args.output

    return args.input, outputFilename

def main():

    """
    Read command line arguments
    """
    inputFilename, outputFilename = parse_arguments()

    print(f"Converting: {inputFilename} to {outputFilename}")

    #print ("Starting booklet generation...")
    booklet = Booklet(nameOut=outputFilename)
    #print (f"Booklet instance created. Processing input file '{inputFilename}'...")
    booklet.processFile(inputFilename)
    booklet.build()

if __name__ == '__main__':
    main()