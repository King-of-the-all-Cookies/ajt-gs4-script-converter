# -*- coding: utf-8 -*-

import argparse
import glob
import re
import os
import sys
import unicodedata


"""

Script to convert AJ:AA Trilogy's GS4 (Apollo Justice) script binary files

---

Don't forget that you need to use the "gs456scr.py" script first and use those decoded ".bin" files:
https://gist.github.com/osyu/5bb86d49153edef5415a7aba09a48ca1

---

***IMPORTANT: For the mappings to work, also download this file and place it in the same directory to the script:
https://raw.githubusercontent.com/niltwill/capcom-mods/main/scripts/ajaat-gs4-script-mappings.txt

The "L" prefix before a decimal number means "Language", indicating that it's possibly a language character. This letter can be ignored.
It is only an indicator letter to convert only these characters into unicode.

---

* You can simply convert every file in the same directory by using the command:
ajaat-gs4-script.py decode *.bin

* To convert back to binary:
ajaat-gs4-script.py encode *.txt

---

* If you're not going for English (en), where non-Latin characters are rare, you should always use this:
ajaat-gs4-script.py decode --unicode --nolparam *.bin

Remove "--nolparam" if it causes issues, however it helps to not confuse text strings with command parameter values.

* And to convert these files back, include "--unicode" as well:
ajaat-gs4-script.py encode --unicode *.txt

"""


def load_mappings(filename, separator):
    # Get the directory path of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the mappings file
    mappings_file_path = os.path.join(script_dir, filename)

    replacement_mapping = {}
    try:
        with open(mappings_file_path, 'r') as file:
            for line in file:
                # Skip empty lines and lines starting with '#'
                if line.strip() == '' or line.strip().startswith('#'):
                    continue

                # Split the line by '=', but only once to separate the numeric sequence from the rest of the line
                numeric_sequence, remaining_part = line.split('=', 1)

                # Split the remaining part by '|'
                parts = remaining_part.split('|')
                if len(parts) != 2:
                    # Skip lines that do not contain exactly one '|' sign after the '='
                    continue

                replacement_string, argument_info = parts
                
                # Add back the separator to the string
                replacement_string += separator

                # Split the argument_info string to extract the argument number and range
                argument_range = tuple(map(int, argument_info.strip().split('-')))

                replacement_mapping[numeric_sequence.strip()] = (replacement_string.strip(), argument_range)
    except FileNotFoundError:
        print(f"Error: Mapping file '{filename}' not found.")
        print("Download it from this URL and place it into the script's directory:")
        print("https://raw.githubusercontent.com/niltwill/capcom-mods/main/scripts/ajaat-gs4-script-mappings.txt")
        sys.exit(1)

    return replacement_mapping


# Preprocess mappings to have a static reverse mapping dictionary
reverse_mapping = {}


def preprocess_mappings(mappings_file, delimiter='|'):
    global reverse_mapping
    replacement_mapping = load_mappings(mappings_file, delimiter)
    reverse_mapping = {value[0]: key for key, value in replacement_mapping.items()}


# Function to return the command number based on the text string
def get_command_number(command_name):
    global reverse_mapping
    if reverse_mapping is not None:
        return reverse_mapping.get(command_name)


# Function to convert the decimal ASCII to symbol representation
def convert_decimal_to_ascii(decimal_value):
    if 32 <= decimal_value <= 126:
        ascii_symbol = chr(decimal_value)
        return ascii_symbol
    else:
        return decimal_value


# Function to convert ASCII symbol to decimal representation
def convert_ascii_to_decimal(char):
    ascii_symbol = char
    if 32 <= ord(ascii_symbol) <= 126:
        return ord(ascii_symbol)
    else:
        return ascii_symbol


def get_first_numeric_values(string, num_parameters):
    # Use rfind to locate the last pipe delimiter
    last_pipe_index = string.rfind("|")

    # Split the string at pipes up to the last delimiter (inclusive)
    if last_pipe_index != -1:
        parts = string.split("|", last_pipe_index + 1)  # Include last delimiter
    else:
        parts = [string]  # No pipes found, return the entire string

    # Check if enough values are present
    if len(parts) >= num_parameters:
        return parts[:num_parameters]
    else:
        return None


def find_and_add_delimiters(string):
    # Find all occurrences of "\L[numeric]" or digits not followed by a pipe
    matches = re.findall(r"\\L(\d+)(?!\|)", string)

    # Add delimiters after each match
    for match in matches:
        string = string.replace(match, match + "|")

    return string


def replace_all_occurrences_backwards(string, expression, replacement, count=None):
    if count is None:
        count = string.count(expression) # If count is not specified, replace all occurrences

    while count > 0:
        last_index = string.rfind(expression)
        if last_index != -1:
            before_last = string[:last_index]
            after_last = string[last_index + len(expression):]
            string = before_last + replacement + after_last
            count -= 1
        else:
            break
    return string


def get_range_parameter(replacement_string, ascii_part, num_parameters, mappings_file):
    # Get command numeric value
    test_cmd = get_command_number(replacement_string)

    # Really barebones command range support here
    # Cause I didn't want to make this super complicated
    # As there are not that many commands with a range
    current_cmds = ascii_part.count('\\')
    base_param = current_cmds - num_parameters

    if test_cmd == "\\57349|":  # \music
        if base_param == 3:
            num_parameters = 3
    elif test_cmd == "\\57397|":  # \cmd051
        if base_param == 1:
            num_parameters = 1
        elif base_param == 2:
            num_parameters = 2
        elif base_param == 3:
            num_parameters = 3
        elif base_param == 4:
            num_parameters = 4
    elif test_cmd == "\\57416|":  # \cmd066
        if base_param == 1:
            num_parameters = 1
        elif base_param == 2:
            num_parameters = 2
    elif test_cmd == "\\57424|":  # \cmd073
        if base_param == 3:
            num_parameters = 3
    elif test_cmd == "\\57451|":  # \cmd095
        if base_param == 3:
            num_parameters = 3
    elif test_cmd == "\\57461|":  # \cmd104
        if base_param == 4:
            num_parameters = 4
    elif test_cmd == "\\57489|":  # \codeblock
        if base_param == 2:
            num_parameters = 2
    elif test_cmd == "\\57490|":  # \cmd123
        if base_param == 1:
            num_parameters = 1

    return num_parameters


