#  Andrea Nicole G Privado
#  2019-03716 (X-1L)
#  Naïve Bayes and Laplace Smoothing

#!/usr/bin/env python
import os
import re
import pathlib
from decimal import Decimal
import pygame
import pygame_gui
from pygame_gui.windows.ui_file_dialog import UIFileDialog
from pygame_gui.elements.ui_button import UIButton
from pygame.rect import Rect

pygame.init()

window_surface = pygame.display.set_mode((900, 600))
pygame.display.set_caption('Filter Messages')

background = pygame.Surface((900, 600))
background.fill(pygame.Color('#cfd8dc'))

manager = pygame_gui.UIManager((900, 600))
clock = pygame.time.Clock()

# Buttons
spamfolder_selection_button = UIButton(relative_rect=Rect(60, 30, 200, 40),
                                 manager=manager, text='Select Spam Folder')
spamfolder_selection_button.normal_bg ='#ffffff'
hamfolder_selection_button = UIButton(relative_rect=Rect(330, 30, 200, 40),
                                 manager=manager, text='Select Ham Folder')
classify_selection_button = UIButton(relative_rect=Rect(610, 130, 230, 40),
                                 manager=manager, text='Select Classify Folder')
filter_button = UIButton(relative_rect=Rect(710, 190, 110, 35),
    manager=manager, text='Filter')

# Fonts used
text_font = pygame.font.SysFont('montserrat',15)
text_font_normal = pygame.font.SysFont('montserrat',14)
text_font_small = pygame.font.SysFont('montserrat',12)
# Texts 
text_dsize = text_font.render('Dictionary Size:',True, '#0c0c0c')
text_word = text_font.render('Word',True, '#0c0c0c')
text_freq = text_font.render('Frequency',True, '#0c0c0c')
text_tw = text_font.render('Total Words:',True, '#0c0c0c')
text_twspam = text_font.render('Total Words in Spam:',True, '#0c0c0c')
text_twham = text_font.render('Total Words in Ham:',True, '#0c0c0c')
text_k = text_font.render('k',True, '#0c0c0c')
text_output = text_font.render('Output',True, '#0c0c0c')
text_filename = text_font.render('Filename',True, '#0c0c0c')
text_class = text_font.render('Class',True, '#0c0c0c')
text_pspam = text_font.render('P(Spam)',True, '#0c0c0c')
text_spam_notdir = text_font.render('',True, '#800000')
text_ham_notdir = text_font.render('',True, '#800000')
text_classify_notdir = text_font.render('',True, '#800000')
text_filter_error = text_font.render('',True, '#800000')

## Variable Initializations
alpha = re.compile("^([a-z0-9])$")
selected_dirpath=""
classify_dirpath=""


# Getting k value
input_rect = pygame.Rect(650,193, 50, 30)   # k value textbox
user_text = ''
active = False
k = 0

# Necesary List and Dictionaries
spam_dict = {}      # k = word ; v = frequency
ham_dict = {}       # k = word ; v = frequency
output_dict = {}    # k = filename ; v = p(spam)
filenames = []      # list of filenames (from classify folder)
class_list = []
p_spam_list = []

# Message/Word/Dictionary Count
total_spam_msg = 0  
total_ham_msg = 0
total_msg = 0       # total_spam_msg + total_ham_msg = 0
total_spam_words = 0
total_ham_words = 0
total_words = 0     # total_spam_words + total_ham_words = 0
dict_size = 0       # total number of unique words that are both in ham and spam

# Output
total_classify_msg = 0

# Scroll Bar Elements
y_spam_items = []
y_ham_items = []
y_output_items = []

spam_scrollStart = False
ham_scrollStart = False
output_scrollStart = False

spam_scroll = pygame.Rect(280, 100, 8, 410)
ham_scroll = pygame.Rect(550, 100, 8, 410)
output_scroll = pygame.Rect(865, 310, 8, 236)

# Function for tokenizing and cleaning the words in a message - returns a list of cleaned words
def tokenize_clean(file1):
    strList = []
    current_file = open(file1, encoding='latin1')
    strList = strList + current_file.read().split()     # tokenize
    for i in range(len(strList)):
        strList[i] = strList[i].lower() 
        for char in strList[i]:
            if not alpha.match(char):
                strList[i] = strList[i].replace(char,"")     # cleaning
    current_file.close()
    try:                       # removing all instances of '' from the list : https://www.techiedelight.com/remove-all-occurrences-item-list-python/
        while True:
            strList.remove('')
    except ValueError:
        pass
    return strList


