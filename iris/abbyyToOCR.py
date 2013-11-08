#The module implements all the functions necessary to convert an abbyy ocr file to an hOCR file for use by Gamera.
#You will also observe that the hOCR output tags are separated by newlines, but not indented. This is because calculating indentation
#requires the memory complexity to increase from O(length of longest tag) to O(log(number of xml tags)). Since this hOCR is fed directly to gamera, who cares?

import os
import logging
from lxml import etree as ET
from kitchen.text.converters import to_unicode, to_bytes


HOCR_HEADER_TEMPLATE = '''<html xmlns:abbyy="{}">\n<head>\n<meta name="ocr-id" value="abbyy"/>\n<meta name="ocr-recognized" value="lines text"/>\n</head>\n<body>'''

HOCR_FOOTER_TEMPLATE = '''</body>\n</html>'''

#The first bracket pair is the name, the second is the page number, starting at 0.
FILE_NAME = '''{}_{}.hocr.html'''

# The size of the buffer for writing the output files.
BUFFER_LENGTH = 4096

# A dictionary of characters we want to substitute in the text sections of the HTML output. Any key in this dictionary will be replaced with its value in the output hOCR and log files.
specialChars = {'<' : u'&lt;',
                '>' : u'&gt;'} 


#Form and return an hOCR tag representing a word, given a state dictionary.
def build_word_tag(state):
    return '<span class=\"ocr_word\" title=\"%s %s %s %s\">%s</span>' % (state['b'], state['t'], state['r'], state['l'], ''.join(state['word']))

#Return the xml element's tag as a string, but without the namespace prefix.
def namespaceless_tag(element):
    return element.tag.split('}')[-1]

#A method for the rule dictioanry to default to, in order to avoid catching pointless (and slow) KeyError exceptions on tags we don't transform.
def unknown_xml_tag(element, event, state):
    pass

# Retrieve the namespace from the document tag's attribute and save it.
def set_header(element, event, state):
    if event == 'start':
        state['header'] = HOCR_HEADER_TEMPLATE.format(element.nsmap.get(None))

#Check if we have aggregated enough character data to form an hOCR tag representing a word.
#This occurs when either (a). we hit a non-charParams tag, or (b). we hit a charaParams tag where wordStart="true".
def check_if_word_is_complete(element, event, state, outDir):
    tag = namespaceless_tag(element)

    if state['pending'] and ((tag == 'charParams' and element.get('wordStart') == 'true') or (event == 'end' and tag == 'line')):
        write_to_page(build_word_tag(state), state, outDir)
        reset_state(state)
   

#Parse a charParams abbyy tag and update the state dictionary to reflect the addition to the current word.
#Remeber that dictionaries are mutable, so the changes to it are preserved up the stack as desired.
def parseCharParams(element, event, state):
    if event != 'start':
        return

    u_char = to_unicode(element.text)
    u_char = u_char if u_char != None else u'' # Because element.text returns None, not '' if the xml tag has no text.
    state['word'].append(specialChars.get(u_char, u_char))

    if element.get('wordStart') == 'true':
        state['pending'] = True
        state['l'] = element.get('l')
        state['t'] = element.get('t')
        state['b'] = element.get('b')
        state['r'] = element.get('r')
    else:   
        state['r'] = element.get('r')
        state['b'] = str(max(int(state['b']), int(element.get('b')))) if state['b'] != '' else element.get('b')
        state['t'] = str(max(int(state['t']), int(element.get('t')))) if state['t'] != '' else element.get('t')
    
# We buffer the output to maximize write speed. This method formats(adds line breaks) to the tags, and flushes teh buffer to the output files when necessary.
def write_to_page(tag, state, outDir):
    if len(state['buffer']) + len(tag) >= BUFFER_LENGTH:
        write_to_file(state['buffer'], state, outDir)

    state['buffer'] += tag + '\n'
    if tag == HOCR_FOOTER_TEMPLATE: # Time for a new file!
        write_to_file(state['buffer'], state, outDir) # Write whatever is left in the buffer; we can't buffer accross files!
        state['pageNum'] += 1

