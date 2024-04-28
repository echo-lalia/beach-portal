from suncalc.mpy_decimal import DecimalNumber
import time, random


def debugprint_helper(name, in_var):
    print(f"{name} : {type(in_var).__name__} = {in_var}")

def og_func(number: str):

      # True: correct
    # Note: 
    step: int = 1   # 1: '-', 2: [0-9], 3: '.', 4: [0-9]
    position: int = 0
    integer_number: int = 0
    is_positive: bool = True
    num_decimals: int = 0
    number = tuple(number,)     # Faster than indexing the string
    length: int = len(number)
    digits: str = "0123456789"
    last_valid: int = 0
    while position < length:
        if step == 1:
            if number[position] == '-':
                is_positive = False
                position += 1
            step = 2
        elif step == 2:
            if digits.find(number[position]) != -1:  # [0-9]+
                integer_number = integer_number * \
                    10 + int(number[position])
                position += 1
                last_valid = position
            else:
                step = 3
        elif step == 3:
            if number[position] == DecimalNumber.DECIMAL_SEP:
                position += 1
                last_valid = position
            step = 4
        elif step == 4:
            if digits.find(number[position]) != -1:  # [0-9]*
                integer_number = integer_number * \
                    10 + int(number[position])
                num_decimals += 1
                position += 1
                last_valid = position
            else:
                break
    if last_valid == length:
        if not is_positive:
            integer_number = -integer_number
        return (True, integer_number, num_decimals)
    else:
        return (False, 0, 0)

@micropython.native
def test_func(number):
    step: int = 1   # 1: '-', 2: [0-9], 3: '.', 4: [0-9]
    position: int = 0
    integer_number: int = 0
    is_positive: bool = True
    num_decimals: int = 0
    #number = tuple(number,)     # Faster than indexing the string
    length: int = int(len(number))
    digits: str = "0123456789"
    last_valid: int = 0
    
    while position < length:

        if step == 1:
            if number[position] == '-':
                is_positive = False
                position += 1
            step = 2
            
        elif step == 2:
            if int(digits.find(number[position])) != -1:  # [0-9]+
                integer_number = integer_number * \
                    10 + int(digits.find(number[position]))
                position += 1
                last_valid = position
            else:
                step = 3

        elif step == 3:
            if number[position] == str(DecimalNumber.DECIMAL_SEP):
                position += 1
                last_valid = position
            step = 4
            
        elif step == 4:
            if int(digits.find(number[position])) != -1:  # [0-9]*
                integer_number = integer_number * \
                    10 + int(digits.find(number[position]))
                num_decimals += 1
                position += 1
                last_valid = position
            else:
                break
            
    if last_valid == length:
        if not is_positive:
            integer_number = -integer_number
        return (True, integer_number, num_decimals)
    else:
        return (False, 0, 0)
    
print(test_func('10.12345'))

# testing
#test_vals = [str(random.uniform(-10,10)) for i in range(20)]
test_vals = ['4785604650123456134.32456', '8143786053427650378652.34856904760154363478601347605873465', '13407607631405735.3145374']
vals_1 = []
vals_2 = []

start_time = time.ticks_ms()
for val in test_vals:
    vals_1.append(og_func(val))
end_time = time.ticks_ms()
ticks_diff = time.ticks_diff(end_time, start_time)
print(f"OG func took {ticks_diff}ms")

start_time = time.ticks_ms()
for val in test_vals:
    vals_2.append(test_func(val))
end_time = time.ticks_ms()
ticks_diff = time.ticks_diff(end_time, start_time)
print(f"test func took {ticks_diff}ms")

print()
print(vals_1)
print(vals_2)
