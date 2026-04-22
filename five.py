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
        output_file = base_name + '.pdf'
    else:
        # Ensure output file has .pdf extension
        if not args.output.endswith('.pdf'):
            output_file = args.output + '.pdf'
        else:
            output_file = args.output

    return args.input, output_file

def main():
    input_file, output_file = parse_arguments()

    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")

    # Demo: Read from input file and write to output file
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        with open(output_file, 'w') as f:
            f.write(content)
        print("File processed successfully.")
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
import argparse
import os

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
        output_file = base_name + '.pdf'
    else:
        # Ensure output file has .pdf extension
        if not args.output.endswith('.pdf'):
            output_file = args.output + '.pdf'
        else:
            output_file = args.output

    return args.input, output_file

def main():
    input_file, output_file = parse_arguments()

    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")

    # Demo: Read from input file and write to output file
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        with open(output_file, 'w') as f:
            f.write(content)
        print("File processed successfully.")
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
