
px_val = False

@micropython.viper
def testfunc() -> int:
    #val = int(px_val)
    if not px_val:
        return 0
    else:
        return 1
    
print(testfunc())