# Function for Bag of Words - returns a dictionary (k = word; v = frequency)
def bagOfWords(dirpath,dirclass):
    wordList = []
    msg_counter = 0
    global total_spam_words
    global total_ham_words
    global total_spam_msg
    global total_ham_msg
    for path in pathlib.Path(dirpath).iterdir():        # iterate through all the files in the dir
        if path.is_file():
            msg_counter += 1
            tokenize_clean(path)
            wordList = wordList + tokenize_clean(path)
             
    if dirclass == "S":
        total_spam_words = len(wordList)
        total_spam_msg = msg_counter
    else:
        total_ham_words = len(wordList)
        total_ham_msg = msg_counter

    strDict = {}                                            # dictionary of words
    sortedDict = {}
    for string in wordList:
        if not string in strDict:
            strDict[string] = 1                             # add new item to dict
        else:
            strDict.update({string:strDict[string]+1})      # increment the value of existing item in dict

    sortedKeys= sorted(strDict.keys())                      # sort keys alphabetically
    for key in sortedKeys:
        sortedDict[key] = strDict[key]                      # sorted dictionary

    return sortedDict

# Function for computing counts and sizes
def compute_size():
    global text_tw
    global text_dsize
    global dict_size
    total_words = total_spam_words + total_ham_words
    text_tw = text_font.render('Total Words: ' + str(total_words),True, '#0c0c0c')
    unique_words = list(spam_dict.keys())
    for word in ham_dict.keys():
        if not word in unique_words:
            unique_words.append(word)
    dict_size = len(unique_words)
    text_dsize = text_font.render('Dictionary Size: ' + str(dict_size),True, '#0c0c0c')
    

# Function for classifying classify folder
def classify(dirpath):
    global total_classify_msg
    global filenames
    global class_list
    global p_spam_list
    filenames = []
    class_list = []
    p_spam_list = []
    msg_counter = 0
    for path in pathlib.Path(dirpath).iterdir():        # iterate through all the files in the dir
        if path.is_file():
            msg_counter += 1
            base_name = os.path.basename(path)
            file_name = base_name.split(".")[0]
            filenames.append(file_name)
    total_classify_msg = msg_counter

# Function for counting new words in a message - returns the count fo new words (int)
def countNewWords(wList):
    new_word_count = 0
    ham_keys = list(ham_dict.keys())
    spam_keys = list(spam_dict.keys())
    classify_keys = []
    for word in wList:
        if not word in classify_keys:
            classify_keys.append(word)
    for word in classify_keys:
        if not word in ham_keys and not word in spam_keys:
            new_word_count += 1
    return new_word_count

def PwSpam(word,new_words):
    global spam_dict
    global k
    global total_spam_words
    global dict_size
  
    if word in spam_dict:
        w_count_spam = spam_dict[word]
    else:
        w_count_spam = 0
    pw_spam = (w_count_spam + k)/ ( total_spam_words + (k * (dict_size + new_words)))
    return Decimal(pw_spam)

def PwHam(word,new_words):
    global ham_dict
    global k
    global total_ham_words
    global dict_size
    
    if word in ham_dict:
        w_count_ham = ham_dict[word]
    else:
        w_count_ham = 0
    pw_ham = (w_count_ham + k)/ ( total_ham_words + (k * (dict_size + new_words)))
    return Decimal(pw_ham)

def PmessSpam(wList):
    new_words = countNewWords(wList)
    p_message_spam = 1
    for word in wList:
        p_message_spam = Decimal(p_message_spam) * PwSpam(word,new_words)
    return Decimal(p_message_spam)

def PmessHam(wList):
    new_words = countNewWords(wList) 
    p_message_ham = 1
    for word in wList:
        p_message_ham = Decimal(p_message_ham) * PwHam(word,new_words)
    return Decimal(p_message_ham)

def PtotalSpam(wordList):
    global p_spam 
    p_message_spam = PmessSpam(wordList)
    ptotalspam =(p_message_spam * p_spam)
    return ptotalspam

def PtotalHam(wordList):
    p_message_ham = PmessHam(wordList)
    ptotalham = (p_message_ham * p_ham)
    return ptotalham

