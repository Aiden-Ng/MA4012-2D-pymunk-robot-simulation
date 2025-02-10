# Log params
LOG = False
WARN = True
DEBUG = False

# Made for logging purpose
def printf(string_args, state_args = "DEBUG"):
    if state_args == "LOG":
        if LOG:
            print(f"\033[93mLOGGING\033[0m" + " : " + f"{string_args}") # Yellow text for logging
        else: 
            pass
    if state_args == "WARN":
        if WARN:
            print(f"\033[91mWARNING\033[0m" + " : " + f"{string_args}")  # Red text for warning
        else: 
            pass
    if state_args == "DEBUG":
        if DEBUG:
            print(f"\033[38;2;255;165;0mDEBUG\033[0m" + " : " + f"{string_args}")  # Orange text for debug
            # how to make orange text
        else: 
            pass