def remove_l_prefix(replacement_string, ascii_part, num_parameters, mappings_file, asciiconv):
    num_parameters = get_range_parameter(replacement_string, ascii_part, num_parameters, mappings_file)
    test_cmd = get_command_number(replacement_string)

    def remove_first_x(regex, text, x):
        result = text
        count = x
        for match in re.finditer(regex, text):
            if count != 0:
                count -= 1
                result = result.replace(match.group(0), "\\" + match.group(1) + "|\\")
        return result

    def remove_first_x2(regex, text, x):
        result = text
        count = x
        for match in re.finditer(regex, text):
            if count != 0:
                count -= 1
                result = result.replace(match.group(0), "\\" + match.group(1) + "|")
        return result

    # Match only the "\L[numeric]" values
    regex_numonly = r"\\L(\d+)\|\\L?"
    regex_numonly2 = r"\\L(\d+)\|$"
    regex_numonly3 = r"\\L(\d+)\|"
    regex_numonly4 = r"\\L?(\d+)\|"

    # Remove L letter from string
    if not test_cmd in {"\\57489|", "\\57355|", "\\57356|", "\\57362|", "\\57383|", "\\57471|",
    "\\57350|", "\\57374|", "\\57347|", "\\57349|", "\\57363|", "\\57462|", "\\57378|", "\\57404|", "\\57470|"}:
        # not \codeblock, \speed, \wait, \bgcolor, \shake, \cmd109, \sound, \person, \music, \showphoto, \person_face, \fademusic, \cmd057, \cmd108
        removed_text = remove_first_x(regex_numonly, ascii_part, num_parameters)
        removed_text2 = remove_first_x2(regex_numonly2, removed_text, num_parameters)
    else:
        removed_text2 = ascii_part

    # Fix some commands that wouldn't work right
    # TODO (lines like...):
    # \music|\16|dピアノがヘタなパパがいるし。 - ending.user.2.ja.txt
    if test_cmd in {"\\57489|", "\\57355|", "\\57356|", "\\57362|", "\\57471|", "\\57347|", "\\57363|",  "\\57378|", "\\57404|", "\\57470|"}:
        # \codeblock, \speed, \wait, \bgcolor, \cmd109, \color, \showphoto, \fademusic, \cmd057, \cmd108
        if removed_text2.startswith("\\L"):
            temp_text = remove_first_x2(regex_numonly3, removed_text2, 1)
            removed_text2 = temp_text
    elif test_cmd in {"\\57383|", "\\57350|", "\\57349|",  "\\57462|"}:  # \shake, \sound, \music, \person_face
        if removed_text2.startswith("\\L"):
            temp_text = remove_first_x2(regex_numonly3, removed_text2, 2)
            removed_text2 = temp_text
    elif test_cmd in {"\\57374|"}:  # \person
        num_param = 3
        split_cmd = removed_text2.split("|", num_param)
        if len(split_cmd) > 2:
            analyze_string = "\\" + split_cmd[0] + "|" + "\\" + split_cmd[1] + "|" + "\\" + split_cmd[2] + "|"
        else:
            analyze_string = "\\" + split_cmd[0] + "|" + "\\" + split_cmd[1] + "|"
        current_cmds = analyze_string.count('\\\\')
        if current_cmds == num_param:
            # This can be safely converted
            temp_text = remove_first_x2(regex_numonly4, removed_text2, num_param)
            removed_text2 = temp_text

    # Convert first char, if necessary
    if num_parameters > 0 and not removed_text2.startswith("\\") and not removed_text2.startswith("{REF ") and not asciiconv:
        processed_text = ""
        process_text = removed_text2
        converted = convert_ascii_to_decimal(process_text[0])
        processed_text += "\\" + str(converted) + "|"
        processed_text += removed_text2[1:]
        removed_text2 = processed_text

    if removed_text2 is not None:
        return replacement_string + str(removed_text2)
    else:
        return replacement_string + ascii_part


# Function to convert certain ASCII symbols to their decimals (32-126)
def convert_ascii_symbols(replacement_string, ascii_part, num_parameters, mappings_file):
    # Remove the "|" delimiter
    command_name = replacement_string[:-1]

    # Get command numeric value (to prevent hardcoded texts)
    test_cmd = get_command_number(replacement_string)

    # Do not process these commands as they don't work with this function well
    if test_cmd in {"\\57370|", "\\57462|"}:  # \swoosh, \person_face
        return replacement_string + ascii_part

    # Do not process if it contains {REF...}
    # And also convert the exceptions here (otherwise return as is)
    if "{REF " in ascii_part:
        if ascii_part == r'{REF 2} ':
            return replacement_string + r'{REF 2}\32|'
        elif ascii_part == r'{REF 1}3\1|':
            return replacement_string + r'{REF 1}\51|\1|'
        elif ascii_part == r'\4|%{REF 7}$':
            return replacement_string + r'\4|\37|{REF 7}\36|'
        elif ascii_part == r'\5|T{REF 8}S':
            return replacement_string + r'\5|\84|{REF 8}\83|'
        elif ascii_part == r'\5|L{REF 9}K':
            return replacement_string + r'\5|\76|{REF 9}\75|'
        elif ascii_part == r'{REF 1}c':
            return replacement_string + r'{REF 1}\99|'
        elif ascii_part == r'{REF 10}e':
            return replacement_string + r'{REF 10}\101|'
        elif ascii_part == r'{REF 2}1':
            return replacement_string + r'{REF 2}\49|'
        elif ascii_part == r'{REF 7}3\1|':
            return replacement_string + r'{REF 7}\51|\1|'
        elif ascii_part == r'{REF 1},':
            return replacement_string + r'{REF 1}\44|'
        elif ascii_part == r'{REF 1}e':
            return replacement_string + r'{REF 1}\101|'
        else:
            return replacement_string + ascii_part

    # Get number of parameters for any range command
    current_cmds = ascii_part.count('\\', 0)
    num_parameters = get_range_parameter(replacement_string, ascii_part, num_parameters, mappings_file)

    # Match only the "\L[numeric]" values
    regex_numonly = r"\\L?(\d+)\|?"
    
    # Used to build the string to return
    final_string = ""
    
    # Define full command
    full_string = replacement_string + ascii_part
    full_cmd_count = full_string.count('\\', 0)
    
    # If only the command name exists, but we have parameters defined, gracefully return
    #if full_cmd_count == 1 and num_parameters > 0:
    #    return replacement_string + ascii_part
    
    # Fix commands that end with a "\" ASCII sign
    if num_parameters == 1 and ascii_part.endswith("\\"):
        return replacement_string + "\\92|"

    if current_cmds < num_parameters:
        # Find all matches with their starting and ending positions
        matches = [match.span() for match in re.finditer(regex_numonly, ascii_part)]
        characters = []

        i = 0  # Index for the string
        for start, end in matches:
            # Add characters before the match
            characters.extend(ascii_part[i:start])
            i = end  # Update index to skip matched characters

        # Add remaining characters and unmatched parts
        characters.extend(ascii_part[i:])
        converted_text = ascii_part

        # Used for the second check of command parameters
        cmd_values = num_parameters
        fixed_cmds = ""
        x = ""

        for c in characters:
            while (num_parameters - len(matches)) != 0:
                
                # Convert "1\1" and the other numbers like that manually
                # (Due to the regex)
                if "1\\1" in ascii_part:
                    converted = convert_ascii_to_decimal(str(1))
                    x = "\\" + str(converted) + "|\\1|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "2\\2" in ascii_part:
                    converted = convert_ascii_to_decimal(str(2))
                    x = "\\" + str(converted) + "|\\2|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "3\\3" in ascii_part:
                    converted = convert_ascii_to_decimal(str(3))
                    x = "\\" + str(converted) + "|\\3|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "4\\4" in ascii_part:
                    converted = convert_ascii_to_decimal(str(4))
                    x = "\\" + str(converted) + "|\\4|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "5\\5" in ascii_part:
                    converted = convert_ascii_to_decimal(str(5))
                    x = "\\" + str(converted) + "|\\5|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "6\\6" in ascii_part:
                    converted = convert_ascii_to_decimal(str(6))
                    x = "\\" + str(converted) + "|\\6|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "7\\7" in ascii_part:
                    converted = convert_ascii_to_decimal(str(7))
                    x = "\\" + str(converted) + "|\\7|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "8\\8" in ascii_part:
                    converted = convert_ascii_to_decimal(str(8))
                    x = "\\" + str(converted) + "|\\8|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "9\\9" in ascii_part:
                    converted = convert_ascii_to_decimal(str(9))
                    x = "\\" + str(converted) + "|\\9|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\1|1":
                    converted = convert_ascii_to_decimal(str(1))
                    x = "\\1|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\2|2":
                    converted = convert_ascii_to_decimal(str(2))
                    x = "\\2|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\3|3":
                    converted = convert_ascii_to_decimal(str(3))
                    x = "\\3|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\4|4":
                    converted = convert_ascii_to_decimal(str(4))
                    x = "\\4|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\5|5":
                    converted = convert_ascii_to_decimal(str(5))
                    x = "\\5|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\6|6":
                    converted = convert_ascii_to_decimal(str(6))
                    x = "\\6|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\7|7":
                    converted = convert_ascii_to_decimal(str(7))
                    x = "\\7|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\8|8":
                    converted = convert_ascii_to_decimal(str(8))
                    x = "\\8|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\9|9":
                    converted = convert_ascii_to_decimal(str(9))
                    x = "\\9|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                else:
                    converted = convert_ascii_to_decimal(str(c))

                    # Fix replacing the wrong (first) element if duplicate numbers exist
                    # - Only for this command where it causes issues -
                    if test_cmd == "\\57369|":  # \cmd024
                        match_number_repetitions = r"(?<!\\)(\d)(?:\W|\||\d)*\1"
                        match_nums = re.search(match_number_repetitions, converted_text)
                        if match_nums:
                            value = match_nums.group()
                            if "|" in value and "|\\" not in value: # Make sure to only do this if the repetition is in a different part, not same value
                                x = replace_all_occurrences_backwards(str(converted_text), str(c), "\\" + str(converted) + "|", count=1)
                                # Boldly assuming it has all the parameters already (should be fine, except if not)
                                return replacement_string + x

                    x = converted_text.replace(str(c), "\\" + str(converted) + "|", 1)
                    
                    # Fix double backslashes
                    if "\\124|\\124|" in x:
                        temp = x
                        temp = temp.replace("\\124|\\124|", "|\\124|")
                        x = temp

                    # Final string to use if command parameters are enough
                    final_string = replacement_string + x
                    num_parameters -= 1

                    # Check if we have enough command parameters
                    # (As sometimes, the \L[numeric] values may add some extra false numbers
                    values = get_first_numeric_values(x, num_parameters)
                    if values:
                      remaining_string = x[x.rfind("|") + 1:]
                      for v in values:
                        if cmd_values == num_parameters:
                            break
                        if v.startswith("\\"):
                            cmd_values -= 1
                            fixed_cmds += v + "|"
                        else:
                            for char in v:
                                if cmd_values != num_parameters:
                                    converted = convert_ascii_to_decimal(str(char))
                                    fixed_cmds += "\\" + str(converted) + "|"
                                    cmd_values -= 1
                                    num_parameters -= 1
                                else:
                                    fixed_cmds += char
                            if remaining_string:
                                fixed_cmds += remaining_string
                            # Add \L[numeric] value delimiters back
                            fixed_delimiters = find_and_add_delimiters(fixed_cmds)
                            final_string += replacement_string + fixed_delimiters

    # Fix the "|" mistakes
    if "\\124||" in final_string:
        temp = final_string
        temp = temp.replace("\\124||", "|\\124|")
        final_string = temp

    if final_string.endswith("||"):
        temp = final_string
        temp = temp.replace("||", "|\\124|")
        final_string = temp

    # Return the final result 
    return final_string


