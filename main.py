import os
import sys


if len(sys.argv) > 0:
    print("AJAAT GS4 SCRIPT CONVERTER")
    print("Example decode: python main.py d <file>")
    print("Example encode: python main.py e <file>")


de = sys.argv[1]
file = sys.argv[2]


l = []
l.append("@echo off")
l.append("color 2")
l.append("cls")

if de == 'd':
    l.append('echo Decoding...')
    l.append(f'python main1.py d {file}')
    l.append(f'python main2.py decode {file}.bin')
    
elif de == 'e':
    l.append('echo Encoding...')
    f1 = file
    f1 = f1[:-3]
    f1 = f"{f1}bin"
    l.append(f'python main2.py encode {file}')
    l.append(f'python main1.py e {f1}')
    
     
else:
    print('You stupid idiot?')


l.append('color f')
l.append('cls')
l.append('echo Done!')
l.append('pause')
l.append('cls')



bat_file_path = 'cache.bat'
with open(bat_file_path, 'w') as bat_file:
    for line in l:
        bat_file.write(line + '\n')


os.system(bat_file_path)
os.remove(bat_file_path)


if de == 'd':
    os.remove(f"{file}.bin")

elif de == 'e':
    os.remove(f1)
    
