import FreeSimpleGUI as sg
import ChessLogic as cl
import time
import os
import threading
import cv2
import sys
import json
import VisionModule as vm
import platform
import ArmControl as ac
import lss_const as lssc
import pygame
import pathlib
import numpy as np

try:
    from picamera.array import PiRGBArray
    from picamera import PiCamera
except:
    pass

# Global Variables
CHESS_PATH = 'pieces_images'

BLANK = 0
PAWNW = 1
KNIGHTW = 2
BISHOPW = 3
ROOKW = 4
QUEENW = 5
KINGW = 6
PAWNB = 7
KNIGHTB = 8
BISHOPB = 9
ROOKB = 10
QUEENB = 11
KINGB = 12

blank = os.path.join(CHESS_PATH, 'blank.png')
bishopB = os.path.join(CHESS_PATH, 'nbishopb.png')
bishopW = os.path.join(CHESS_PATH, 'nbishopw.png')
pawnB = os.path.join(CHESS_PATH, 'npawnb.png')
pawnW = os.path.join(CHESS_PATH, 'npawnw.png')
knightB = os.path.join(CHESS_PATH, 'nknightb.png')
knightW = os.path.join(CHESS_PATH, 'nknightw.png')
rookB = os.path.join(CHESS_PATH, 'nrookb.png')
rookW = os.path.join(CHESS_PATH, 'nrookw.png')
queenB = os.path.join(CHESS_PATH, 'nqueenb.png')
queenW = os.path.join(CHESS_PATH, 'nqueenw.png')
kingB = os.path.join(CHESS_PATH, 'nkingb.png')
kingW = os.path.join(CHESS_PATH, 'nkingw.png')

images = {BISHOPB: bishopB, BISHOPW: bishopW, PAWNB: pawnB, PAWNW: pawnW, KNIGHTB: knightB, KNIGHTW: knightW,
          ROOKB: rookB, ROOKW: rookW, KINGB: kingB, KINGW: kingW, QUEENB: queenB, QUEENW: queenW, BLANK: blank}

FENCODE = ""
colorTurn = True
graveyard = 'k0'
playerColor = True
playing = False
blackSquareColor = '#B58863'
whiteSquareColor = '#F0D9B5'
state = "stby"
newGameState = "config"
whiteSide = 0
route = os.getcwd() + '/'
homography = []
prevIMG = []
chessRoute = ""
detected = True
selectedCam = 0
skillLevel = 10
cap = cv2.VideoCapture()
rotMat = np.zeros((2, 2))
physicalParams = {
    "baseradius": 0.00,
    "cbFrame": 0.00,
    "sqSize": 0.00,
    "cbHeight": 0.00,
    "pieceHeight": 0.00
}

# Configuration Functions
def systemConfig():
    global chessRoute
    if platform.system() == 'Windows':
        chessRoute = "games/stockfishX64.exe"
    elif platform.system() == 'Linux':
        chessRoute = "/usr/games/stockfish"

def pcTurn(board, engine):
    global sequence, state, homography, cap, selectedCam
    command = ""
    pcMove = engine.play(board, cl.chess.engine.Limit(time=1))
    sequence = cl.sequenceGenerator(pcMove.move.uci(), board)
    
    window["gameMessage"].update(sequence["type"])
    if sequence["type"] in ("White Queen Side Castling", "Black Queen Side Castling"):
        command = "q_castling"
    elif sequence["type"] in ("White King Side Castling", "Black King Side Castling"):
        command = "k_castling"
    elif sequence["type"] == "Capture":
        command = "capture"
    elif sequence["type"] == "Passant":
        command = "passant"
    elif sequence["type"] == "Promotion":
        command = "promotion"
    if command:
        speakThread = threading.Thread(target=speak, args=[command], daemon=True)
        speakThread.start()
        
    command = ""
    ac.executeMove(sequence["seq"], physicalParams, playerColor, homography, cap, selectedCam)
    board.push(pcMove.move)
    updateBoard(sequence, board)
    if board.is_checkmate():
        window["robotMessage"].update("CHECKMATE!")
        command = "checkmate"
    elif board.is_check():
        window["robotMessage"].update("CHECK!")
        command = "check"
    if command:
        speakThread = threading.Thread(target=speak, args=[command], daemon=True)
        speakThread.start()
    state = "robotMove"
    if board.is_game_over():
        playing = False
        state = "showGameResult"