def count_backslashes_with_numbers(text, num_parameters):
    count = 0
    pattern = r"\\L?(\d+)"
    matches = re.findall(pattern, text)
    for match in matches:
        if count < num_parameters:
            count += 1
    return count


def replace_single_backslashes(text, num_parameters):
    result = ""
    pattern = r"\\L?(\d+)"
    matches = re.finditer(pattern, text)
    ignore_indices = set()
    for match in matches:
        if num_parameters != 0:
            # Get the starting index (excluding captured digits)
            start_index = match.start(1) - 1  # Backslash index (excluding digits)
            # Check for optional "L"
            if text[start_index - 1] == "L" and text[start_index - 2] == "\\":
                start_index -= 2
            # Adjust for "L" and preceding backslash
            if text[start_index] == "L":
                start_index -= 1
            num_parameters -= 1
        ignore_indices.add(start_index)

    filtered_matches = re.finditer(r"\\", text)
    for match in filtered_matches:
        if match.start() not in ignore_indices:
          start = match.start()
          end = match.end()

          # Build the new string with replacement
          result = text[:match.start()] + "\\92|" + text[match.end():]

          # Fix double "\\"
          if "\\92||" in result:
            result = text[:match.start()] + "\\92|\\92" + text[match.end():]

          return result


def ascii_convert_command(ascii_part, num_parameters):
    cmd_count = ascii_part.count('\\', 0)
    iteration = num_parameters - cmd_count

    # Exceptional cases that require manual handling
    #if ascii_part == "\\0|0":
    #    return "\\0|\\48"
    if ascii_part == r'\0|\\0|':
        return r'\0|\92|\0|'

    # For {REF} stuff (\person, \bganim, \swoosh)
    # -en-
    if ascii_part == r'\5|{REF 14}VU':
        return r'\5|{REF 14}\86|\85|'
    # -de-
    if ascii_part == r'{REF 8}b\L275|':
        return r'{REF 8}\98|\L275|'
    # -fr-
    elif ascii_part == r'\0|{REF 6}\L4096|%\L817|':
        return r'\0|{REF 6}\L4096|\37|\L817|'

    # Do not process if it still contains {REF...}
    if "{REF " in ascii_part:
        return ascii_part

    # If there are a ton of values after command, return as is
    if iteration < 0:
        return ascii_part

    # Create a copy so that it doesn't overwrite current value
    ascii_part_copy = ascii_part

    split_cmd = ascii_part_copy.split('|')
    secondProcess = False
    for part in split_cmd:
        if not part.startswith('\\') and not part.endswith('|') and len(part) == 1:
            x = ascii_part_copy.replace(part, "\\" + str(convert_ascii_to_decimal(part)) + "|", 1)
            ascii_part_copy = x
        elif not part.startswith('\\'):
            for p in part:
                while p in ascii_part_copy and iteration != 0:
                    x = ascii_part_copy.replace(p, "\\" + str(convert_ascii_to_decimal(p)) + "|", 1)
                    if "\\\\" in x:
                        iteration = 0
                        secondProcess = True
                        break
                    ascii_part_copy = x
                    iteration -= 1

    if "\\\\" in ascii_part_copy or secondProcess:
        # Assuming it did not replace properly, try a different method
        ascii_part_copy2 = ascii_part
        cmd_count = ascii_part.count('\\', 0)
        iteration = num_parameters - cmd_count

        # Replace sole numeric values with temporary markers
        # (I know there can be better ways, but this is the most simple)
        ap0 = ascii_part_copy2.replace('\\0', '\\Q')
        ap1 = ap0.replace('\\1', '\\W')
        ap2 = ap1.replace('\\2', '\\E')
        ap3 = ap2.replace('\\3', '\\R')
        ap4 = ap3.replace('\\4', '\\T')
        ap5 = ap4.replace('\\5', '\\Z')
        ap6 = ap5.replace('\\6', '\\U')
        ap7 = ap6.replace('\\7', '\\I')
        ap8 = ap7.replace('\\8', '\\O')
        ap9 = ap8.replace('\\9', '\\P')

        split_cmd = ap9.split('|')
        new_parts = []
        new_part = []
        remaining_string = []
        removed_char = 0
        for part in split_cmd:
            if not part.startswith('\\'):
                # This method doesn't actually support "b\0" (char before \num value)
                if "\\" in part:
                    return ascii_part_copy2
                remaining_string.append(part)
                while iteration != 0:
                    for p in part:
                        if iteration != 0:
                            decimal_value = convert_ascii_to_decimal(p)
                            new_part.append("\\" + str(decimal_value) + "|")
                            iteration -= 1
                            removed_char += 1
                    remaining_string = [i[removed_char:] for i in remaining_string]
                    new_parts.append("".join(new_part))
            else:
                ap0 = part.replace('\\P', '\\9')
                ap1 = ap0.replace('\\O', '\\8')
                ap2 = ap1.replace('\\I', '\\7')
                ap3 = ap2.replace('\\U', '\\6')
                ap4 = ap3.replace('\\Z', '\\5')
                ap5 = ap4.replace('\\T', '\\4')
                ap6 = ap5.replace('\\R', '\\3')
                ap7 = ap6.replace('\\E', '\\2')
                ap8 = ap7.replace('\\W', '\\1')
                final_string = ap8.replace('\\Q', '\\0')
                new_parts.append(final_string + "|")

        joinedlist = new_parts + remaining_string

        # Also convert any "\" ASCII symbols now before returning it
        # num_parameters + 1 --> because this now also includes the command name
        count_cmd_backslashes = count_backslashes_with_numbers("".join(joinedlist), num_parameters + 1)
        if count_cmd_backslashes < num_parameters:
            if "\\\\" in ascii_part_copy:
                fix_doubleslashes = ascii_part_copy.replace('\\\\', '\\\\92|')
                ascii_part_copy = fix_doubleslashes
            backslash_fix = replace_single_backslashes(ascii_part_copy, (num_parameters + 1) - count_cmd_backslashes)
            return backslash_fix
        else:
            return "".join(joinedlist)

    # Also convert any "\" ASCII symbols now before returning it
    # num_parameters + 1 --> because this now also includes the command name
    count_cmd_backslashes = count_backslashes_with_numbers(ascii_part_copy, num_parameters + 1)
    if count_cmd_backslashes < num_parameters:
        if "\\\\" in ascii_part_copy:
            fix_doubleslashes = ascii_part_copy.replace('\\\\', '\\\\92|')
            ascii_part_copy = fix_doubleslashes
        backslash_fix = replace_single_backslashes(ascii_part_copy, (num_parameters + 1) - count_cmd_backslashes)
        return backslash_fix
    else:
        return ascii_part_copy