# Function for filtering messages in classify folder
def filter(dirpath):
    global k
    global user_text
    global dict_size
    global p_ham
    global p_spam
    global p_spam_list
    global class_list
    k = int(user_text)
    p_ham = Decimal((total_ham_msg + k) / ((total_spam_msg + total_ham_msg) + (2*k)))
    p_spam = Decimal((total_spam_msg + k)/ ((total_spam_msg + total_ham_msg) + (2*k)))
    p_spam_list = []
    class_list = []
    for path in pathlib.Path(dirpath).iterdir():
        wordList = []
        if path.is_file():
            wordList = tokenize_clean(path)
            p_spam_message = PtotalSpam(wordList)/Decimal(((PtotalSpam(wordList)+(PtotalHam(wordList)))))
            p_spam_list.append(p_spam_message)

    for value in p_spam_list:
        if value > 0.5:
            class_list.append('SPAM')
        else:
            class_list.append('HAM')
    # Printing
    print()
    print("HAM\n","Dictionary Size: ", len(ham_dict),'\n',"Total Number of Words: ", total_ham_words, '\n' )
    print("SPAM\n","Dictionary Size: ", len(spam_dict),'\n',"Total Number of Words: ", total_spam_words )
    # Writing output to file
    outputfile = open("classify.out","w")
    outputfile.write("")                                # Clearing classify.out

    outputfile = open("classify.out","a")               # Append mode

    for i in range(len(filenames)):                     # Writing the file name, classification, and probability
        if i == 0:
            outputfile.write(filenames[i] + " " + class_list[i] + " " + str(p_spam_list[i]))
        else: 
            outputfile.write("\n" + filenames[i] + " " + class_list[i] + " " + str(p_spam_list[i]))
    outputfile.close()