def startEngine():
    global engine, state
    engine = cl.chess.engine.SimpleEngine.popen_uci(chessRoute)
    engine.configure({"Skill Level": skillLevel})
    if playerColor == colorTurn:
        state = "playerTurn"
    else:
        state = "pcTurn"

def playerTurn(board, squares):
    result = cl.moveAnalysis(squares, board)
    piece = ""
    if result:
        if result["type"] == "Promotion":
            while not piece:
                piece = coronationWindow()
            result["move"] += piece
        sequence = cl.sequenceGenerator(result["move"], board)
        window["gameMessage"].update(sequence["type"])
        board.push_uci(result["move"])
        updateBoard(sequence, board)
        return True
    return False

def startGame():
    window["newGame"].update(disabled=True)
    window["quit"].update(disabled=False)
    window["robotMessage"].update("Good Luck!")
    window["gameMessage"].update("--")

def quitGame():
    window["newGame"].update(disabled=False)
    window["quit"].update(disabled=True)
    engine.quit()

# Interface Functions
def renderSquare(image, key, location):
    if (location[0] + location[1]) % 2:
        color = blackSquareColor
    else:
        color = whiteSquareColor
    return sg.Button('', image_filename=image, size=(1, 1),
                     border_width=0, button_color=('white', color),
                     pad=(0, 0), key=key)

def redrawBoard(board):
    columns = 'abcdefgh'
    global playerColor
    if playerColor:
        sq = 63
        for i in range(8):
            window[str(8-i)+"r"].update("   "+str(8-i))
            window[str(8-i)+"l"].update(str(8-i)+"   ")
            for j in range(8):
                window[columns[j]+"t"].update(columns[j])
                window[columns[j]+"b"].update(columns[j])    
                color = blackSquareColor if (i + 7-j) % 2 else whiteSquareColor
                pieceNum = board.piece_type_at(sq)
                if pieceNum:
                    if not board.color_at(sq):
                        pieceNum += 6
                else:
                    pieceNum = 0
                piece_image = images[pieceNum]
                elem = window[(i, 7-j)]
                elem.update(button_color=('white', color),
                            image_filename=piece_image)
                sq -= 1
    else:
        sq = 0
        for i in range(8):
            window[str(8-i)+"r"].update("   "+str(i+1))
            window[str(8-i)+"l"].update(str(i+1)+"   ")
            for j in range(8):
                window[columns[j]+"t"].update(columns[7-j])
                window[columns[j]+"b"].update(columns[7-j]) 
                color = blackSquareColor if (i + 7-j) % 2 else whiteSquareColor
                pieceNum = board.piece_type_at(sq)
                if pieceNum:
                    if not board.color_at(sq):
                        pieceNum += 6
                else:
                    pieceNum = 0
                piece_image = images[pieceNum]
                elem = window[(i, 7-j)]
                elem.update(button_color=('white', color),
                            image_filename=piece_image)
                sq += 1

def updateBoard(move, board):
    global playerColor, images
    for cont in range(0, len(move["seq"]), 4):
        squareCleared = move["seq"][cont:cont+2]
        squareOcupied = move["seq"][cont+2:cont+4]
        scNum = cl.chess.SQUARE_NAMES.index(squareCleared)
        y = cl.chess.square_file(scNum)
        x = 7 - cl.chess.square_rank(scNum)
        color = blackSquareColor if (x + y) % 2 else whiteSquareColor
        if playerColor:
            elem = window[(x, y)]
        else:
            elem = window[(7-x, 7-y)]
        elem.update(button_color=('white', color),
                    image_filename=blank)  

        if squareOcupied != graveyard:
            soNum = cl.chess.SQUARE_NAMES.index(squareOcupied)
            pieceNum = board.piece_type_at(soNum)
            if not board.color_at(soNum):
                pieceNum += 6
            y = cl.chess.square_file(soNum)
            x = 7 - cl.chess.square_rank(soNum)
            color = blackSquareColor if (x + y) % 2 else whiteSquareColor
            if playerColor:
                elem = window[(x, y)]
            else:
                elem = window[(7-x, 7-y)]    
            elem.update(button_color=('white', color),
                        image_filename=images[pieceNum])         

