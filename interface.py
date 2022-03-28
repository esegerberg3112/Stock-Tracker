# Module for creating, defining and maintaining user interfaces for the project
import sqlconnect as sql
import PySimpleGUI as sg
import finance
import psycopg2
import re
import time

# a custom popup for if a stock ticker doesn't exist
def invalid_ticker_search():
    layout = [
        [sg.Text("That ticker does not exist, try searching again.")],
        [sg.Button("OK")]
    ]
    win = sg.Window("Stock Search", layout, modal=True, grab_anywhere=True)
    event, value = win.read()
    if event == sg.WIN_CLOSED or event == "OK":
        win.close()

# defining a custom popup for when an account is successfully created
def account_created_popup():
    layout = [
        [sg.Text("You're account was successfully created!")],
        [sg.Button("OK")]
    ]
    win = sg.Window("Account Created", layout, modal=True,grab_anywhere=True)
    event, value = win.read()
    if event == sg.WIN_CLOSED:
        win.close()
    # return to main login page
    if event == "OK":
        win.close()
        user_login()

# function to create the default user login window that all users will start at
def user_login():
    # define layout for user login window
    layout = [
        [sg.Text("Welcome to Stock Tracker!!", font=("Arial", 20))],
        [sg.VPush()],
        [sg.Text("Username ", size=(12, 1)), sg.InputText(key='-USERNAME-')],
        [sg.Text("Password ", size=(12, 1)), sg.InputText(key='-PASSWORD-', password_char='*')],
        [sg.Push(), sg.Button("Login"), sg.Button("Cancel"), sg.Push()],
        [],
        [sg.Push(), sg.Button("New User?"), sg.Push()],
        [sg.VPush()]
    ]

    # create the window
    window = sg.Window("Stock Tracker", layout, size=(350, 200))

    # create event loop
    # create a count to allow for a maximum of 3 login attempts
    counter = 0
    while True:
        event, values = window.read()
        # end program if user closes widow or presses 'Cancel'
        if event in (sg.WIN_CLOSED, 'Cancel'):
            break

        # if user doesn't have an account, navigate them to account creation page if select "New User?"
        if event == "New User?":
            window.close() # close the current window, since have a separate window for new user creation
            create_user()

        # if user attempts to login, take username and password and attempt to authenticate against database
        if event == "Login":
            counter += 1
            # store user inputs
            username = values['-USERNAME-'].strip()
            password = values['-PASSWORD-'].strip()

            # query database to see if credentials match database entry
            match = sql.check_credentials(username, password)
            # if username/password combo match (query True), login user to their Stock Tracker interface
            if match:
                window.close()
                stock_interface(username)
            # if login has failed 3 times, close the program
            elif counter == 3:
                window.close()
                sg.popup("You have input incorrect information too many times, goodbye.")
            else:
                sg.popup("That username/password does not exist. Please try again.")
    window.close()

# function for window that allows for creation of a new user
def create_user():
    # define layout for new user creation screen
    layout = [
        [sg.Text("Create Your Account", font=("Arial", 14))],
        [sg.Text("Username: ", size=(15, 1)), sg.InputText(key='-USERNAME-')],
        [sg.Text("Password: ", size=(15, 1)), sg.InputText(key='-PASSWORD-', password_char='*')],
        [sg.Text("Confirm Password: ", size=(15, 1)), sg.InputText(key='-CONFIRMPASSWORD-', password_char='*')],
        [sg.VPush()],
        [sg.Push(), sg.Button("Create"), sg.Push()],
        [sg.VPush()]
    ]
    # create the window
    window = sg.Window("Stock Tracker", layout, size=(300, 200))

    while True:
        event, values = window.read()
        # end program if user closes widow
        if event == sg.WIN_CLOSED:
            break
        # if user selects create
        if event == "Create":
            username = values['-USERNAME-'].strip()
            password = values['-PASSWORD-'].strip()
            confirm = values['-CONFIRMPASSWORD-'].strip()
            # call function to insert new user into database
            try:
                # if password and confirm password don't match, prompt popup and have user try again
                if password != confirm:
                    sg.Popup('The passwords you entered do not match, try again!!', title="Issue", keep_on_top=True)
                    continue
                hashed_passw = sql.hash_password(password)
                sql.add_user(username, hashed_passw)
            except psycopg2.errors.UniqueViolation:
                sg.Popup('That username already exists, please try a new one!', title="Issue", keep_on_top=True)
                continue
            except psycopg2.errors.StringDataRightTruncation:
                sg.Popup('That username is too long, please limit it to 20 characters!', title="Issue", keep_on_top=True)
                continue

            # if username was successfully created, prompt custom pop up and return to main login page
            window.close()
            account_created_popup()

    window.close()