while 1:
    time_delta = clock.tick(60) / 1000.0
    mousePressed = pygame.mouse.get_pressed()[0]
    mousePos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:       # Clicked exit button
            quit()

        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == spamfolder_selection_button :        # Select Spam Folder
                    selected_dirpath = UIFileDialog(rect=Rect(0, 0, 600, 500), manager=manager, allow_picking_directories=True)
                    dir_forwhat = "S"
                elif event.ui_element == hamfolder_selection_button:        # Select Ham Folder
                    selected_dirpath = UIFileDialog(rect=Rect(0, 0, 600, 500), manager=manager, allow_picking_directories=True)
                    dir_forwhat = "H"
                elif event.ui_element == classify_selection_button:         # Select Classify Folder
                    selected_dirpath = UIFileDialog(rect=Rect(0, 0, 600, 500), manager=manager, allow_picking_directories=True)
                    dir_forwhat = "C"
                elif event.ui_element == filter_button:                     # Filter
                    if len(filenames) != 0:                                 # Check if a classify folder has been selected
                        if len(spam_dict) != 0:                             # Check for spam folder
                            if len(ham_dict) != 0:                          # Check for ham folder
                                try:                                        # Check/try if the user input (k) is a valid int
                                    int(user_text)
                                    text_filter_error = text_font.render('',True, '#800000')
                                    filter(classify_dirpath)
                                except ValueError:
                                    text_filter_error = text_font.render('Enter valid k value',True, '#800000')
                            else:
                                text_filter_error= text_font.render('Select Ham Folder first',True, '#800000')
                        else:
                            text_filter_error= text_font.render('Select Spam Folder first',True, '#800000')
                    else:
                        text_filter_error= text_font.render('Select Classify Folder first',True, '#800000')
                    

                if selected_dirpath != "":                                  # File Selection successful
                    if event.ui_element == selected_dirpath.ok_button:
                        dirpath = str(selected_dirpath.current_file_path)
                        if os.path.isdir(dirpath):                          # Check if the selected path is a directory
                            if dir_forwhat == "S":
                                total_spam_words = 0
                                spam_dict = {}
                                spam_dict = bagOfWords(dirpath,dir_forwhat) # Get bag of words
                                y_spam_items = []
                                if total_spam_words != 0:
                                    # Update GUI
                                    text_twspam = text_font.render('Total Words in Spam: '+ str(total_spam_words),True, '#0c0c0c')
                                    text_spam_notdir = text_font.render('',True, '#800000')
                                else:
                                    # Reset texts in Window
                                    text_twspam = text_font.render('Total Words in Spam: ',True, '#0c0c0c')
                                    text_tw = text_font.render('Total Words: ',True, '#0c0c0c')
                                    text_dsize = text_font.render('Dictionary Size: ',True, '#0c0c0c')
                                if total_spam_words != 0 and total_ham_words != 0:
                                    compute_size()
                                for y in range(len(spam_dict)):     # For scrolling
                                    y_spam_items.append(y * 20 + 135)
                            elif dir_forwhat == "H":
                                total_ham_words = 0
                                ham_dict = {}
                                ham_dict = bagOfWords(dirpath,dir_forwhat)  # Get bag of words
                                y_ham_items = []
                                if total_ham_words != 0:
                                    # Update GUI
                                    text_twham = text_font.render('Total Words in Ham: '+ str(total_ham_words),True, '#0c0c0c')
                                    text_ham_notdir = text_font.render('',True, '#800000')
                                else:
                                    # Reset texts in Window
                                    text_twham = text_font.render('Total Words in Ham: ',True, '#0c0c0c')
                                    text_tw = text_font.render('Total Words: ',True, '#0c0c0c')
                                    text_dsize = text_font.render('Dictionary Size: ',True, '#0c0c0c')
                                if total_spam_words != 0 and total_ham_words != 0:
                                    compute_size()
                                for y in range(len(ham_dict)):      # For scrolling
                                    y_ham_items.append((y * 20) + 135)
                            else:
                                text_spam_notdir = text_font.render('',True, '#800000')
                                classify_dirpath = dirpath
                                classify(dirpath)
                                y_output_items = []
                                for y in range(len(filenames)):     # For scrolling
                                    y_output_items.append((y * 25) + 309)
                                text_classify_notdir = text_font.render('',True, '#800000')
                        else:  # if selected path is not a directory
                            if dir_forwhat == "S":
                                text_spam_notdir = text_font.render('Please select a valid folder.',True, '#800000')
                                spam_dict = {}
                                y_spam_items = []
                                # Reset texts in Window
                                text_twspam = text_font.render('Total Words in Spam: ',True, '#0c0c0c')
                                text_tw = text_font.render('Total Words: ',True, '#0c0c0c')
                                text_dsize = text_font.render('Dictionary Size: ',True, '#0c0c0c')
                            elif dir_forwhat == "H":
                                text_ham_notdir = text_font.render('Please select a valid folder.',True, '#800000')
                                ham_dict = {}
                                y_ham_items = []
                                # Reset texts in Window
                                text_twham = text_font.render('Total Words in Ham: ',True, '#0c0c0c')
                                text_tw = text_font.render('Total Words: ',True, '#0c0c0c')
                                text_dsize = text_font.render('Dictionary Size: ',True, '#0c0c0c')
                            else:
                                text_classify_notdir = text_font.render('Please select a valid folder.',True, '#800000')
                                # Clear lists
                                filenames = []
                                class_list = []
                                p_spam_list = []
                                y_output_items = []
        # User Input Event (getting k value)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if input_rect.collidepoint(event.pos):
                active = True
            else:
                active = False
        if event.type == pygame.KEYDOWN:
            if active == True:
                if event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                else:
                    user_text += event.unicode
        if event.type == pygame.MOUSEMOTION:
            if input_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_IBEAM)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    ## SCROLL EVENTS (c) https://stackoverflow.com/questions/66369695/making-a-scrollbar-but-its-inconsistent
        # Spam Table Scroll Event
        if(len(spam_dict) != 0):
            if mousePressed and spam_scroll.collidepoint(mousePos):
                spam_scrollStart = True
                spam_scrollPosY = mousePos[1]

            if mousePressed and spam_scrollStart:
                spam_scroll.y = max(135, min(545 - spam_scroll.height, mousePos[1]))
                scroll_height = (545 - 135) - spam_scroll.height 
                scroll_rel = (spam_scroll.y - 135) / scroll_height
            
                box_height = (545 - 130)
                list_height = len(spam_dict) * 20
                offset = (list_height - box_height) * scroll_rel
            
                for i in range(len(y_spam_items)):
                    y_spam_items[i] = (i * 20) + 135 - offset
            
            if not mousePressed and spam_scrollStart:
                spam_scrollStart = False 

        # Ham Table Scroll Event 
        if(len(ham_dict) != 0):
            if mousePressed and ham_scroll.collidepoint(mousePos):
                ham_scrollStart = True
                ham_scrollPosY = mousePos[1]

            if mousePressed and ham_scrollStart:
                ham_scroll.y = max(135, min(545 - ham_scroll.height, mousePos[1]))
                scroll_height = (545 - 135) - ham_scroll.height 
                scroll_rel = (ham_scroll.y - 135) / scroll_height
            
                box_height = (545 - 130)
                list_height = len(ham_dict) * 20
                offset = (list_height - box_height) * scroll_rel
            
                for i in range(len(y_ham_items)):
                    y_ham_items[i] = (i * 20) + 135 - offset
            
            if not mousePressed and ham_scrollStart:
                ham_scrollStart = False

        # Output Table Scroll Event 
        if(len(filenames) != 0):
            if mousePressed and output_scroll.collidepoint(mousePos):
                output_scrollStart = True
                output_scrollPosY = mousePos[1]

            if mousePressed and output_scrollStart:
                output_scroll.y = max(310, min(545 - output_scroll.height, mousePos[1]))
                scroll_height = (545 - 310) - output_scroll.height 
                scroll_rel = (output_scroll.y - 310) / scroll_height
            
                box_height = (545 - 310)
                list_height = len(filenames) * 25
                offset = (list_height - box_height) * scroll_rel
            
                for i in range(len(filenames)):
                    y_output_items[i] = (i * 25) + 310 - offset
            
            if not mousePressed and output_scrollStart:
                output_scrollStart = False

        manager.process_events(event)