def sideConfig():
    global newGameState, state, whiteSide, prevIMG, rotMat
    i = 0
    img = vm.drawQuadrants(prevIMG)
    imgbytes = cv2.imencode('.png', img)[1].tobytes()

    windowName = "Calibration"
    initGame = [[sg.Text('Please select the "white" pieces side', justification='center', pad=(25,(5,15)), font='Any 15')],
                [sg.Image(data=imgbytes, key='boardImg')],
                [sg.Radio('1-2', group_id='grp', default=True, font='Any 14'), sg.Radio('2-3', group_id='grp', font='Any 14'), sg.Radio('4-3', group_id='grp', font='Any 14'), sg.Radio('1-4', group_id='grp', font='Any 14')],
                [sg.Text('_'*30)],
                [sg.Button("Back"), sg.Submit("Play")]]
    newGameWindow = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, location=(100,50), icon='interface_images/robot_icon.ico').layout(initGame) 

    while True:
        button, value = newGameWindow.read(timeout=100)
        if button == "Play":
            newGameState = "initGame"
            while value[i] == False and i < 4:
                i += 1
            whiteSide = i
            if whiteSide == 0:
                theta = 90
            elif whiteSide == 1:
                theta = 180
            elif whiteSide == 2:
                theta = -90
            elif whiteSide == 3:
                theta = 0
            rotMat = vm.findRotation(theta)
            prevIMG = vm.applyRotation(prevIMG, rotMat)
            break
        if button == "Back":
            newGameState = "ocupiedBoard"
            break
        if button in (None, 'Exit'):
            state = "stby"
            newGameState = "config"
            break   
    newGameWindow.close()

def ocupiedBoard():
    global newGameState, state, selectedCam, homography, prevIMG
    windowName = "Calibration"
    initGame = [[sg.Text('Place the chess pieces and press Next', justification='center', pad=(25,(5,15)), font='Any 15')],
                [sg.Image(filename='', key='boardVideo')],
                [sg.Text('_'*30)],
                [sg.Button("Back"), sg.Submit("Next")]]
    newGameWindow = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, location=(100,50), icon='interface_images/robot_icon.ico').layout(initGame)  

    while True:
        button, value = newGameWindow.read(timeout=10)
        if detected:    
            frame = takePIC()
            prevIMG = vm.applyHomography(frame, homography)
            imgbytes = cv2.imencode('.png', prevIMG)[1].tobytes()
            newGameWindow['boardVideo'].update(data=imgbytes)
        if button == "Next":
            newGameState = "sideConfig"
            break
        if button == "Back":
            newGameState = "calibration"
            break
        if button in (None, 'Exit'):
            state = "stby"
            newGameState = "config"
            break   
    newGameWindow.close()

def calibration():
    global newGameState, state, selectedCam, homography, detected
    cbPattern = cv2.imread(route+'interface_images/cb_pattern.jpg', cv2.IMREAD_GRAYSCALE)
    windowName = "Camera calibration"
    initGame = [[sg.Text('Please adjust your camera and remove any chess piece', justification='center', pad=(25,(5,15)), font='Any 15', key="calibrationBoard")],
                [sg.Image(filename='', key='boardVideo')],
                [sg.Text('_'*30)],
                [sg.Button("Back"), sg.Submit("Next")]]
    newGameWindow = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, location=(100,50), icon='interface_images/robot_icon.ico').layout(initGame) 

    while True:
        button, value = newGameWindow.read(timeout=10)
        if detected:    
            frame = takePIC()
            imgbytes = cv2.imencode('.png', frame)[1].tobytes()  
            newGameWindow['boardVideo'].update(data=imgbytes)
            homography = []
            retIMG, homography = vm.findTransformation(frame, cbPattern)
            if retIMG:
                print(f"Debug: Calibration successful, homography matrix: {homography}")
                newGameWindow['calibrationBoard'].update("Camera calibration successful. Please press Next")
            else:
                print("Debug: Calibration failed, homography not computed")
                newGameWindow['calibrationBoard'].update("Please adjust your camera and remove any chess piece")
        if button == "Next" and retIMG:
            newGameState = "ocupiedBoard"
            break
        if button == "Back":
            if not selectedCam:
                cap.close()
            newGameState = "config"
            break
        if button in (None, 'Exit'):
            state = "stby"
            newGameState = "config"
            break   
    newGameWindow.close() 