# Function to replace ASCII symbols before numerical values
# This only converts the chars before the values
def ascii_convert_prevalues(ascii_part, num):
    # These are not needed for this, but doesn't hurt to keep them either
    cmd_count = ascii_part.count('\\', 0)
    cmd_left = num - cmd_count

    # Return language-specific exceptions here (add your own ones if needed)
    # -de-
    if ascii_part == r'\6|\0|\0|\0|h\L228|tte er so stehen m\L252|ssen,':
        return r'\6|\0|\0|\0|h\L228|tte er so stehen m\L252|ssen,'

    # Convert two or triple pipes before splitting
    if "|||" in ascii_part:
        temp = ascii_part
        temp = temp.replace('|||', '|\\124|\\124|')
        ascii_part = temp
    elif "||" in ascii_part:
        temp = ascii_part
        temp = temp.replace('||', '|\\124|')
        ascii_part = temp

    converted_chars = []
    remaining_string = []
    #converted_num = cmd_count
    converted_num = 0
    split_pattern = r".{2,}(\d+)" # Match only the values before numbers
    string_split = ascii_part.split('|')
    firstOnly = False
    if converted_num <= 4: # Maximum parameter number for all the commands involved
        for text in string_split:
            match = re.search(split_pattern, text)
            if match:
                string = match.group()
                length = len(string)
                firstChar = False
                secondChar = False
                if length >= 3:
                    if not string[0] == "\\" and not firstOnly:
                        # Convert first char
                        decimal_value = convert_ascii_to_decimal(string[0])
                        converted_chars.append("\\" + str(decimal_value) + "|")
                        converted_num += 1
                        firstChar = True
                        if not string[1] == "\\":
                            # Convert second char
                            decimal_value = convert_ascii_to_decimal(string[1])
                            converted_chars.append("\\" + str(decimal_value) + "|")
                            converted_num += 1
                            secondChar = True
                            firstOnly = True
                    elif string[0] == " " and firstOnly:
                        # Don't convert spaces at this point
                        converted_chars.append(" " + string[1:] + "|")
                    else:
                        converted_chars.append("\\" + string[1:] + "|")
                    if firstChar and not secondChar:
                        converted_chars.append(string[1:] + "|")
                    elif firstChar and secondChar:
                        converted_chars.append(string[2:] + "|")
            else:
                if text.startswith("\\"):
                    if len(text) >= 1:
                        if text[1].isnumeric():
                            converted_chars.append(text + "|")
                        elif text[1] == "L":
                            converted_chars.append(text + "|")
                        else:
                           converted_chars.append(text) 
                    else:
                        converted_chars.append(text + "|")
                else:
                    # text at the end (not getting handled in this function)
                    remaining_string.append(text)

        return "".join(converted_chars + remaining_string)


# Convert the last characters only
def ascii_convert_aftervalues(ascii_part, num):
    #cmd_count = ascii_part.count('\\', 0)
    #cmd_left = num - cmd_count

    # Do not proceed if there is a pipe at the end (that means it's a command end)
    if ascii_part.endswith('|'):
        return ascii_part

    # Return language-specific exceptions here (add your own ones if needed)
    # -ko-
    if ascii_part == r'\5|\84|\36|\L47560|\L52840|\L45236| \L46300|\L47084|\L45212| \L46319|\L54633|\L45768|\L45796|.':
        return ascii_part

    # Convert two or triple pipes before splitting
    # (should be redundant as this has happened before earlier, but anyway)
    if "|||" in ascii_part:
        temp = ascii_part
        temp = temp.replace('|||', '|\\124|\\124|')
        ascii_part = temp
    elif "||" in ascii_part:
        temp = ascii_part
        temp = temp.replace('||', '|\\124|')
        ascii_part = temp

    converted_chars = []
    starting_string = []
    space_text = []
    non_matches = 0
    split_pattern = r"\\L?(\d+).*" # values after numbers
    string_split = ascii_part.split('|')
    for text in string_split:
        # If language text has space, do not convert that
        if " \L" in text:
            space_text.append(text + "|")

        match = re.search(split_pattern, text)
        if not match:
            # Text at the end
            length = len(text)
            if length == 1:
                # Always convert these
                decimal_value = convert_ascii_to_decimal(text)
                converted_chars.append("\\" + str(decimal_value) + "|")
                non_matches += 1
            elif length == 2:
                # Always convert these
                for char in text:
                    decimal_value = convert_ascii_to_decimal(char)
                    converted_chars.append("\\" + str(decimal_value) + "|")
                    non_matches += 1
            elif length > 2:
                # Convert only first char here too (should be enough for these commands)
                for char in text:
                    if non_matches < 1:
                        decimal_value = convert_ascii_to_decimal(char)
                        converted_chars.append("\\" + str(decimal_value) + "|")
                        non_matches += 1
                    else:
                        converted_chars.append(char)
            else:
                # If we'd ever reach this point, and don't know what to do, put it back as is
                converted_chars.append(text)
        else:
            # Matching numbers come first
            string = match.group()
            starting_string.append(string + "|")

    # Add original spaces back to strings with \L numbers, if they contain them
    for i, space_element in enumerate(space_text):
        for j, orig_element in enumerate(starting_string):
            if space_element.strip() == orig_element:
                starting_string[j] = space_element
                break

    return "".join(starting_string + converted_chars)