## GUI Elements
    window_surface.blit(background, (0, 0))
    
    # SPAM TABLE OF BAG OF WORDS 
        # 1st Column (Word)
    pygame.draw.rect(window_surface, 'white', [40,130, 120, 420], 0)
    pygame.draw.rect(window_surface, 'black', [40,130, 120, 420], 1)
    spam_keys = list(spam_dict.keys())
    for y in range(len(spam_dict)) :
        word = text_font_small.render(spam_keys[y], True, (0, 0, 0))
        window_surface.blit(word, (50, y_spam_items[y])) 
    pygame.draw.rect(window_surface, 'white', [159,130, 120, 420], 0)
    pygame.draw.rect(window_surface, 'black', [159,130, 120, 420], 1)
        # 2nd Column (Frequency)
    spam_values = list(spam_dict.values())
    for y in range(len(spam_dict)) :
        freq = text_font_small.render(str(spam_values[y]), True, (0, 0, 0))
        window_surface.blit(freq, (220, y_spam_items[y])) 
    pygame.draw.rect(window_surface, '#cfd8dc', [40,0,240,130],0)
    pygame.draw.rect(window_surface, '#cfd8dc', [279,0,31,600],0)
    pygame.draw.rect(window_surface, '#cfd8dc', [40,550,240,50],0)
        # Scroll Bar Elements
    spam_scroll.height = (30 if len(y_spam_items) > 0 else 410) 
    if (spam_scroll.y < 135): spam_scroll.y = 135
    if (spam_scroll.y + spam_scroll.height) > 545: spam_scroll.y = 545 - spam_scroll.height
    pygame.draw.rect(window_surface, 'gray', [280, 135, 8,410])
    pygame.draw.rect(window_surface, '#646464', spam_scroll)
    
    # HAM TABLE OF BAG OF WORDS
        # 1st Column (Word)
    pygame.draw.rect(window_surface, 'white', [310,130, 120, 420], 0)
    pygame.draw.rect(window_surface, 'black', [310,130, 120, 420], 1)
    ham_keys = list(ham_dict.keys())
    for y in range(len(ham_dict)) :
        word = text_font_small.render(ham_keys[y], True, (0, 0, 0))
        window_surface.blit(word, (320, y_ham_items[y]))
        # 2nd Column (Frequency)
    pygame.draw.rect(window_surface, 'white', [429,130, 120, 420], 0)
    pygame.draw.rect(window_surface, 'black', [429,130, 120, 420], 1)
    ham_values = list(ham_dict.values())
    for y in range(len(ham_dict)) :
        freq = text_font_small.render(str(ham_values[y]), True, (0, 0, 0))
        window_surface.blit(freq, (481, y_ham_items[y]))
        # Rectangles for hiding excess data of BOW 
    pygame.draw.rect(window_surface, '#cfd8dc', [310,0,240,130],0)
    pygame.draw.rect(window_surface, '#cfd8dc', [549,0,350,600],0)
    pygame.draw.rect(window_surface, '#cfd8dc', [310,550,240,50],0)
        # Scroll Bar Elements
    ham_scroll.height = (30 if len(y_ham_items) > 0 else 410) 
    if (ham_scroll.y < 135): ham_scroll.y = 135
    if (ham_scroll.y + ham_scroll.height) > 545: ham_scroll.y = 545 - ham_scroll.height
    pygame.draw.rect(window_surface, 'gray', [550, 135, 8,410])
    pygame.draw.rect(window_surface, '#646464', ham_scroll)
    
    # BOW Column Titles
    pygame.draw.rect(window_surface, 'black', [40,101, 120, 30], 1)
    pygame.draw.rect(window_surface, 'black', [159,101, 120, 30], 1)
    pygame.draw.rect(window_surface, 'black', [310,101, 120, 30], 1)
    pygame.draw.rect(window_surface, 'black', [429,101, 120, 30], 1)
    window_surface.blit(text_word,(76,106))
    window_surface.blit(text_word,(346,106))
    window_surface.blit(text_freq,(180,106))
    window_surface.blit(text_freq,(450,106))

    # BOW Table Footer
    window_surface.blit(text_twspam,(55,560))
    window_surface.blit(text_twham,(330,560))

    # OUTPUT TABLE
        # 1st Column (Filename)
    pygame.draw.rect(window_surface, 'white', [580,304, 100, 246], 0)
    pygame.draw.rect(window_surface, 'black', [580,304, 100, 246], 1)
    for x in range(len(filenames)) :
        name = text_font_normal.render(filenames[x], True, (0, 0, 0))
        window_surface.blit(name, (612, y_output_items[x]))
        # 2nd Column (Class)
    pygame.draw.rect(window_surface, 'white', [679,304, 85, 246], 0)
    pygame.draw.rect(window_surface, 'black', [679,304, 85, 246], 1)
    if len(class_list) == len(filenames):
        for y in range(len(class_list)) :
            classification = text_font_normal.render(class_list[y], True, (0, 0, 0))
            window_surface.blit(classification, (700, y_output_items[y]))
        # 3rd Column (P(Spam))
    pygame.draw.rect(window_surface, 'white', [763,304, 100, 246], 0)
    pygame.draw.rect(window_surface, 'black', [763,304, 100, 246], 1)
    if len(p_spam_list) == len(filenames):
        for z in range(len(p_spam_list)) :
            p_spam_value = text_font_normal.render(str("{:.6f}".format(p_spam_list[z])), True, (0, 0, 0))
            window_surface.blit(p_spam_value, (780, y_output_items[z]))
    pygame.draw.rect(window_surface, '#cfd8dc', [580,550,300,50],0)
    pygame.draw.rect(window_surface, '#cfd8dc', [580,0,300,305],0)
         # Scroll Bar Elements
    output_scroll.height = (30 if len(y_output_items) > 0 else 236) 
    if (output_scroll.y < 310): output_scroll.y = 310
    if (output_scroll.y + output_scroll.height) > 545: output_scroll.y = 545 - output_scroll.height
    pygame.draw.rect(window_surface, 'gray', [865, 310, 8, 236])
    pygame.draw.rect(window_surface, '#646464', output_scroll)
         # Column Titles
    window_surface.blit(text_output,(580,250))  # Title
    pygame.draw.rect(window_surface, 'black', [580,280, 100, 25], 1)
    pygame.draw.rect(window_surface, 'black', [679,280, 85, 25], 1)
    pygame.draw.rect(window_surface, 'black', [763,280, 100, 25], 1)
    window_surface.blit(text_filename,(594,284))    # Filename
    window_surface.blit(text_class,(701,284))       # Class
    window_surface.blit(text_pspam,(780,284))       # P(Spam)

    # Display of Error Message (Chosen path is not a directory)
    window_surface.blit(text_spam_notdir,(60,70))
    window_surface.blit(text_ham_notdir,(330,70))
    window_surface.blit(text_classify_notdir,(627,167))
    
    # Upper Right Texts
    window_surface.blit(text_dsize,(550,40))    # Dictionary size
    window_surface.blit(text_tw,(730,40))       # Total words

    # Getting user input k-value
    window_surface.blit(text_k,(630,200))
    pygame.draw.rect(window_surface, 'white', input_rect, 0)
    pygame.draw.rect(window_surface, 'black', input_rect, 1)
    text_input = text_font.render(user_text,True, '#0c0c0c')
    window_surface.blit(text_input,(input_rect.x+21,input_rect.y+6))
        # Value entered is not an integer
    window_surface.blit(text_filter_error,(630,223))

    # Display update
    manager.update(time_delta)
    manager.draw_ui(window_surface)
    pygame.display.update()