def newGameWindow():
    global playerColor, newGameState, state, detected, cap, selectedCam, skillLevel
    windowName = "Configuration"
    frame_layout = [[sg.Radio('RPi Cam', group_id='grp', default=True, key="rpicam"), sg.VerticalSeparator(pad=None), sg.Radio('USB0', group_id='grp', key="usb0"), sg.Radio('USB1', group_id='grp', key="usb1")]]
    initGame = [[sg.Text('Game Parameters', justification='center', pad=(25,(5,15)), font='Any 15')],
                [sg.Checkbox('Play as White', key='userWhite', default=playerColor)],
                [sg.Combo([sz for sz in range(1, 11)], default_value=10, key="enginelevel"), sg.Text('Engine skill level', pad=(0,0))],
                [sg.Frame('Camera Selection', frame_layout, pad=(0, 10), title_color='white')],
                [sg.Text('_'*30)],
                [sg.Button("Exit"), sg.Submit("Next")]]
    windowNewGame = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, icon='interface_images/robot_icon.ico').layout(initGame)
    while True:
        button, value = windowNewGame.read()
        if button == "Next":
            if value["rpicam"] == True:
                selectedCam = 0
            elif value["usb0"] == True:
                selectedCam = 1
            elif value["usb1"] == True:
                selectedCam = 2
            cap = initCam(selectedCam)
            if detected:
                newGameState = "calibration"
                playerColor = value["userWhite"]
                skillLevel = value["enginelevel"] * 2
            break
        if button in (None, 'Exit'):
            state = "stby"
            break   
    windowNewGame.close() 

def coronationWindow():
    global playerColor
    pieceSelected = ""
    rook = rookB
    knight = knightB
    bishop = bishopB
    queen = queenB
    if playerColor:
        rook = rookW
        knight = knightW
        bishop = bishopW
        queen = queenW
    windowName = "Promotion"
    pieceSelection = [[sg.Text('Select the piece for promotion', justification='center', pad=(25,(5,15)), font='Any 15')],
                     [sg.Button('', image_filename=rook, size=(1, 1), border_width=0, button_color=('white', "brown"), pad=((40,0), 0), key="rook"),
                      sg.Button('', image_filename=knight, size=(1, 1), border_width=0, button_color=('white', "brown"), pad=(0, 0), key="knight"),
                      sg.Button('', image_filename=bishop, size=(1, 1), border_width=0, button_color=('white', "brown"), pad=(0, 0), key="bishop"),
                      sg.Button('', image_filename=queen, size=(1, 1), border_width=0, button_color=('white', "brown"), pad=(0, 0), key="queen")]]
    windowNewGame = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, icon='interface_images/robot_icon.ico').layout(pieceSelection)
    while True:
        button, value = windowNewGame.read()
        if button == "rook":
            pieceSelected = "r"
            break
        if button == "knight":
            pieceSelected = "k"
            break
        if button == "bishop":
            pieceSelected = "b"
            break
        if button == "queen":
            pieceSelected = "q"
            break
        if button in (None, 'Exit'):
            break   
    windowNewGame.close() 
    return pieceSelected

def takePIC():  
    global selectedCam, cap
    if selectedCam:
        for i in range(5):
            cap.grab()
        _, frame = cap.read()
    else:
        cap.capture(rawCapture, format="bgr")
        frame = rawCapture.array
        rawCapture.truncate(0)
    return frame

def quitGameWindow():
    global playing, window, cap
    windowName = "Quit Game"
    quitGame = [[sg.Text('Are you sure?', justification='center', size=(30, 1), font='Any 13')],
                [sg.Submit("Yes", size=(15, 1)), sg.Submit("No", size=(15, 1))]]
    if not selectedCam:
        cap.close()
    if playing:
        while True:
            windowNewGame = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, icon='interface_images/robot_icon.ico').layout(quitGame)
            button, value = windowNewGame.read()
            if button == "Yes":
                playing = False
                break
            if button in (None, 'Exit', "No"):
                break   
    windowNewGame.close()   