def is_language_related(char):
    # Get the general category of the character
    category = unicodedata.category(char)
    # Check if the character belongs to a script commonly used in languages
    if category.startswith('L') is not None:
        return True
    else:
        return False


def process_replacement(replacement_string, line, start_index, ascii_part, num_parameters, mappings_file):
    modified_line = None
    converted_cmd = None

    # Define a dictionary to map command numbers to conversion functions
    conversion_functions = {
        "\\57370|": ascii_convert_command,  # \swoosh
        "\\57374|": ascii_convert_command,  # \person
        "\\57462|": ascii_convert_command,  # \person_face
        "\\57349|": ascii_convert_command,  # \music
        "\\57449|": ascii_convert_command,  # \bganim
        "\\57369|": ascii_convert_command,  # \cmd024
        "\\57451|": ascii_convert_command,  # \cmd095
        "\\57402|": ascii_convert_prevalues,  # \cmd055
        "\\57424|": ascii_convert_prevalues,  # \cmd073
        "\\57451|": ascii_convert_prevalues,  # \cmd095
        "\\57461|": ascii_convert_prevalues  # \cmd104
    }

    # Get command numeric value (to prevent hardcoded texts)
    test_cmd = get_command_number(replacement_string)

    # Perform the conversions
    if test_cmd in conversion_functions:
        converted_cmd = conversion_functions[test_cmd](ascii_part, num_parameters)

    # Apply the conversion if any
    if converted_cmd is not None:
        modified_line = replacement_string + converted_cmd
        ascii_part = converted_cmd  # Update ascii_part with converted_cmd

    # Clear dictionary
    conversion_functions.clear()

    # Add functions to do after (second phase)
    conversion_functions = {
        "\\57397|": ascii_convert_aftervalues,  # \cmd051
        "\\57402|": ascii_convert_aftervalues,  # \cmd055
        "\\57416|": ascii_convert_aftervalues,  # \cmd066
        "\\57424|": ascii_convert_aftervalues,  # \cmd073
        "\\57451|": ascii_convert_aftervalues  # \cmd095
    }

    # Apply the conversion if any
    if converted_cmd is not None:
        modified_line = replacement_string + converted_cmd
        ascii_part = converted_cmd  # Update ascii_part with converted_cmd

    return modified_line, ascii_part


# Binary search for position (for markers)
def is_position_in_list(byte_position, position_list):
    left = 0
    right = len(position_list) - 1

    while left <= right:
        mid = (left + right) // 2
        if position_list[mid] == byte_position:
            return True
        elif position_list[mid] < byte_position:
            left = mid + 1
        else:
            right = mid - 1

    return False


# For decoding the GS4 scripts
def decode_gs4_script(input_file, output_file, sections_zero, sections_one, mappings_file, asciiconv=False, lparam=False):
  with open(input_file, "rb") as f_in, open(output_file, "w") as f_out:
    data = f_in.read()

    try:
      # Attempt decoding with UTF-16LE (utf-16le) - alternative might be ISO-8859-1 (latin-1)
      text = data.decode("utf-16le", errors="replace")
    except UnicodeDecodeError:
      print("Warning: Decoding failed with the UTF-16LE encoding.")
      sys.exit(1)

    output_lines = []
    no_conv_lines = []
    byte_position = 0  # Initialize byte position to be able to find and mark sections
    section_num = 1  # Initialize section counter
    section2_num = 1 # Initialize section 2 counter
    for char in text:

      # If we are at a section marker, insert that here
      if is_position_in_list(byte_position, sections_zero):
        output_lines.append("\n\n{SECTION " + str(section_num) + "}\n")
        section_num += 1
      if is_position_in_list(byte_position, sections_one):
        output_lines.append("{REF " + str(section2_num) + "}")
        section2_num += 1

      # Check if character is within the basic ASCII range without control characters (0-31, 127)
      if 32 <= ord(char) <= 126:
        output_lines.append(char)
      elif unicodedata.category(char)[0] == 'C':
        #output_lines.append("\\x{:02o}||".format(ord(char))) # convert control characters to octal values
        #output_lines.append("\\x{:02x}||".format(ord(char))) # convert control characters to hexadecimal values
        string = "{:d}||".format(ord(char))
        if (string.startswith("5") or string.startswith("6")) and len(string) >= 7:
            if section_num == 1:
                output_lines.append("\\{:d}|".format(ord(char))) # convert control characters to decimal values
            else:
                output_lines.append("\n\\{:d}|".format(ord(char))) # add newline for the command control characters
        else:
            output_lines.append("\\{:d}|".format(ord(char))) # convert control characters to decimal values
      else:
        # Convert non-ASCII characters to their decimal representations
        # Otherwise use hex (with the Unicode code point)
        if is_language_related(char):
            try:
                dec_char = ord(char)
                output_lines.append(f"\\L{dec_char}|")
            except:
                hex_char = hex(ord(char))[2:].zfill(2)
                output_lines.append(f"[U+{hex_char}]")
        else:
            try:
                dec_char = ord(char)
                output_lines.append(f"\\{dec_char}|")
            except:
                hex_char = hex(ord(char))[2:].zfill(2)
                output_lines.append(f"[U+{hex_char}]")

      byte_position += 2  # Each character is 2 bytes in UTF-16LE

    # Load mappings from the mappings file
    replacement_mapping = load_mappings(mappings_file, '|')

    # Apply replacements
    for numeric_sequence, (replacement_string, argument_range) in replacement_mapping.items():
        #output_string = "".join(output_lines)
        #output_string = output_string.replace(numeric_sequence, replacement_string)

        # Split the list based on first "{SECTION 1}"
        split_index = None
        for i, element in enumerate(output_lines):
            if "{SECTION 1}" in element:
                split_index = i
                break

        if split_index is not None:
          lines_before = output_lines[:split_index]
          lines_after = output_lines[split_index:]
          before_string = "".join(lines_before)
          after_string = "".join(lines_after).replace(numeric_sequence, replacement_string)
          output_string = before_string + after_string
        else:
          # Handle the case where "{SECTION 1}" is not found
          output_string = "".join(output_lines).replace(numeric_sequence, replacement_string)

        if argument_range:
            lines = output_string.split("\n")
            for i, line in enumerate(lines):
                if i == len(lines) - 1 and not line.strip():
                    break
                start_index = 0
                while True:
                    start_index = line.find(replacement_string, start_index)
                    if start_index == -1:
                        break
                    if section_num == 1:
                        break
                    ascii_part = (line[start_index + len(replacement_string):])
                    line = replacement_string + ascii_part
                    num_parameters = argument_range[0]

                    if not asciiconv:
                        # Process the line with ASCII symbol conversion (through two methods)
                        converted_line = convert_ascii_symbols(replacement_string, ascii_part, num_parameters, mappings_file)
                        if converted_line:
                            line = converted_line
                            ascii_part = (converted_line[start_index + len(replacement_string):])

                        # Additional commands to convert from ASCII symbols to decimals
                        modified_line, ascii_part = process_replacement(replacement_string, line, start_index, ascii_part, num_parameters, mappings_file)
                        if modified_line is not None:
                            line = modified_line
                            ascii_part = (modified_line[start_index + len(replacement_string):])

                    # Remove "L" prefix from parameter numbers
                    if lparam:
                        line = remove_l_prefix(replacement_string, ascii_part, num_parameters, mappings_file, asciiconv)

                    start_index += len(replacement_string)
                lines[i] = line
            output_string = '\n'.join(lines)
        output_lines = output_string.splitlines(keepends=True)

    # Write the converted text with annotations to the output file
    f_out.write("".join(output_lines))


