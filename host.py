from json import JSONDecodeError
from tkinter import *
from tkinter import font
from PIL import Image, ImageTk
from functools import partial
from string import ascii_uppercase
from random import choice
from requests import get
from threading import Thread
from time import sleep, time

root = Tk()
root.title('Hangman: Reactivation')
root.geometry('1500x750+0+0')
root.resizable(False, False)
root.iconbitmap('logo.ico')

BR, DR = '#e5eec5', '#4d4f47' # Bright, Dark
BG, SM = ('Bahnschrift Light', 15, 'normal'), ('Bahnschrift Light', 11, 'normal')
host = 'https://hunched-mittens.000webhostapp.com/'
exit, password, obscured, used, correct, gatherLetters, win = False, '', '', [], [], False, False

def destroy(*args):
    global exit
    exit = True
    if code:
        get(host+f'?code={code}&end')
    root.destroy()

def changeFrame(actFrame, newFrame):
    actFrame.place_forget()
    newFrame.place(relx=0, rely=0, relwidth=1, relheight=1)

def checkTable():
    global code, table, exit
    while True:
        sleep(3)
        if exit:
            return
        try:
            table = get(host+f'{code}.json').json()
        except JSONDecodeError as e:
            continue
        playerString = ''
        del table['sJ58XdfG']
        del table['a2SsdaS34']
        if table != {}:
            for i, name in enumerate(table.keys()):
                playerString += name
                if (i+1)%5: playerString += '    '
                else: playerString += '\n'
            playersLabel.config(text=playerString)
        else:
            playersLabel.config(text='')
            
def endGame(screen):
    global table, code, exit
    table = []
    exit = True
    get(host+f'?code={code}&end')
    code = ''
    changeFrame(screen, startFrame)

def startRoom():
    global code, codeThread, exit, obscured, password, used, correct, table
    exit, table = False, {}
    code = ''.join([choice(ascii_uppercase) for _ in range(6)])
    codeLabel.config(text=f'Kod do gry: {code}')
    get(host+f'?code={code}')
    codeThread = Thread(target=checkTable)
    codeThread.start()
    changeFrame(startFrame, codeFrame)

def endGathering():
    global code, exit
    get(host+f'?code={code}&start')
    exit = True
    passwordEntry.delete(0, END)
    changeFrame(codeFrame, passFrame)   