def mainBoardLayout():
    menu_def = [['&Configuration', ["&Dimensions", "E&xit"]],      
                ['&Help', 'About']]  
    sg.theme('Dark')  # Updated to use sg.theme() for compatibility
    board_layout = [[sg.Text(' '*12)] + [sg.Text('{}'.format(a), pad=((0,47),0), font='Any 13', key=a+'t') for a in 'abcdefgh']]
    for i in range(8):
        numberRow = 8-i 
        row = [sg.Text(str(numberRow)+'   ', font='Any 13', key=str(numberRow)+"l")]
        for j in range(8):
            row.append(renderSquare(blank, key=(i,j), location=(i,j)))
        row.append(sg.Text('   '+str(numberRow), font='Any 13', key=str(numberRow)+"r"))
        board_layout.append(row)
    board_layout.append([sg.Text(' '*12)] + [sg.Text('{}'.format(a), pad=((0,47),0), font='Any 13', key=a+'b') for a in 'abcdefgh'])

    frame_layout_game = [[sg.Button('---', size=(14, 2), border_width=0, font=('courier', 16), button_color=('black', "white"), pad=(4, 4), key="gameMessage")]]
    frame_layout_robot = [[sg.Button('---', size=(14, 2), border_width=0, font=('courier', 16), button_color=('black', "white"), pad=(4, 4), key="robotMessage")]]
    board_controls = [[sg.Button('New Game', key='newGame', size=(15, 2), pad=(0,(0,7)), font=('courier', 16))],
                     [sg.Button('Quit', key='quit', size=(15, 2), pad=(0, 0), font=('courier', 16), disabled=True)],
                     [sg.Frame('GAME', frame_layout_game, pad=(0, 10), font='Any 12', title_color='white', key="frameMessageGame")],
                     [sg.Frame('ROBOT', frame_layout_robot, pad=(0, (0,10)), font='Any 12', title_color='white', key="frameMessageRobot")]]
    layout = [[sg.Menu(menu_def, tearoff=False, key="manubar")], 
              [sg.Column(board_layout), sg.VerticalSeparator(pad=None), sg.Column(board_controls)]]
    return layout

def initCam(selectedCam):
    global detected, rawCapture
    if selectedCam:
        cap = cv2.VideoCapture(selectedCam - 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not cap.isOpened():
            detected = False  
            sg.popup_error('USB Video device not found')
    else:
        cap = PiCamera()
        if not cap:
            detected = False    
            sg.popup_error('RPi camera module not found')
        else:
            cap.resolution = (640, 480)
            rawCapture = PiRGBArray(cap, size=(640, 480))
    return cap

def loadParams():
    global physicalParams
    if os.path.isfile('params.txt'):
        with open('params.txt') as json_file:
            physicalParams = json.load(json_file)
    else:
        with open('params.txt', 'w') as outfile:
            json.dump(physicalParams, outfile)

def phisicalConfig():
    global physicalParams
    windowName = "Chessboard parameters"
    robotParamLayout = [[sg.Text('Insert the physical dimensions in inches', justification='center', font='Any 14', pad=(10,10))], 
                        [sg.Spin([sz/100 for sz in range(1, 1000)], initial_value=physicalParams["baseradius"], font='Any 11'), sg.Text('Base Radius', pad=(0,0))],
                        [sg.Spin([sz/100 for sz in range(1, 1000)], initial_value=physicalParams["cbFrame"], font='Any 11'), sg.Text('Chess Board Frame', pad=(0,0))],
                        [sg.Spin([sz/100 for sz in range(1, 1000)], initial_value=physicalParams["sqSize"], font='Any 11'), sg.Text('Square Size', pad=(0,0))],
                        [sg.Spin([sz/100 for sz in range(1, 1000)], initial_value=physicalParams["cbHeight"], font='Any 11'), sg.Text('Chess Board Height', pad=(0,0))],
                        [sg.Spin([sz/100 for sz in range(1, 1000)], initial_value=physicalParams["pieceHeight"], font='Any 11'), sg.Text('Tallest Piece Height', pad=(0,0))],
                        [sg.Text('_'*37)],
                        [sg.Submit("Save", size=(15, 1)), sg.Submit("Close", size=(15, 1))]]
    while True:
        robotParamWindow = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, icon='interface_images/robot_icon.ico').layout(robotParamLayout)
        button, value = robotParamWindow.read()
        if button == "Save":
            physicalParams = {
                "baseradius": float(value[0]),
                "cbFrame": float(value[1]),
                "sqSize": float(value[2]),
                "cbHeight": float(value[3]),
                "pieceHeight": float(value[4])
            }
            with open('params.txt', 'w') as outfile:
                json.dump(physicalParams, outfile)
            break
        if button in (None, 'Close'):
            break   
    robotParamWindow.close()   

layout = mainBoardLayout()
window = sg.Window('ChessRobot', default_button_element_size=(12,1), auto_size_buttons=False, icon='interface_images/robot_icon.ico').layout(layout)

def speak(command):
    pygame.mixer.init()
    filePath = str(pathlib.Path().absolute()) + "/audio/"
    pygame.mixer.music.load(filePath + command + ".mp3")
    pygame.mixer.music.play()

