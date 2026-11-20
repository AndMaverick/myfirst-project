# word_counter.py
# A simple script to count words in a text file.
# This is the original script, kept as it was. It splits on spaces, which is right for English and not for Vietnamese
# (one syllable per space), Chinese or Japanese (no spaces). For those, use:  python -m buoc_dau FILE

def count_words(file_path):
    with open(file_path, encoding='utf-8') as file:   # utf-8 added: the default encoding breaks on Vietnamese text on Windows
        text = file.read()
        words = text.split()
        return len(words)

if __name__ == "__main__":
    # Change 'sample.txt' to any text file you want to analyze
    file_name = "sample.txt"
    try:
        word_count = count_words(file_name)
        print(f"The file '{file_name}' has {word_count} words.")
    except FileNotFoundError:
        print(f"File '{file_name}' not found. Please add it to the project folder.")
