# pocket.py
# Page View is
# 7 6 5 4 (upside down)
# 8 1 2 3

"""
Printout is 
7 6 5 4 upside down
8 1 2 3

measurement
4.25 vertical
horizontal 0 2.75 5.5 8.25 11
"""

from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Frame, FrameBreak, PageBreak, Spacer
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
#from reportlab.lib.colors import yellow, green, blue, red, black
#from reportlab.lib.styles import ParagraphStyle
#from reportlab.lib.enums import TA_CENTER


class EightUp:
    """The render engine for the 8up pocket book maker"""
    def __init__(self):
        self.frames = None
        self.currentFrame = None
        self.frameN = 1

    def InitFrames(self):
        f0 = self.defineFrame(0*2.75, 0*4.25, 2.75, 4.25, 0.1*inch)
        f1 = self.defineFrame(1*2.75, 0*4.25, 2.75, 4.25, 0.1*inch)
        f2 = self.defineFrame(2*2.75, 0*4.25, 2.75, 4.25, 0.1*inch)
        f3 = self.defineFrame(3*2.75, 0*4.25, 2.75, 4.25, 0.1*inch)
        # top half (upside down)
        f4 = self.defineFrame(0*2.75, 0*4.25, 2.75, 4.25, 0.1*inch)
        f5 = self.defineFrame(1*2.75, 0*4.25, 2.75, 4.25, 0.1*inch)
        f6 = self.defineFrame(2*2.75, 0*4.25, 2.75, 4.25, 0.1*inch)
        f7 = self.defineFrame(3*2.75, 0*4.25, 2.75, 4.25, 0.1*inch)

        return [f0, f1, f2, f3, f4, f5, f6, f7]

    def defineFrame(self, x,y, w,h, m):
        return Frame(x*inch+m, y*inch+m, w*inch-m-m, h*inch-m-m, showBoundary=1)

    def DrawGuidelines(self):
        # TODO Change to fold lines and cut line with cfg patterns
        self.canvas.saveState()
        self.canvas.setStrokeColor(Cfg.get("guidecolor"))
        self.canvas.setDash(1,5) # on off
        self.canvas.line(0*inch, 4.25*inch, 11*inch,  4.25*inch) # horiz
        for x in [2.75, 5.5, 8.25]:
            self.canvas.line(x*inch, 0*inch, x*inch, 8.5*inch)
        self.canvas.restoreState()

    def Rotate(self):
        self.canvas.translate(letter[1]/2, letter[0]/2)
        self.canvas.rotate(180)
        self.canvas.translate(-letter[1]/2, -letter[0]/2)

    def DocClose(self):
        self.canvas.setAuthor(Cfg.get("author"))
        self.canvas.setTitle(Cfg.get("title"))
        self.canvas.setSubject(Cfg.get("subject"))
        self.canvas.setKeywords(Cfg.get("keywords"))
        self.canvas.save()

    def InitPage(self):
        if Cfg.get("guidelines"): self.DrawGuidelines()
        self.frames = self.InitFrames()
        self.frameN = 1 # frame number start at 1
        self.currentFrame = self.frames[self.frameN]
        if Cfg.get("drawBoundary"): self.currentFrame.drawBoundary(self.canvas)

    #===================================================================
    def OldGenerate(self, filename, content):
        canvasWidth, canvasHeight = letter
        self.canvas = Canvas(filename, pagesize=(canvasHeight, canvasWidth))

        self.InitPage()
        # begin line processing
        for para in content:
            # process the resulting text
            if self.currentFrame.add(para, self.canvas) == 0: # won't handle a giant paragraph
                self.frameN += 1
                if self.frameN < len(self.frames):
                    self.currentFrame = self.frames[self.frameN]
                if self.frameN == 4 or self.frameN == 8: self.Rotate()
                if self.frameN==8:
                    self.currentFrame = self.frames[0]
                if self.frameN==9:
                    self.canvas.showPage()
                    # Init Block
                    self.InitPage()
                self.currentFrame.add(para, self.canvas) # print the popped content
                if Cfg.get("drawBoundary"): self.currentFrame.drawBoundary(self.canvas)
        self.DocClose()

    def Generate(self, filename, bodyContent, titleContent=None):
        canvasWidth, canvasHeight = letter
        self.canvas = Canvas(filename, pagesize=(canvasHeight, canvasWidth))

        self.InitPage()

        # Process the title if it exists
        if titleContent:
            # compute height of title page
            htTitle = 0
            widthFrame = 2.75*inch
            for para in titleContent:
                pw, ph = para.wrap(widthFrame, 4.25*inch)
                htTitle += ph 
            yOff = (4.25*inch - htTitle)/2

            # modify first frame for the title
            self.frames[1] = Frame((2.75*inch)+10, 10, (2.75*inch)-10-10, 4.25*inch, topPadding=yOff)
            # set to new frame
            self.currentFrame = self.frames[1]

            # combine all the content to go through the generator
            content = titleContent
            content.extend([PageBreak()])
            content.extend(bodyContent)
        else:
            # no title page, content is the body content
            content = bodyContent

        if Cfg.get("drawBoundary"): self.currentFrame.drawBoundary(self.canvas)

        # begin line processing
        for para in content:
            # process the resulting text
            if self.currentFrame.add(para, self.canvas) == 0: # won't handle a giant paragraph
                self.frameN += 1
                if self.frameN < len(self.frames):
                    self.currentFrame = self.frames[self.frameN]
                if self.frameN == 4 or self.frameN == 8: self.Rotate()
                if self.frameN==8:
                    self.currentFrame = self.frames[0]
                if self.frameN==9:
                    self.canvas.showPage()
                    # Init Block
                    self.InitPage()
                self.currentFrame.add(para, self.canvas) # print the popped content
                if Cfg.get("drawBoundary"): self.currentFrame.drawBoundary(self.canvas)
        self.DocClose()


#######################################################################

if __name__ == "__main__":
    from cfgpocket import Cfg
    #from testpocket import *
    from proff import Pocketroff
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="Input filename")
    parser.add_argument("outfile", help="Output pdf filename")
    args = parser.parse_args()
    #print(args.infile)
    #print(args.outfile[-4:])
    outFilename = args.outfile
    if outFilename[-4:] != ".pdf": outFilename += ".pdf"

    pocketGen = EightUp()

    #with open("input.txt", "r") as file:
    with open(args.infile, "r") as file:
        text = file.readlines()

    #convert input text to content
    content, titlePage = Pocketroff().process(text)

    # Make the document
    pocketGen.Generate(outFilename, content, titlePage)