def commitPass():
    global obscured, password, used, correct, tries, gatherLetters, table, win
    obscured, password, used, correct, tries, gatherLetters, win = '', '', [], [], 12, False, False
    buttonsConfig()
    hangmanLabel.config(image=None)
    hangmanLabel.image=None
    password = passwordEntry.get().upper()
    if password == '': return
    for l in password:
        if l!=' ':
            obscured += '_'
            obscured += ' '
        else: obscured += '  '
    usedLabel.config(text=f'UŻYTE:  '+'  '.join(used))
    obscureLabel.config(text=f'HASŁO:  {obscured}')
    triesLabel.config(text=f'PRÓBY:  {tries}')
    if table != []:
        for i, name in enumerate(table.keys()):
            if table[name] != 0: break
            nameButton = Button(resultsFrame, bd=0, bg=BR, fg=DR, font=("Bahnshrift Light", 11, "bold"), text=name, command=partial(addPoints, name))
            scoreLabel = Label(resultsFrame, bg=BR, fg=DR, font=SM, text="0")
            nameButton.place(relx=0.55*(i%2), relwidth=0.35, rely=0.05*(i//2), relheight=.05)
            scoreLabel.place(relx=0.35+0.55*(i%2), relwidth=0.1, rely=0.05*(i//2), relheight=.05)
            table[name] = scoreLabel

    passwordEntry.delete(0, END)
    changeFrame(passFrame, gameFrame)
    
def gather():
    global gatherLetters, code
    if gatherLetters: return
    get(host+f'?code={code}&startGather={time()}')
    gatherLetters = True 

def stopGather():
    global gatherLetters, code
    if not gatherLetters: return

    get(host+f'?code={code}&stopGather')
    gatherLetters = False

def buttonsConfig(active=True):
    if active:
        startLetters.config(state='normal')
        stopLetters.config(state='normal')
        updateTable.config(text='AKTUALIZUJ WYNIKI', command = getResults)
        return 
    startLetters.config(state='disabled')
    stopLetters.config(state='disabled')
    updateTable.config(text='NOWE HASŁO', command = partial(changeFrame, gameFrame, passFrame))

def getResults():
    global code, password, table, win, correct, used, obscured, tries
    if win: return
    data = get(host+f'{code}-time.json').json()
    del data['a2SsdaS34']
    times, passwords, letters = {}, {}, {}
    for k, v in data.items():
        if v['type'] == "password": passwords[k] = v
        else: letters[k] = v
    
    for nick in passwords.keys():
        times[nick] = data[nick]['time']
    times = {k: v for k, v in sorted(times.items(), key=lambda item: item[1])}
    for nick, time in times.items():
        if passwords[nick]['password'].upper() == password:
            pts = int(table[nick]['text'])
            table[nick].config(text=str(pts+100))
            win = True
            obscureLabel.config(text=f"GRACZ {nick} ODGADŁ HASŁO:  {password}")
            buttonsConfig(active=False)
            return
        pts = int(table[nick]['text'])
        table[nick].config(text=str(pts-20))
    
    times = {}
    for nick in letters.keys():
        times[nick] = data[nick]['time']
    times = {k: v for k, v in sorted(times.items(), key=lambda item: item[1])}
    firstWrong = True
    for nick, time in times.items():
        letter = letters[nick]['letter'].upper()
        if letter in password and letter!=' ' and len(letter)==1 and letter not in correct and letter not in used:
            correct.append(letter)
            obscured = ''
            for l in password:
                if l!=' ' and l not in correct:
                    obscured += '_'
                    obscured += ' '
                elif l in correct:
                    obscured += l
                    obscured += ' '
                else: obscured += '  '
            obscureLabel.config(text=f'HASŁO:  {obscured}')
            if not obscured.count('_'):
                pts = int(table[nick]['text'])
                table[nick].config(text=str(pts+100))
                win = True
                obscureLabel.config(text=f"GRACZ {nick} ODGADŁ HASŁO:  {password}")
                buttonsConfig(active=False)
                return
            pts = int(table[nick]['text'])
            table[nick].config(text=str(pts+10))
            return
        if letter==' ' or len(letter)!=1 or letter in correct or letter in used:
            pts = int(table[nick]['text'])
            table[nick].config(text=str(pts-5))
            continue

        if firstWrong:
            tries -= 1
            triesLabel.config(text=f'PRÓBY: {tries}')
            hangmanLabel.config(image=hangPics[12-tries])
            hangmanLabel.image = hangPics[12-tries]
            firstWrong = False
            used.append(letter)
            usedLabel.config(text='UŻYTE:  '+'  '.join(used))
        if not tries:
            pts = int(table[nick]['text'])
            table[nick].config(text=str(pts-10))
            win = True
            obscureLabel.config(text=f"ZOSTALIŚCIE POWIESZENI xx HASŁO:  {password}")
            buttonsConfig(active=False)
            return
        pts = int(table[nick]['text'])
        table[nick].config(text=str(pts-5))

def addPoints(nick):
    global table
    pts = int(table[nick]['text'])
    pts += 100
    table[nick].config(text=str(pts))

### FRAMES ###
startFrame = Frame(root, bg=BR)
instrFrame = Frame(root, bg=BR)
codeFrame = Frame(root, bg=BR)
passFrame = Frame(root, bg=BR)
gameFrame = Frame(root, bg=BR)

### INSTRUCTION FRAME ###
with open('instruction.txt', 'r', encoding='utf-8') as file:
    text = file.read()
    instrLabel = Label(instrFrame, bg=BR, fg=DR, font=SM, justify='center', text=text)
instrLabel.place(relx=0, rely=0, relwidth=1, relheight=0.85)
backButton = Button(instrFrame, bd=0, bg=DR, fg=BR, font=SM, text='POWRÓT', command=partial(changeFrame, instrFrame, startFrame))
backButton.place(relx=0.3, rely=0.9, relwidth=0.4, relheight=0.05)

### STARTING FRAME ###
title = Label(startFrame, text='HANGMAN: REACTIVATION', bg=BR, fg=DR, font=('Bahnshrift Light', 30, 'bold'))
title.place(relx=0.05, rely=0.1, relwidth=0.5, relheight=0.1)
startButton = Button(startFrame, text='ROZPOCZNIJ GRĘ', bd=0, bg=DR, fg=BR, font=BG, command=startRoom)
startButton.place(relx=0.1, rely=0.3, relwidth=0.4, relheight=0.1)
instrButton = Button(startFrame, text='JAK GRAĆ?', bd=0, bg=DR, fg=BR, font=BG, command=partial(changeFrame, startFrame, instrFrame))
instrButton.place(relx=0.1, rely=0.5, relwidth=0.4, relheight=0.1)
ground = Label(startFrame, bg=DR); ground.place(relx=0, rely=0.9, relwidth=1, relheight=0.1)
logo = Image.open('hangman-main.png')
logo = ImageTk.PhotoImage(logo.resize((350, 650), Image.ANTIALIAS))
logoLabel = Label(startFrame, image=logo, bg=BR)
logoLabel.place(relx=0.6, rely=0.035, relheight=0.865, relwidth=0.4)

### CODE FRAME ###
code = ''
waitLabel = Label(codeFrame, text='Czekam na graczy...', bg=BR, fg=DR, font=('Bahnschrift Light', 30, 'normal'))
waitLabel.place(relx=0, rely=0, relwidth=1, relheight=0.1)
codeLabel = Label(codeFrame, text=f'Kod do gry: {code}', fg=DR, bg=BR, font=BG)
codeLabel.place(relx=0, rely=.1, relwidth=1, relheight=.1)
table = []
playersLabel = Label(codeFrame, text='', bg=BR, fg=DR, font=SM)
playersLabel.place(relx=.1, rely=.25, relwidth=.8, relheight=.6)
toStart = Button(codeFrame, bd=0, text='POWRÓT', fg=BR, bg=DR, font=BG, command=partial(endGame, codeFrame))
toStart.place(relx=0.25, rely=.9, relwidth=.2, relheight=.05)
startGame = Button(codeFrame, bd=0, text='ZATWIERDŹ', fg=BR, bg=DR, font=BG, command=endGathering)
startGame.place(relx=0.55, rely=.9, relwidth=.2, relheight=.05)

### PASS FRAME ###
infoLabel = Label(passFrame, text='PODAJ HASŁO', bg=BR, fg=DR, font=('Bahnshrift Light', 30, 'bold'))
infoLabel.place(relx=0, relwidth=1, rely=0.1, relheight=0.1)
passwordEntry = Entry(passFrame, justify='center', bd=0, bg=DR, fg=BR, font=('Bahnshrift Light', 30, 'bold'), show="\u2022")
passwordEntry.place(relx=0.15, rely=0.45, relwidth=0.7, relheight=0.1)
end1Button = Button(passFrame, bd=0, bg=DR, fg=BR, font=SM, text='ZAKOŃCZ', command=partial(endGame, passFrame))
end1Button.place(relx=0.25, rely=0.925, relwidth=0.2, relheight=0.05)
toGuessing = Button(passFrame, bd=0, bg=DR, fg=BR, text='ZATWIERDŹ', font=SM, command=commitPass)
toGuessing.place(relx=0.55, relwidth=0.2, rely=0.925, relheight=0.05)

### GAME FRAME ###
hangPaths = [Image.open(f'images/hang{i}.png') for i in range(13)]
hangPics = [ImageTk.PhotoImage(image.resize((int(image.size[0]*600/image.size[1])+1, 600), Image.ANTIALIAS)) for image in hangPaths]
obscureLabel = Label(gameFrame, bg=BR, fg=DR, font=('Bahnshrift Light', 20, 'normal'), text=f'HASŁO: {obscured}')
obscureLabel.place(relx=0, relwidth=1, relheight=.1, rely=0)
usedLabel = Label(gameFrame, bg=BR, fg=DR, font=BG, text=f'UŻYTE:  '+'  '.join(used))
usedLabel.place(relx=0, relwidth=1, rely=.1, relheight=.05)
startLetters = Button(gameFrame, bd=0, bg=DR, fg=BR, font=SM, text='ZBIERZ LITERY', command=gather)
startLetters.place(relx=0.525, rely=0.85, relwidth=0.2, relheight=0.05)
stopLetters = Button(gameFrame, bd=0, bg=DR, fg=BR, font=SM, text='ZATRZYMAJ LITERY', command=stopGather)
stopLetters.place(relx=0.775, rely=0.85, relwidth=0.2, relheight=0.05)
updateTable = Button(gameFrame, bd=0, bg=DR, fg=BR, font=SM, text='AKTUALIZUJ WYNIKI', command=getResults)
updateTable.place(relx=0.525, rely=0.925, relwidth=0.2, relheight=0.05)
end2Button = Button(gameFrame, bd=0, bg=DR, fg=BR, font=SM, text='ZAKOŃCZ GRĘ', command=partial(endGame, gameFrame))
end2Button.place(relx=0.775, rely=0.925, relwidth=0.2, relheight=0.05)
triesLabel = Label(gameFrame, bg=BR, fg=DR, font=SM, text='PRÓBY:  12')
triesLabel.place(relx=0, relwidth=.5, rely=.15, relheight=.05)
Label(gameFrame, bg=BR, fg=DR, font=SM, text='TABLICA WYNIKÓW').place(relx=0.5, rely=0.15, relwidth=.5, relheight=0.05)
hangmanLabel = Label(gameFrame, bg=BR, fg=DR, font=BG, image=None)
hangmanLabel.place(relx=0, relwidth=.5, rely=.2, relheight=.8)
resultsFrame = Frame(gameFrame, bg=BR)
resultsFrame.place(relx=0.5, relwidth=.5, rely=0.2, relheight=0.6)


startFrame.place(relx=0, rely=0, relwidth=1, relheight=1)

root.protocol("WM_DELETE_WINDOW", destroy)
root.bind('<Escape>', destroy)
root.mainloop()