# function to create GUI for Stonks-R-Us interface
def stock_interface(username):
    # define what will be inside the UI window
    search_frame = [
            [sg.Text("Welcome to Stock Tracker!!", font=40, justification='c')],
            [sg.Text("Search a stock ticker:"), sg.InputText(key='-SEARCH-', size=(15, 1)), sg.Button("Search"),
             sg.Button("Favorite")]
    ]
    # will hide this until user actually enters a search
    results_frame = [
        [sg.Listbox(values=(), key='-SEARCHDATA-', size=(25, 120))]
    ]

    # pull in existing list of favorites, set as default Account view
    add_list = []
    fav_string = sql.get_favorites(username)
    if fav_string is not None:
        favorites_list = fav_string.split(';')
        for i in favorites_list:
            output = finance.get_quote(i)
            value = "{ticker}: {price}, {change}%".format(ticker=i, price=output['currentPrice'], change=output['percentChangeSinceClose'])
            add_list.append(value)

    account_frame = [
        [sg.Listbox(values=(add_list), key='-ACCOUNTDATA-', size=(25, 120))]
    ]

    layout = [
        [sg.Frame("Search", search_frame)],
        [sg.Frame("Account", account_frame), sg.Frame("Results", results_frame, key="-RESULTSFRAME-", visible=False)]
    ]

    # create the window
    window = sg.Window("Stock Tracker", layout, size=(425, 250), finalize=True)

    # create event loop
    while True:
        event, values = window.read()
        # end program if user closes widow
        if event == sg.WIN_CLOSED:
            break

        # if user favorites a ticker, add that to their account view along with the current price
        if event == 'Favorite':
            # ensuring consistency in format of ticker string
            ticker_cleaned = re.sub('[^A-Za-z]+', '', values['-SEARCH-']).lower()
            search_output = finance.get_quote(ticker_cleaned)

            if not search_output:
                invalid_ticker_search()
                continue

            # check if searched ticker is already in favorites list. Might be NULL in SQL table (default value)
            current_favorites = sql.get_favorites(username)
            fav_empty = False
            if current_favorites is None:
                # set a flag to indicate that favorites string is empty
                fav_empty = True
                pass
            elif ticker_cleaned in current_favorites:
                continue

            # get existing list of Favorites, created new Favorite to be added
            fav_list = window['-ACCOUNTDATA-'].get_list_values()
            add_fave = "{ticker}: {price}, {change}%".format(ticker=ticker_cleaned,
                                                            price=search_output['currentPrice'],
                                                            change=search_output['percentChangeSinceClose'])

            # if element is empty (no values), it's an empty tuple. Once it is updated with values, it is a list
            if isinstance(fav_list, list):
                fav_list.append(add_fave)
                window.Element('-ACCOUNTDATA-').update(values=fav_list)
            else:
                window.Element('-ACCOUNTDATA-').update(values=[add_fave])

            # add ticker to favorites list, as a semi-colon separated string
            # if favorite column is empty, need to add a ";" at the end of what is inserted into table
            if fav_empty:
                sql.add_favorite(username, ticker_cleaned)
            else:
                ticker_mod = current_favorites + ';' + ticker_cleaned
                sql.add_favorite(username, ticker_mod)

        # if user enters something in the search, check if it is a valid company/ticker
        # if it is, pull the relevant data from Yahoo Finance
        if event == 'Search':
            ticker = values['-SEARCH-']
            ticker_cleaned = re.sub('[^A-Za-z]+', '', ticker).lower()
            output = finance.get_quote(ticker_cleaned)
            if not output:
                invalid_ticker_search()
                continue

            # update the data, as well as make the Results Frame visible
            window['-RESULTSFRAME-'].update(visible=True)
            window.Element('-SEARCHDATA-').update(values=[output['companyName'], "Price: {price}".format(price=output['currentPrice']), "Prev. Closing Price: {close}".format(close=output['lastClose']), "% Change Since Close: {change}".format(change=output['percentChangeSinceClose'])])
    window.close()