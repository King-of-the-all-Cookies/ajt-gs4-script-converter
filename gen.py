def create_file_with_lines(file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            for i in range(0, 1000000):
                line = f"\\{i}|\n"
                file.write(line)
                line = f"\\L{i}|\n"
                file.write(line)
                print(f"Recorded {i} of 999999 exceptions")
        print(f"Done.")
    except Exception as e:
        print(f"ERROR: {e}")

file_path = 'clean.txt'
create_file_with_lines(file_path)
