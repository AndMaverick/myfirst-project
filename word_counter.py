# word_counter.py
# A simple script to count words in a text file

def count_words(file_path):
    with open(file_path, 'r') as file:
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