def main():
    global playerColor, state, playing, sequence, newGameState, detected, physicalParams, prevIMG, rotMat, homography, colorTurn
    systemConfig()
    loadParams()
    board = cl.chess.Board()
    squares = []
    last_move_time = time.time()

    while True:
        button, value = window.read(timeout=100)
        if button in (None, 'Exit') or (value and value.get("manubar") == "Exit"):
            angles_rest = (0, -1150, 450, 1100, 0)
            _ = ac.LSSA_moveMotors(angles_rest)
            ac.allMotors.limp()
            ac.allMotors.setColorLED(lssc.LSS_LED_Black)
            break

        if value and value.get("manubar") == "Dimensions":
            if playing:
                sg.popup("Please, first quit the game")
            else:
                phisicalConfig()

        if button == "newGame":
            if all(physicalParams.values()): 
                state = "startMenu"
            else:
                sg.popup_error('Please configure the chess board dimensions in the Configuration option of menu bar')

        if button == "quit":
            ac.allMotors.setColorLED(lssc.LSS_LED_Black)
            quitGameWindow()
            if not playing:
                state = "showGameResult"

        if state == "stby":
            pass

        elif state == "startMenu":
            if newGameState == "config":
                newGameWindow()
            elif newGameState == "calibration":
                calibration()
            elif newGameState == "ocupiedBoard":
                ocupiedBoard()
            elif newGameState == "sideConfig":
                sideConfig()
            elif newGameState == "initGame":
                playing = True
                newGameState = "config"
                board = cl.chess.Board()
                if FENCODE:
                    board = cl.chess.Board(FENCODE)
                colorTurn = board.turn
                startGame()
                last_move_time = time.time()
                startEngineThread = threading.Thread(target=startEngine, daemon=True)
                startEngineThread.start()
                speak("good_luck")
                state = "stby"
                redrawBoard(board)

        elif state == "playerTurn":
            if time.time() - last_move_time >= 30:  # 30-second auto-timer
                try:
                    print("Debug: 30-second timer triggered, capturing image...")
                    currentIMG = takePIC()
                    cv2.imwrite("debug_prevIMG.png", prevIMG)
                    print("Debug: Image captured, applying homography...")
                    curIMG = vm.applyHomography(currentIMG, homography)
                    print("Debug: Homography applied, applying rotation...")
                    curIMG = vm.applyRotation(curIMG, rotMat)
                    cv2.imwrite("debug_curIMG.png", curIMG)
                    print("Debug: Rotation applied, detecting moves...")
                    squares = vm.findMoves(prevIMG, curIMG)
                    print(f"Debug: Move detection complete, squares changed: {squares}")
                    if playerTurn(board, squares):
                        print("Debug: Valid move detected, transitioning to pcTurn")
                        state = "pcTurn"
                        last_move_time = time.time()
                        if board.is_game_over():
                            print("Debug: Game over, transitioning to showGameResult")
                            playing = False
                            state = "showGameResult"
                    else:
                        print("Debug: Invalid move detected, staying in playerTurn")
                        window["gameMessage"].update("Invalid move!")
                        speak("invalid_move")
                        state = "playerTurn"
                        last_move_time = time.time()
                except Exception as e:
                    print(f"Error in playerTurn: {e}")
                    sg.popup_error(f"Error processing move: {e}")
                    state = "stby"

        elif state == "pcTurn":
            pcTurnThread = threading.Thread(target=pcTurn, args=(board, engine,), daemon=True)
            pcTurnThread.start()
            state = "stby"

        elif state == "robotMove":
            previousIMG = takePIC()
            prevIMG = vm.applyHomography(previousIMG, homography)
            prevIMG = vm.applyRotation(prevIMG, rotMat)
            state = "playerTurn"
            last_move_time = time.time()
            window["robotMessage"].update("---")

        elif state == "showGameResult":
            gameResult = board.result()
            if gameResult == "1-0":
                window["gameMessage"].update("Game Over\nWhite Wins")
                if not playerColor:
                    ac.winLED(ac.allMotors)
                else:
                    speak("goodbye")
            elif gameResult == "0-1":
                window["gameMessage"].update("Game Over\nBlack Wins")
                if playerColor:
                    ac.winLED(ac.allMotors)
                else:
                    speak("goodbye")
            elif gameResult == "1/2-1/2":
                window["gameMessage"].update("Game Over\nDraw")
            else:
                window["gameMessage"].update("Game Over")
            window["robotMessage"].update("Goodbye")
            quitGame()
            state = "stby"

    window.close()

if __name__ == "__main__":
    main()