#Format an hOCR tag for human readability (add line breaks), and stream the results to our output file.
def write_to_file(tag, state, outDir):
    fileName = FILE_NAME.format(state['fileName'], state['pageNum'])
    state['writingPath'] = os.path.join(outDir, fileName)
    outFile = open(state['writingPath'], 'a', buffering=BUFFER_LENGTH)
    outFile.write(to_bytes(state['buffer']))
    state['buffer'] = ''
    

#Resets a state dictionary to a set of defaults values. We can't use "return {'pending':False, 'word':[]... etc.} because this would update only the local copy of state; we want to mutate the parameter.
def new_state(state):
    reset_state(state)
    state['writingPath'] = ''
    state['pageNum'] = 0
    state['buffer'] = ''
    state['fileName'] = ''

#Defaults all values except the startPage values, which is preserved.
def reset_state(state):
    state['pending'] = False
    state['word'] = []
    state['b'] = ''
    state['l'] = ''
    state['r'] = ''
    state['t'] = ''

# Maps xml abbyy tags to their apporopriate transform functions. Want to transform more tags? Just add a new rule! The lambda shorthand params stand for element, event, and state.
rules = {'line': lambda el, ev, s: '<span class=\"ocr_line\" title=\"bbox %s %s %s %s\">' % (el.get('l'),el.get('t'),el.get('r'),el.get('b')) if ev == 'start' else '</span>',
         'block': lambda el, ev, s: '<span class=\"ocr_carea\">' if ev == 'start' else '</span>',
         'par': lambda el, ev, s: '<p>' if ev == 'start' else '</p>',
         'charParams': parseCharParams,
         'document': set_header,
         'page': lambda el, ev, s: s['header'] if ev == 'start' else HOCR_FOOTER_TEMPLATE}

#Parse the abbyy file one tag at a time, sequentially transforming each tag, stream the results to an output file.
#If need be, we can easily add new parsing rules simply be implementing a new transform function, and adding it to the dictionary above.
#Iterparse's schema kwarg can be used to supply an XML schema, and may be a local path, URL, or a file. If not used the method will attempt to determine the correct schema through the abbyy file's xmlns attribute of the document tag.
#Currently, on-the-fly OCR correction is disabled due to bugs in the lxml library.
#The multipage flag can be used to output each xml 'page' tag as a separate file. Otherwise the output will be a single hOCR file, similar to the abbyy file.
def convert_abbyy_to_ocr(abbyyFile, outDir, outFileName):
    # abbyySchema = ET.XMLSchema(file='./resources/FineReader6-schema-v1.xml') Currently, using the schema= kwarg causes anomalous failure in the form of a stopiteration exception due to lxml bugs.
    # abbyyErrors = [] # A list of all errors resulting from the abbyy xml not conforming to its schema. See the above line.
    state = {}
    new_state(state)
    state['fileName'] = outFileName


    context = ET.iterparse(abbyyFile, events = ('start', 'end'), huge_tree=True, remove_comments=True)
    context = iter(context)
    doneParsing = False

    while(not doneParsing):
        try:
            event, element = context.next()
            tag = namespaceless_tag(element)

            check_if_word_is_complete(element, event, state, outDir)
            transformedTag = rules.get(tag, unknown_xml_tag)(element, event, state)

            if transformedTag:
                write_to_page(transformedTag, state, outDir)

            element.clear()
            doneParsing = namespaceless_tag(element) == 'document' and event == 'end'
        except ET.XMLSyntaxError as e:  # For catching abbyy schema violations. Obviously this does nothing as schema checking is currently disabled.
            # abbyyErrors.append(e)
            continue
        except StopIteration as e:
            print 'caught stop iteration in abbyyToOCR; should not see me. The abbyy XML document may be malformed.'
            raise e

# A simple command line interface. First arg is the input abbyy file second is the output directory. Should NOT be used in Iris; call convert_abbyy_to_ocr() properly.
if __name__ == "__main__":
    import sys

    inFile = open(sys.argv[1], 'r')
    outFileName = sys.argv[3]
    convert_abbyy_to_ocr(inFile, sys.argv[2], outFileName)
    inFile.close()
