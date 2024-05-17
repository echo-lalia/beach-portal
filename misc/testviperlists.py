@micropython.viper
def test_viper():
    mystuff = [10,12,14,16]
    for stuff in mystuff:
        print(stuff << 11)
        
test_viper()