# Also convert the ASCII symbols to decimals on first line
def fix_first_line(annotated_file, output_file):
  with open(annotated_file, "r") as f_in, open(output_file, "w") as f_out:
    try:
        # Handle the first line, remove the "L" chars and convert ASCII symbols here too
        first_line = f_in.readline()

        # Split the line in case of extra newlines
        lines = first_line.splitlines()

        # Remove the "L" from first line, as that's needed for the regex to work
        modified_line = re.sub(r'\\L(\d+)', r'\\\1', lines[0])

        # Manually catch and convert any "\\" sign (regex is not going to find this)
        if "\\\\" in modified_line:
            changed_line = modified_line
            changed_line = changed_line.replace('\\\\', '\\92|\\')
            modified_line = changed_line

        # Match two patterns with regex
        pattern_before = r'(?<=\|)([^\\\\]*)'  # Pattern to capture text before \number
        pattern_after = r'\\(\d+)([^|]*)'  # Pattern to capture \number and text after it

        # Find all matches for pattern_before in the string
        matches_before = re.finditer(pattern_before, modified_line)

        # Find all matches for pattern_after in the string
        matches_after = re.finditer(pattern_after, modified_line)

        # Empty string to hold the values
        final_line = ""

        # Manually add the very first byte if the second byte starts with "\"
        # (As the regex fails to catch this one)
        second_byte = modified_line[1]
        if second_byte == '\\':
            first_byte = modified_line[0]
            replaced_char = convert_ascii_to_decimal(first_byte)
            final_line += "\\" + str(replaced_char) + "|"

        # Extract captured groups from matches
        for match_before, match_after in zip(matches_before, matches_after):
            text_before = match_before.group(1)  # Capture the text before \number
            # Capture the numeric value (\number)
            number = match_after.group(1)
            # Capture the text after \number
            text_after = match_after.group(2)

            if number:
                final_line += "\\" + str(number) + "|"
            if text_before:
                if not text_before.startswith("{REF "):  # Do not convert {REF...} values
                    for char in text_before:
                        replaced_char = convert_ascii_to_decimal(char)
                        final_line += "\\" + str(replaced_char) + "|"
                else:
                    final_line += text_before
            if text_after:
                if not text_before.startswith("{REF "):  # Do not convert {REF...} values
                    for char in text_after:
                        replaced_char = convert_ascii_to_decimal(char)
                        final_line += "\\" + str(replaced_char) + "|"
                else:
                    final_line += text_after

        modified_line = final_line

        f_out.write(modified_line + '\n' + f_in.read())
    except IndexError:
        print(f"Can't read first line of: {f_in}")
        sys.exit(1)
  

def remove_newlines_and_replace_inplace(filename, mappings_file):
    temp_filename = filename + ".temp"  # Create a temporary filename

    # Load mappings from the mappings file
    replacement_mapping = load_mappings(mappings_file, '|')

    # Construct the replacement string pattern using only the replacement strings
    replacement_strings = [value[0] for value in replacement_mapping.values()]
    escaped_replacement_strings = [re.escape(string) for string in replacement_strings]
    #replacement_string_pattern = "|".join(f"{escaped_string}" for escaped_string in escaped_replacement_strings)
    replacement_string_pattern = "|".join(escaped_replacement_strings)

    # Define a function to replace replacement strings with their corresponding numeric sequences
    def replace_replacement_string(match):
        matched_string = match.group(0)
        #return next((key for key, value in replacement_mapping.items() if value[0].rstrip('|') == matched_string), matched_string)
        return next(key for key, value in replacement_mapping.items() if value[0] == matched_string)

    # Read the original file, apply replacements, and remove newlines
    with open(filename, 'r') as infile, open(temp_filename, 'w') as outfile:
        try:
            content = infile.read()
            modified_content = re.sub(replacement_string_pattern, replace_replacement_string, content)
            modified_content_with_sections = re.sub(r"\{SECTION[^}]*\}", "|SECTION|", modified_content)
            modified_content_with_sections2 = re.sub(r"\{REF[^}]*\}", "|REF|", modified_content_with_sections)
            modified_content_without_newlines = modified_content_with_sections2.replace('\n', '')
            outfile.write(modified_content_without_newlines)
        except UnicodeDecodeError as e:
            print(f"The '{filename}' cannot be encoded.")
            print(f"Error message: {e}")
            sys.exit(1)

    # Replace the original file with the temporary file (atomic operation)
    os.replace(temp_filename, filename)


def encode_gs4_script(input_file, output_file, target_encoding="utf-16le"):
  with open(input_file, "r") as f_in, open(output_file, "wb") as f_out:
    text = f_in.read()

    # Define a regular expression to match control characters
    #controlchar_pattern = r"\\x([0-9a-fA-F]{2,4})\|"
    controlchar_pattern = r"\\L?(\d+)\|"

    def replace_decimal(match):
      decimal_value = int(match.group(1))
      if 32 <= decimal_value <= 126:  # Convert to symbol, if the number is in ASCII 32-126 range
        ascii_symbol = convert_decimal_to_ascii(decimal_value)
        hex_code = hex(ord(ascii_symbol))[2:].upper().zfill(4)
        return f"[U+{hex_code}]"
      else:
        hex_code = format(decimal_value, '04X')
        return f"[U+{hex_code}]"

    # Define a regular expression to match hex annotations (within square brackets)
    hex_pattern = r"\[U\+([0-9a-fA-F]{4})\]"

    def replace_hex(match):
      # Extract the hex code from the match object (group 1)
      hex_code = match.group(1)
      char_code = int(hex_code, 16)

      try:
          return chr(char_code)
      except UnicodeEncodeError:
          # If decoding fails, replace with a placeholder (e.g., "?")
          return "?"

    # Replace annotations with their corresponding characters
    text_without_dec = re.sub(controlchar_pattern, replace_decimal, text)
    text_without_hex = re.sub(hex_pattern, replace_hex, text_without_dec)

    try:
      # Encode the text without hex annotations back to the target encoding
      encoded_data = text_without_hex.encode(target_encoding)
    except UnicodeEncodeError:
      print(f"Error: Encoding back to {target_encoding} failed. Consider a different encoding.")
      return

    # Write to output file
    f_out.write(encoded_data)


