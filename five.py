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
.spacer   add a spacer of current font size
.file       Read in a file and process it, ignore config in the file 

CONFIG
.layout #   Layout is 1,2,4,8 page
.frames     Show frames
.fold       Show folds 
.margin #   Size of margins

FONT PARAMETERS


PROCESS
- Only one argument, the input file
- Input file can contain the configuration - Only one time config
- If no config, then use defaults (TBD)
- Ater config, then the text to generate
- Can do the commands above only

- Process text has an optional cleaner 
"""

import argparse
import os
from reportlab.lib.pagesizes import A4, landscape, letter, portrait
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
import reportlab.lib.enums 
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Frame, FrameBreak, Spacer, Paragraph

class Booklet: 
    """ The render engine for the pocket book maker
        Proper add the rotation which has to be done manually
    """
    def __init__(self,nameOut="output.pdf", docSize=letter, marginSize=0.3*inch, showFrames=False, drawFolds=True):
        self.docSize = docSize
        self.margin = marginSize # CFG
        self.showFrames = showFrames # CFG
        self.drawFolds = drawFolds # CFG
        self.canvas = Canvas(nameOut, pagesize=self.docSize)
        self.frameN = 0

def testProce(f):
    for line in f:
        print (line.strip())


def processHeader(f):
    """
    .layout #   Layout is 1,2,4,8 page
    .frames     Show frames
    .fold       Show folds 
    .margin #   Size of margins
    """
    # defaults
    layout = 4
    showFrames = False
    drawFolds = False
    margin = 0.3*inch

def processInputFile(inputFilename, outputFilename):
    """
    Process the input file content and generate the output PDF.
    """
    try:
        with open(inputFilename, 'r') as f:
            """
            Process the header
            """
            n = 0
            for line in f:
                print (line.strip())
                n+=1
                if n >= 3:
                    break
            print ("/nEngage second processor/n")
            # create the booklet object

            # Process the body
            testProce(f)
            #content = f.read()
        print("File processed successfully.")
    except FileNotFoundError:
        print(f"Error: Input file '{inputFilename}' not found.")
    except Exception as e:
        print(f"Error: {e}")

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

    print(f"Input file: {inputFilename}")
    print(f"Output file: {outputFilename}")

    processInputFile(inputFilename, outputFilename)

if __name__ == '__main__':
    main()