# Split sections by 0 (main) and 1 (sub)
def split_list_by_following_element(input_list):
    list_0 = []
    list_1 = []
    for i in range(len(input_list) - 1):  # Iterate until the second last element
        current_element = input_list[i]
        next_element = input_list[i + 1]
        if next_element == 0:
            list_0.append(current_element)
        elif next_element == 1:
            list_1.append(current_element)
    return list_0, list_1


# Extract position values for decoding
def extract_position_values(filename):
    positions = []
    first_value = None  # Initialize a variable to store the first value
    sections_read = 0   # Initialize a variable for sections
    with open(filename, 'rb') as file:
        chunk_size = 1024  # As the files are small, this should be enough
        offset = 0  # Start from beginning of the file
        chunk = file.read(chunk_size)  # Read the first chunk
        while chunk:  # Continue until no more data is read
            if offset == 0:  # Check if it's the first chunk
                # Read two bytes and convert to UInt16 for the first value
                first_value = int.from_bytes(chunk[:2], byteorder='little')
                chunk = chunk[2:]  # Move chunk pointer forward
                offset += 2  # Increment offset by the number of bytes read
            else:
                # Iterate over the remaining chunk by 2 bytes (UInt16)
                for i in range(0, len(chunk), 2):
                    # Read two bytes and convert to UInt16
                    uint16_value = int.from_bytes(chunk[i:i+2], byteorder='little')
                    if sections_read != (first_value * 2) + 1:
                        positions.append(uint16_value)  # Append number to list
                        sections_read += 1
                # Read the next chunk
                chunk = file.read(chunk_size)
                offset += len(chunk)  # Increment offset by the number of bytes read

    if positions[0] == 0:  # Remove zero value if that's the first element
        temp_list = positions[1:]
        positions = temp_list

    list_0, list_1 = split_list_by_following_element(positions)
    return list_0, list_1


def remove_bytes(binary_file, position, bytes_to_remove):
    # Open the binary file in read and write mode
    with open(binary_file, "r+b") as f:
        # Move the file pointer to the position of the bytes to be removed
        f.seek(position)

        # Read the bytes at the specified position
        bytes_read = f.read(len(bytes_to_remove))

        # Check if the bytes read match the specified bytes to remove
        if bytes_read == bytes_to_remove:
            # Save the current position as the offset
            offset = f.tell()

            # Move the file pointer back to the position of the bytes to be removed
            f.seek(position + len(bytes_to_remove))

            # Read the remaining bytes from the file
            remaining_bytes = f.read()

            # Move the file pointer back to the position of the bytes to be removed
            f.seek(position)

            # Write the remaining bytes back to the file
            f.write(remaining_bytes)

            # Truncate the file to remove the extra bytes at the end
            f.truncate(position + len(remaining_bytes))

            # Return the offset of the bytes found
            return offset
        else:
            # If the bytes read do not match the specified bytes to remove, do nothing
            return None


# Clean file of initial values
def remove_initial_values(filename):
    with open(filename, 'r+b') as file:
        # Read the first byte separately
        first_byte = file.read(1)

        if first_byte:
            # Determine the number of bytes to remove based on the value of the first byte
            bytes_to_remove = (ord(first_byte) * 4) + 4  # +4 to include the first byte too

            # Move the file pointer to the position after the bytes to remove
            file.seek(bytes_to_remove)

            # Read the remaining content
            content = file.read()

            # Move the file pointer to the beginning
            file.seek(0)

            # Write the remaining content starting from the beginning of the file
            file.write(content)

            # Truncate the file to remove the remaining content
            file.truncate()


# Get position offsets
def find_offsets(binary_file, search_string):
    offsets = []
    with open(binary_file, 'rb') as file:
        # Read the entire file as binary data
        data = file.read()
        # Initialize the starting index for searching
        start_index = 0
        # Loop until there are no more matches
        while True:
            # Find the next occurrence of the search string
            index = data.find(search_string, start_index)
            if index == -1:
                break  # No more occurrences found
            # Add the offset to the list
            offsets.append(index)
            # Move the starting index for the next search
            start_index = index + len(search_string)
    return offsets


def insert_values(filename, values):
    with open(filename, 'r+b') as file:
        # Get the total size of bytes to insert
        total_insert_size = sum(len(value.to_bytes(2, byteorder='little')) for value in values)

        # Read the existing content from the file
        existing_content = file.read()

        # Move the file pointer to the position after inserted bytes
        file.seek(total_insert_size)

        # Write back the existing content, effectively shifting it after inserted bytes
        file.write(existing_content)

        # Move the file pointer back to the beginning of the file
        file.seek(0)

        # Write the inserted values at the beginning of the file
        for value in values:
            file.write(value.to_bytes(2, byteorder='little'))


# Create temp file for position offsets: |REF|
def copy_file(src_file, dst_file):
    # Open source file for reading and destination file for writing
    with open(src_file, 'rb') as src, open(dst_file, 'wb') as dst:
        # Read and write in chunks to avoid loading the entire file into memory
        chunk_size = 1024  # Should be enough for these small files
        while True:
            chunk = src.read(chunk_size)
            if not chunk:
                break
            dst.write(chunk)


def rename_decoded_file(output_file):
  final_name = os.path.splitext(output_file)[0]
  os.rename(output_file, final_name)


def convert_decimal_to_unicode(text):
    def replace_unicode(match):
        decimal_code = int(match.group(1))
        hex_code = hex(decimal_code)[2:]
        return chr(int(hex_code, 16))

    unicode_pattern = r"\\L(\d+)\|"
    result = re.sub(unicode_pattern, replace_unicode, text)
    return result


def convert_to_decimal(text):
    result = ''
    for char in text:
        if ord(char) > 127:
            # Character is non-ASCII, convert it to decimal representation
            decimal_value = ord(char)
            result += f"\\L{decimal_value}|"
        else:
            # Character is ASCII, keep it unchanged
            result += char
    return result


def main():
    # Define the mappings text file
    mappings = "ajaat-gs4-script-mappings.txt"
    # Call preprocess_mappings for command name lookup
    preprocess_mappings(mappings)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Convert AJ:AA Trilogy's GS4 (Apollo Justice) scripts")
    subparsers = parser.add_subparsers(title="Main Commands", dest="command")

    # Subparser for decoding
    decode_parser = subparsers.add_parser("decode", help="Decode GS4 scripts to readable format")
    decode_parser.add_argument("input_file", type=str, help="Path to the input binary file or wildcard pattern (mandatory)")
    decode_parser.add_argument("output_file", type=str, nargs='?', default=None, help="Path to the output text file (optional)")
    decode_parser.add_argument("--unicode", action="store_true", help="Convert the \L numeric values to unicode (optional)")
    decode_parser.add_argument("--noasciiconv", action="store_true", help="Do not convert the ASCII symbols to decimal values (optional)")
    decode_parser.add_argument("--nolparam", action="store_true", help="Removes the L prefix from all command parameter values [experimental] (optional)")

    # Subparser for encoding
    encode_parser = subparsers.add_parser("encode", help="Encode readable GS4 scripts back to binary")
    encode_parser.add_argument("input_file", type=str, help="Path to the input text file or wildcard pattern (mandatory)")
    encode_parser.add_argument("output_file", type=str, nargs='?', default=None, help="Path to the output binary file (optional)")
    encode_parser.add_argument("--unicode", action="store_true", help="Convert the unicode values back to decimal (optional)")

    args = parser.parse_args()

    # Validate argument usage based on chosen command
    if args.command == "decode" or args.command == "encode":
        if not args.input_file:
            parser.error(f"{args.command} requires input_file argument")
    else:
        parser.error("Invalid command. Choose either decode or encode")

    # Decode argument
    if args.command == "decode":
        input_files = glob.glob(args.input_file)
        for input_file in input_files:
            output_file = args.output_file if args.output_file else f"{os.path.splitext(input_file)[0]}.txt"
            sections_zero, sections_one = extract_position_values(input_file)
            decode_gs4_script(input_file, output_file, sections_zero, sections_one, mappings, asciiconv=args.noasciiconv, lparam=args.nolparam)

            # Fix the first line of the file (removing the L chars and converting ASCII symbols to decimals)
            if not args.noasciiconv:
                fix_first_line(output_file, f"{output_file}.2")
            else:
                copy_file(output_file, f"{output_file}.2")

            # Decode into unicode with optional flag
            if args.unicode:
                try:
                    with open(f"{output_file}.2", "r", encoding="utf-8") as f_in:
                        input_text = f_in.read()

                    output_text = convert_decimal_to_unicode(input_text)

                    with open(f"{output_file}.3", "wb") as f_out:
                        f_out.write(output_text.encode("utf-8", errors="ignore"))
                except FileNotFoundError:
                    print(f"Error: File not found: {output_file}.2")
                    sys.exit(1)
                except Exception as e:
                    print(f"Error processing file {output_file}.2: {str(e)}")
                    sys.exit(1)

            # Remove temporary output file if it exists
            try:
                os.remove(output_file)
            except FileNotFoundError:
                pass

            # Rename the final file to the original output file
            if args.unicode:
                rename_decoded_file(f"{output_file}.3")
                try:
                    os.remove(f"{output_file}.2")
                except FileNotFoundError:
                    pass
            else:
                rename_decoded_file(f"{output_file}.2")

            # Write conversion message to console
            print(f'Converted "{input_file}" to readable format: "{output_file}"')


    # Encode argument
    elif args.command == "encode":
        input_files = glob.glob(args.input_file)
        for input_file in input_files:
            output_file = args.output_file if args.output_file else f"{os.path.splitext(input_file)[0]}.bin"
            
            # Encode unicode back to decimal with optional flag
            if args.unicode:
                try:
                    with open(input_file, "r", encoding="utf-8") as f_in:
                        input_text = f_in.read()

                    output_text = convert_to_decimal(input_text)

                    with open(f"{input_file}.2", "w", encoding="utf-8") as f_out:
                        f_out.write(output_text)
                except FileNotFoundError:
                    print(f"Error: File not found: {input_file}")
                    sys.exit(1)
                except Exception as e:
                    print(f"Error processing file {input_file}: {str(e)}")
                    sys.exit(1)

            # Rename the final file to the original output file
            if args.unicode:
                try:
                    os.remove(f"{input_file}")
                except FileNotFoundError:
                    pass
                rename_decoded_file(f"{input_file}.2")

            remove_newlines_and_replace_inplace(input_file, mappings)
            encode_gs4_script(input_file, output_file)

            # For the position offsets, a temp file is needed due to some offsets having a value of 1, not 0
            copy_file(output_file, f"{output_file}.TMP")
            temp_file = f"{output_file}.TMP"

            #
            # Write the new position offsets
            #
            str_sec = 18  # |SECTION| = 18 (9*2)
            str_ref = 10  # |REF| = 10 (5*2)
            string_value1 = b'|\x00S\x00E\x00C\x00T\x00I\x00O\x00N\x00|\x00'
            string_value2 = b'|\x00R\x00E\x00F\x00|\x00'
            sections = []
            sections2 = []
            aligned_sections = []
            aligned_sections2 = []

            # 1. Calculate the offsets for sections with 1 values in temp file first
            # Remove |SECTION| strings, leave only |REF|
            zero_offsets = find_offsets(temp_file, string_value1)
            if zero_offsets:
                zero_offsets.sort(reverse=True)
                for p in zero_offsets:
                    section_offset = remove_bytes(temp_file, p, string_value1)
                    zero_offsets = [x - str_sec for x in zero_offsets if x > p]
                    
            # Find and store the offsets for the |REF| strings only
            one_offsets = find_offsets(temp_file, string_value2)
            if one_offsets:
                one_offsets.sort(reverse=True)
                for p in one_offsets:
                    section_offset2 = remove_bytes(temp_file, p, string_value2)
                    if section_offset2 is not None:
                        sections2.append(section_offset2)
                    one_offsets = [x - str_ref for x in one_offsets if x > p]
                sections2 = sorted(sections2)
                aligned_sections2 = [x - (str_ref * i) for i, x in enumerate(sections2, 1)]
                
            modified_list2 = [x for pair in zip(aligned_sections2, [1] * len(aligned_sections2)) for x in pair]

            # Discard the temp file, as it's no longer needed
            if os.path.exists(temp_file):
                os.remove(temp_file)

            # 2. Calculate the offsets for sections with 0 values in original file
            # Remove |REF| strings, leave only |SECTION|
            one_offsets = find_offsets(output_file, string_value2)
            if one_offsets:
                one_offsets.sort(reverse=True)
                for p in one_offsets:
                    section_offset2 = remove_bytes(output_file, p, string_value2)
                    one_offsets = [x - str_ref for x in one_offsets if x > p]

            # Find and store the offsets for the |SECTION| strings only
            zero_offsets = find_offsets(output_file, string_value1)
            if zero_offsets:
                zero_offsets.sort(reverse=True)
                for p in zero_offsets:
                    section_offset = remove_bytes(output_file, p, string_value1)
                    if section_offset is not None:
                        sections.append(section_offset)
                    zero_offsets = [x - str_sec for x in zero_offsets if x > p]
                sections = sorted(sections)
                aligned_sections = [x - (str_sec * i) for i, x in enumerate(sections, 1)]

            # Add zeroes and ones back into the lists
            modified_list1 = [x for pair in zip(aligned_sections, [0] * len(aligned_sections)) for x in pair]
            modified_lists = modified_list1 + modified_list2

            # Count every section
            joined_sections = aligned_sections + aligned_sections2
            position_counter = len(joined_sections)

            # Add the position counter to the list too
            modified_lists.insert(0, position_counter)
            modified_lists.insert(1, 0)

            # Insert new position values
            remove_initial_values(output_file)
            insert_values(output_file, modified_lists)

            # Write conversion message to console
            print(f'Converted "{input_file}" back to binary format: "{output_file}"')


if __name__ == "__main__":
  main()
